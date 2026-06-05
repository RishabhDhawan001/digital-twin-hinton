"""
Geoffrey Hinton Digital Twin Agent
Ties together: Gemini 2.5 Flash, Persona, RAG, Memory
"""

import os
import sys
import uuid
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from persona.hinton_persona import build_system_prompt, HINTON_GREETING as FEYNMAN_GREETING
from memory.memory_system import ShortTermMemory, LongTermMemory, MemoryExtractor
from rag.rag_pipeline import FeynmanRAG


load_dotenv()


class FeynmanAgent:
    """The Richard Geoffrey Hinton Digital Twin Agent."""

    def __init__(self, api_key: str = None, user_id: str = None):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Set it in your .env file or pass it directly.\n"
                "Get a key at: https://aistudio.google.com/"
            )
        
        genai.configure(api_key=api_key)
        
        self.user_id = user_id or str(uuid.uuid4())[:8]
        self.current_year = datetime.now().year

        # Initialize components
        print("[Agent] Loading RAG pipeline...")
        self.rag = FeynmanRAG()
        
        print("[Agent] Initializing memory system...")
        self.short_term = ShortTermMemory(max_turns=20)
        self.long_term = LongTermMemory()
        self.memory_extractor = MemoryExtractor()
        
        # Gemini model
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.85,
                "top_p": 0.95,
                "max_output_tokens": 8192,  # 1024 was too low; Hinton's answers can be long
            }
        )
        
        print(f"[Agent] Ready. User ID: {self.user_id}")

    def _build_prompt(self, user_query: str) -> str:
        """Build the full prompt with persona, memory, and RAG context."""
        rag_context = self.rag.retrieve(user_query, n_results=3)
        memory_context = self.long_term.build_memory_context(self.user_id)
        conversation_history = self.short_term.get_history_string()
        
        system_prompt = build_system_prompt(
            memory_context=memory_context,
            rag_context=rag_context,
            conversation_history=conversation_history,
            current_year=self.current_year
        )
        return system_prompt

    def chat(self, user_message: str) -> str:
        """Process a user message and return Hinton's response."""
        # Build full prompt
        system_prompt = self._build_prompt(user_message)
        
        # Combine system prompt + user message for Gemini
        full_prompt = f"{system_prompt}\n\nUser's current question: {user_message}\n\nYour response as Hinton:"
        
        # Call Gemini
        response = self.model.generate_content(full_prompt)
        assistant_message = response.text.strip()

        # Detect if Gemini hit the token limit mid-response
        try:
            finish_reason = response.candidates[0].finish_reason
            # finish_reason 2 == MAX_TOKENS (truncated); 1 == STOP (complete)
            if hasattr(finish_reason, "value"):
                finish_reason = finish_reason.value
            if finish_reason == 2:
                assistant_message += (
                    "\n\n*(Response was cut off — ask me to continue if you'd like the rest.)*"
                )
        except Exception:
            pass  # Don't let finish_reason inspection crash the chat
        
        # Update short-term memory
        self.short_term.add("user", user_message)
        self.short_term.add("model", assistant_message)
        
        # Extract and save long-term memories (async-ish — don't block response)
        try:
            memories = self.memory_extractor.extract(user_message, assistant_message)
            for mem in memories:
                self.long_term.save_memory(
                    user_id=self.user_id,
                    memory_type=mem["type"],
                    content=mem["content"]
                )
        except Exception:
            pass  # Memory extraction is best-effort
        
        return assistant_message

    def end_session(self):
        """Save session summary to long-term memory."""
        turns = self.short_term.turns
        if not turns:
            return
        
        # Extract topics from conversation
        user_messages = [t["content"] for t in turns if t["role"] == "user"]
        topics = list(set([msg.split()[0] for msg in user_messages if msg]))[:5]
        
        summary = f"Session with {len(turns)//2} exchanges. Topics: {', '.join(topics[:3]) if topics else 'general'}."
        
        self.long_term.save_session(
            user_id=self.user_id,
            session_start=self.short_term.session_start,
            summary=summary,
            turn_count=len(turns) // 2,
            topics=topics
        )
        self.short_term.clear()

    def get_greeting(self) -> str:
        return FEYNMAN_GREETING

    def get_memory_data(self) -> dict:
        """Return all memory data for the dashboard."""
        return self.long_term.get_all_memories_for_dashboard(self.user_id)

    def get_rag_stats(self) -> dict:
        return self.rag.get_stats()
