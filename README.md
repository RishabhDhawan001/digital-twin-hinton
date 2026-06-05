# digital twin
I have created a digital twin of Geoffrey Hinton, which answers through his papers, interviews, and lectures in depth and accurately.

# overview
i have built it using:-
gemini 2.5
rag
chromaDB
Langchain
long-term memory

# features
hinton's persona
persistent memory
multi-turn conversations

# architecture
Papers + Lectures + Interviews
                ↓
          Text Extraction
                ↓
          Embeddings
                ↓
           ChromaDB
                ↓
             RAG
                ↓
        LLM (Gemini/OpenAI)
                ↓
      Geoffrey Hinton Twin
