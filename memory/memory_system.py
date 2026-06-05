"""
Memory System for Geoffrey Hinton Digital Twin
- Short-term: in-session conversation buffer
- Long-term: SQLite database persisted across sessions
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "feynman_memory.db")


class ShortTermMemory:
    """In-session conversation buffer with sliding window."""

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.turns = []  # list of {"role": ..., "content": ...}
        self.session_start = datetime.now().isoformat()

    def add(self, role: str, content: str):
        self.turns.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        if len(self.turns) > self.max_turns * 2:
            # Keep the most recent turns
            self.turns = self.turns[-(self.max_turns * 2):]

    def get_history_string(self) -> str:
        if not self.turns:
            return ""
        lines = []
        for t in self.turns[-10:]:  # last 5 exchanges for context
            role_label = "User" if t["role"] == "user" else "Hinton"
            lines.append(f"{role_label}: {t['content'][:300]}{'...' if len(t['content']) > 300 else ''}")
        return "\n".join(lines)

    def get_gemini_history(self) -> list:
        """Return history in Gemini API format."""
        history = []
        for t in self.turns:
            history.append({
                "role": t["role"],
                "parts": [{"text": t["content"]}]
            })
        return history

    def clear(self):
        self.turns = []


class LongTermMemory:
    """Persistent memory across sessions using SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    summary TEXT,
                    turn_count INTEGER DEFAULT 0,
                    topics TEXT DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_user 
                ON memories(user_id, memory_type)
            """)

    def save_memory(self, user_id: str, memory_type: str, content: str, metadata: dict = None):
        """
        memory_type can be:
        - 'fact'         : something the user told Hinton about themselves
        - 'interest'     : topics the user is curious about
        - 'prior_knowledge': what the user already knows
        - 'question'     : interesting questions asked
        - 'breakthrough' : moments of understanding
        """
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (user_id, memory_type, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, memory_type, content, json.dumps(metadata or {}), now, now))

    def get_memories(self, user_id: str, memory_type: Optional[str] = None, limit: int = 10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            if memory_type:
                rows = conn.execute("""
                    SELECT memory_type, content, metadata, created_at
                    FROM memories WHERE user_id = ? AND memory_type = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (user_id, memory_type, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT memory_type, content, metadata, created_at
                    FROM memories WHERE user_id = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (user_id, limit)).fetchall()
        return [{"type": r[0], "content": r[1], "metadata": json.loads(r[2]), "date": r[3]} for r in rows]

    def build_memory_context(self, user_id: str) -> str:
        """Build a memory summary string for injection into the system prompt."""
        memories = self.get_memories(user_id, limit=15)
        if not memories:
            return "No previous conversations with this person."

        sections = {}
        for m in memories:
            t = m["type"]
            sections.setdefault(t, []).append(m["content"])

        lines = ["What I remember about this person:"]
        type_labels = {
            "fact": "Personal facts",
            "interest": "Topics they're curious about",
            "prior_knowledge": "What they already know",
            "question": "Questions they've asked before",
            "breakthrough": "Moments they understood something new"
        }
        for t, items in sections.items():
            label = type_labels.get(t, t)
            lines.append(f"\n{label}:")
            for item in items[:3]:
                lines.append(f"  - {item}")
        return "\n".join(lines)

    def save_session(self, user_id: str, session_start: str, summary: str, 
                     turn_count: int, topics: list):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (user_id, session_start, session_end, summary, turn_count, topics)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, session_start, now, summary, turn_count, json.dumps(topics)))

    def get_session_history(self, user_id: str, limit: int = 5) -> list:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT session_start, session_end, summary, turn_count, topics
                FROM sessions WHERE user_id = ?
                ORDER BY session_start DESC LIMIT ?
            """, (user_id, limit)).fetchall()
        return [{
            "start": r[0], "end": r[1], "summary": r[2],
            "turns": r[3], "topics": json.loads(r[4])
        } for r in rows]

    def get_all_memories_for_dashboard(self, user_id: str) -> dict:
        """Return all memory data for visualization."""
        memories = self.get_memories(user_id, limit=100)
        sessions = self.get_session_history(user_id, limit=20)
        return {"memories": memories, "sessions": sessions, "user_id": user_id}

    def delete_memory(self, user_id: str, memory_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (memory_id, user_id))


class MemoryExtractor:
    """Uses Gemini to extract memorable facts from conversations."""

    EXTRACTION_PROMPT = """You are analyzing a conversation with Geoffrey Hinton's digital twin.
Extract any memorable facts about the USER (not Hinton) that should be remembered for future sessions.

Conversation turn:
User said: "{user_message}"
Hinton responded: "{assistant_message}"

Extract facts in this JSON format (return ONLY valid JSON, no markdown):
{{
  "memories": [
    {{
      "type": "fact|interest|prior_knowledge|question|breakthrough",
      "content": "brief memorable fact about the user"
    }}
  ]
}}

Only extract genuinely useful information. If nothing memorable, return {{"memories": []}}.
Types:
- fact: personal info they shared (name, job, age, location)
- interest: topic they seem curious about
- prior_knowledge: what they already know about a topic
- question: a particularly interesting question they asked
- breakthrough: a moment of clear understanding they expressed
"""

    def extract(self, user_message: str, assistant_message: str) -> list:
        """Extract memories from a conversation turn. Returns list of memory dicts."""
        import google.generativeai as genai
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = self.EXTRACTION_PROMPT.format(
                user_message=user_message[:500],
                assistant_message=assistant_message[:500]
            )
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return data.get("memories", [])
        except Exception as e:
            return []
