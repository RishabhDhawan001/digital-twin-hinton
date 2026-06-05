# Geoffrey Hinton Digital Twin — Documentation

**AIMS DTU Summer Project 2026**
Scientist chosen: **Geoffrey Hinton** (b. 1947) — "The Godfather of AI"

---

## Overview

A Digital Twin of Geoffrey Hinton that emulates his knowledge, reasoning style, communication
style, and research expertise using RAG, persistent memory, and a carefully designed persona
layer — all powered by Gemini 2.5 Flash.

---

## Why Hinton?

- **Rich public corpus**: foundational papers (backpropagation 1986, AlexNet 2012, dropout, distillation,
  capsule networks), plus dozens of recent interviews, lectures, and his Nobel and Turing Award talks
- **Distinctive voice**: thoughtful, measured, dry British wit, famous for homely analogies
- **Deep, current domain**: deep learning, neural networks, the brain, and AI safety — exactly the kind
  of technical territory evaluators will probe
- **Alive and current**: unlike a historical figure, Hinton has no hard knowledge cutoff. The
  timeline-awareness feature instead grounds him in his real biography (left Google 2023, Nobel 2024)
  and has him flag when he's speculating about very recent events
- **A genuine intellectual arc**: he publicly changed his mind about AI risk, which makes for a rich,
  honest persona that distinguishes what it knows from what it suspects

---

## Architecture

```
User Input
    │
    ▼
Hinton Persona Layer (system prompt: voice, values, teaching style, biography)
    │
    ├──► RAG Pipeline ──► Vector DB (ChromaDB) ──► Retrieved passages
    │         ▲
    │    Hinton's works:
    │    backprop, AlexNet, dropout,
    │    distillation, AI-risk interviews
    │
    ├──► Memory System
    │       ├── Short-term: conversation buffer (in-session)
    │       └── Long-term: SQLite DB (cross-session)
    │              ├── User facts
    │              ├── Interests
    │              ├── Prior knowledge
    │              └── Session summaries
    │
    ▼
Gemini 2.5 Flash (LLM core)
    │
    ▼
Hinton's Response
    │
    ▼
Memory Extractor (auto-extracts memorable facts → saves to SQLite)
```

---

## Component Design

### 1. Persona Layer (`persona/hinton_persona.py`)

The system prompt encodes:

- **Voice**: measured, qualifying, dry self-deprecating humor, vivid everyday analogies
- **Teaching style**: intuition before equations, analogies, honesty about the unknown, frequent
  comparison between artificial and biological neural networks
- **Knowledge areas**: backpropagation, Boltzmann machines, deep belief nets, AlexNet, dropout, ReLUs,
  capsule networks, knowledge distillation, mortal computation, AI safety/alignment
- **Real biography**: Turing Award 2018 (with Bengio and LeCun), Nobel Prize in Physics 2024 (with
  Hopfield), left Google in 2023 to speak about AI risk, professor emeritus at University of Toronto
- **Intellectual honesty**: represents opposing views fairly (e.g. his disagreement with Yann LeCun on
  AI risk), distinguishes knowledge from informed speculation
- **Timeline awareness**: he is alive and current; the persona anchors him to verified milestones and
  has him flag speculation about anything very recent

**Design decision**: We inject the system prompt fresh each turn (rather than relying on Gemini's chat
history API) so RAG retrievals and memory context are always current.

### 2. RAG Pipeline (`rag/rag_pipeline.py` + `rag/feynman_texts.py`)

- **Embedding model**: `all-MiniLM-L6-v2` (sentence-transformers) — fast, local, no API calls
- **Vector DB**: ChromaDB with persistent storage
- **Chunking**: 500-word chunks with 100-word overlap for ingested files
- **Built-in corpus**: 15 key passages in Hinton's voice covering backpropagation, the 2012 AlexNet
  breakthrough, dropout, knowledge distillation, Boltzmann machines, capsule networks, digital vs
  biological intelligence, the AI-risk argument, the "do LLMs understand?" debate, and his advice to
  researchers
- **Adding sources**: drop `.txt` files in `data/sources/` and call
  `rag.ingest_text_file(path, name, year)`

