"""
RAG Pipeline for Geoffrey Hinton Digital Twin
Ingests Hinton's talks, papers, and interviews, embeds them, stores in ChromaDB,
and retrieves relevant passages.
"""

import os
import hashlib
import chromadb
from sentence_transformers import SentenceTransformer

try:
    from rag.feynman_texts import HINTON_BUILTIN_TEXTS as FEYNMAN_BUILTIN_TEXTS
except ImportError:
    from feynman_texts import HINTON_BUILTIN_TEXTS as FEYNMAN_BUILTIN_TEXTS


CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
SOURCES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sources")


class FeynmanRAG:
    """RAG pipeline for Hinton's works."""

    def __init__(self):
        os.makedirs(CHROMA_PATH, exist_ok=True)
        os.makedirs(SOURCES_PATH, exist_ok=True)
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        self.collection = self.client.get_or_create_collection(
            name="feynman_works",
            metadata={"hnsw:space": "cosine"}
        )
        self._ingest_builtin_texts()

    def _embed(self, texts: list) -> list:
        return self.embedding_model.encode(texts).tolist()

    def _ingest_builtin_texts(self):
        """Load built-in Hinton texts into the vector DB."""
        existing_ids = set(self.collection.get()["ids"])
        
        to_add = []
        for item in FEYNMAN_BUILTIN_TEXTS:
            if item["id"] not in existing_ids:
                to_add.append(item)
        
        if not to_add:
            return
        
        texts = [t["text"] for t in to_add]
        ids = [t["id"] for t in to_add]
        metadatas = [{"source": t["source"], "year": t["year"]} for t in to_add]
        embeddings = self._embed(texts)
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        print(f"[RAG] Ingested {len(to_add)} built-in Hinton texts.")

    def ingest_text_file(self, filepath: str, source_name: str, year: int = 0, 
                          chunk_size: int = 500, overlap: int = 100):
        """Ingest a text file into the vector DB with chunking."""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunks = self._chunk_text(text, chunk_size, overlap)
        existing_ids = set(self.collection.get()["ids"])
        
        new_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{source_name}_{i}_{chunk[:50]}".encode()).hexdigest()[:16]
            if chunk_id not in existing_ids:
                new_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "source": source_name,
                    "year": year,
                    "chunk_idx": i
                })
        
        if not new_chunks:
            print(f"[RAG] All chunks from {source_name} already ingested.")
            return
        
        texts = [c["text"] for c in new_chunks]
        ids = [c["id"] for c in new_chunks]
        metadatas = [{"source": c["source"], "year": c["year"]} for c in new_chunks]
        embeddings = self._embed(texts)
        
        self.collection.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
        print(f"[RAG] Ingested {len(new_chunks)} chunks from {source_name}.")

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list:
        """Split text into overlapping chunks by word count."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            start += chunk_size - overlap
        return chunks

    def retrieve(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant passages for a query."""
        query_embedding = self._embed([query])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count())
        )
        
        if not results["documents"][0]:
            return "No specific passages retrieved."
        
        passages = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "Unknown")
            year = meta.get("year", "")
            passages.append(f'[From "{source}", {year}]\n{doc}')
        
        return "\n\n---\n\n".join(passages)

    def get_stats(self) -> dict:
        count = self.collection.count()
        return {"total_chunks": count, "collection": "feynman_works"}