> Note: the corpus module is named `feynman_texts.py` for historical reasons (the project was first
> scaffolded for Feynman), but it contains Hinton's material — see `HINTON_BUILTIN_TEXTS`.

**Design decision**: cosine similarity is used because chunks vary in length; cosine normalizes for
length and gives more consistent relevance.

### 3. Memory System (`memory/memory_system.py`)

- **Short-term**: in-memory turn buffer, sliding window of recent turns injected into context
- **Long-term**: SQLite at `data/feynman_memory.db`, two tables (`memories`, `sessions`), typed
  memories (`fact`, `interest`, `prior_knowledge`, `question`, `breakthrough`), keyed by `user_id`
- **Memory extraction**: after each turn a lightweight Gemini call extracts memorable user facts as
  structured JSON; runs best-effort so it never blocks the main response

**Design decision**: typed memories let the prompt inject only relevant context rather than dumping
every stored fact.

### 4. Core Agent (`agent.py`)

Per turn: RAG retrieves 3 passages → long-term memory builds a per-user context string → short-term
memory supplies recent history → all three inject into the system prompt → Gemini generates the
response → memory extractor runs.

---

## Running the Project

### Setup

```bash
git clone <repo>
cd hinton-twin
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key_here" > .env
```

Get a Gemini API key at: https://aistudio.google.com/

### CLI Demo

```bash
python demo/cli_demo.py
```

### Web Demo (with memory dashboard)

```bash
python demo/web_demo.py
# open http://localhost:7860
```

### Add Custom Source Documents

```python
from rag.rag_pipeline import FeynmanRAG   # class name retained for compatibility
rag = FeynmanRAG()
rag.ingest_text_file("path/to/hinton_interview.txt", "Interview title", year=2024)
```

---

## Bonus Features Implemented

- **Timeline awareness** — Hinton is grounded in his real, verified biography and flags when he is
  speculating about very recent developments rather than breaking character
- **Memory dashboard** — the web UI includes a Plotly visualization of memory types plus a table of all
  stored memories ("Memory Dashboard" tab)
- **Voice I/O (optional)** — install `pyttsx3 SpeechRecognition pyaudio` and extend the web demo with
  Gradio audio components

---

## Evaluation Criteria — Self-Assessment

| Criterion | Approach |
|-----------|----------|
| **Persona consistency** | System prompt encodes Hinton's measured voice, analogies, dry wit, real biography, and intellectual honesty. Represents opposing views fairly. |
| **Technical accuracy** | RAG grounds answers in 15 passages covering backprop, AlexNet, dropout, distillation, capsules, and AI-risk reasoning. |
| **Memory quality** | Short-term (turn buffer) + long-term (SQLite, typed memories, session summaries). Cross-session recall demonstrated in Sample Conversation 4. |
| **RAG quality** | Cosine-similarity retrieval with sentence-transformers; passages injected as labeled, sourced quotes. |
| **User experience** | Rich CLI with colors; Gradio web UI with chat, memory dashboard, and sample questions. |

---

## File Structure

```
hinton-twin/
├── agent.py                    # Core agent tying all components together
├── requirements.txt
├── .env                        # GEMINI_API_KEY (not committed)
├── persona/
│   └── hinton_persona.py       # System prompt, persona config, timeline logic
├── rag/
│   ├── rag_pipeline.py         # ChromaDB, embeddings, ingestion, retrieval
│   └── feynman_texts.py        # Built-in Hinton corpus (HINTON_BUILTIN_TEXTS)
├── memory/
│   └── memory_system.py        # Short-term + long-term memory, extractor
├── demo/
│   ├── cli_demo.py             # Interactive terminal demo
│   └── web_demo.py             # Gradio web UI with dashboard
├── data/
│   ├── chroma_db/              # ChromaDB persistent store (auto-created)
│   ├── feynman_memory.db       # SQLite memory store (auto-created)
│   └── sources/                # Drop .txt files here for custom ingestion
└── docs/
    ├── README.md               # This file
    └── sample_conversations.md # 10 sample conversations
```
