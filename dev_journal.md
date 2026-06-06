# Wraith — Developer Journal

> This document is a living record of every major decision, mistake, and lesson from building Wraith. Not a polished post-mortem — an honest account of what happened and why.

---

## Why I Built This

Everyone around me was doing open source contributions. I decided to give it a try — opened a large, unfamiliar codebase and felt completely lost. No idea where anything was, what connected to what, or where to even begin. I spent more time navigating than actually understanding.

That frustration became the idea: what if there was a tool that could just *tell you* about a codebase? Ask it a question, get an answer with the exact file and line number. Paste a GitHub issue URL, get a fix suggestion grounded in the actual code.

That's Wraith. A codebase-aware AI agent — not a generic chatbot, but one that has actually read your code.

---

## Architecture Overview

```
GitHub URL
    ↓
git clone → temp directory
    ↓
file_parser.py     → walks directory, filters junk, reads files
    ↓
chunker.py         → AST-based chunking (Python) + sliding window fallback
    ↓
embedder.py        → Jina AI API (jina-embeddings-v2-base-code)
    ↓
vector_store.py    → ChromaDB (in-memory, cosine similarity)
    ↓
qa_engine.py       → RAG: embed query → search → build prompt → LLM
    ↓
agent.py           → ReAct loop: Reason → Act → Observe → Repeat
    ↓
api/main.py        → FastAPI backend
    ↓
api/static/        → HTML/CSS/JS frontend dashboard
```

**LLM:** LLaMA 3.1 8B Instant via Groq API  
**Embedding:** Jina AI (API-based, code-specific)  
**Vector DB:** ChromaDB  
**Backend:** FastAPI  
**Frontend:** Vanilla HTML, CSS, JavaScript  

---

## Phase 1 — Ingestion Pipeline

The foundation of everything. A codebase is useless to an LLM as raw text — it needs to be parsed, chunked, embedded, and stored in a way that supports semantic search.

### File Parsing

Built `file_parser.py` to walk a directory, skip junk (`node_modules`, `__pycache__`, `venv`, etc.), and read supported file types. Simple in concept but tricky in practice.

**Problem: UTF-16 encoded files**

Some files like `requirements.txt` were returning garbage values — raw hex like `\x00` instead of readable text. The issue was that my file parser only handled UTF-8. Files encoded in UTF-16 (which Windows sometimes produces) were being read as binary noise and passed downstream into the chunker and embedder.

**Fix:** Added a fallback in `read_file()` — try UTF-8 first, catch `UnicodeDecodeError`, then retry with UTF-16. If both fail, return `None` and skip the file. The chunker already handles `None` gracefully with an early `continue`.

**Lesson:** Never assume encoding. Real codebases have files from different systems, editors, and eras.

---

### Chunking Strategy — Why AST over Sliding Window

The naive approach is sliding window chunking — take every N lines, slide forward with overlap. It works, but it has a fundamental flaw: it can cut a function in half. A chunk that starts mid-function has no context — the LLM reads it and has no idea what class it belongs to, what the parameters mean, or what the function is supposed to do.

**The fix:** AST-based chunking for Python files. Instead of blindly cutting every 40 lines, parse the code using Python's `ast` module and cut at natural boundaries — functions, classes, and methods. Each chunk is a complete, meaningful unit.

**Result:** On the Smart Attendance System codebase, chunks went from 72 (sliding window) to 108 (AST). More chunks, better quality — each one semantically complete.

**Limitation:** AST parsing only works for Python. For other languages, sliding window is the fallback. The right long-term fix is `tree-sitter`, a multi-language parser. Planned but not yet implemented — it adds build complexity that isn't worth it before the core product is stable.

---

### Embedding Model — Why I Switched from all-MiniLM to Jina

Started with `sentence-transformers/all-MiniLM-L6-v2` — a popular, fast local embedding model. It worked, but had two problems:

**1. It's not code-aware.**  
all-MiniLM is trained on general text. It doesn't understand that `def authenticate(token)` and "how does login work" are semantically related. Jina's `jina-embeddings-v2-base-code` is trained specifically on code and understands this relationship much better.

**2. It pulls in PyTorch.**  
Sentence Transformers depends on PyTorch. PyTorch is enormous — 2-4 GB easily. Render's free tier has 512MB of RAM. The app was crashing before it even started serving requests.

**Switch:** Moved to Jina's API. No local model, no PyTorch, no torch in requirements.txt. Embedding happens over an HTTP call to Jina's servers.

**Trade-off acknowledged:** API-based embedding adds network latency to ingestion. But ingestion is a one-time operation per codebase — acceptable. Query time is still fast because only the query embedding hits the API, and ChromaDB search is local.

---

### Batch Embedding & Retry Logic

Jina's API accepts batches of text. Chunks are sent in batches of 50. But occasionally a batch fails — Jina returns `{"detail": {"message": "Failed to encode text"}}` with no further explanation.

**Initial approach:** Retry each item in the failed batch one-by-one. This worked but was slow — a failed batch of 50 means 50 separate HTTP requests.

**Better approach:** Recursive binary retry. If a batch fails, split it in half and retry each half. If a half fails, split again. If a single item fails, skip it. One bad chunk causes at most `log2(50) ≈ 6` extra requests instead of 50.

This is divide-and-conquer applied to API reliability.

**Silent misalignment bug:** Bad chunks were being dropped with `return []`, making the embeddings list shorter than the chunks list. The `zip(chunks, embeddings)` at the end was misaligning — chunk B was getting paired with chunk C's embedding. Fixed by returning `[None]` instead of `[]` for skipped chunks, keeping both lists the same length. The cleanup step filters `None` embeddings after zipping.

---

## Phase 2 — Q&A Engine (RAG from Scratch)

The RAG pipeline:
1. Embed the user's question
2. Search ChromaDB for the most similar chunks
3. Build a prompt with those chunks as context
4. Call the LLM and return the answer with source citations

Straightforward in theory. The hard part was quality.

### Hallucination Problem & Relevance Threshold

Without a relevance threshold, ChromaDB returns the top N results regardless of how irrelevant they are. Ask "how does authentication work" in a codebase with no authentication — Wraith still finds *something* and the LLM builds a confident, plausible-sounding, completely wrong answer around it.

**Fix:** Added a `RELEVANCE_THRESHOLD` constant. Chunks below the threshold score are filtered out before building the prompt. If no chunks pass the threshold, Wraith says it can't find relevant information instead of hallucinating.

**Lesson:** Retrieval quality gates response quality. Garbage in, garbage out — but with LLMs, the garbage comes out sounding very confident.

---

## Phase 3 — The Agent (ReAct Loop)

The Q&A engine handles direct questions. But some tasks need multi-step reasoning — "find the bug in the authentication flow" requires searching multiple files, reading them, and synthesizing across them.

The agent uses a ReAct loop: **Reason** about what to do, **Act** by calling a tool, **Observe** the result, repeat.

**Tools:**
- `search_codebase` — semantic search in ChromaDB
- `read_file` — read a full file by path
- `get_file_summary` — get a short summary of a file
- `github_issue_solver` — analyze a GitHub issue against the codebase
- `web_research` — search the web for relevant information

### Why Text-Based Tool Calling

OpenAI's function calling API lets you define tools as JSON schemas and the model calls them natively. Groq's free tier doesn't support this.

**Workaround:** Prompt-based tool calling. The system prompt tells the LLM to respond in a specific format when it wants to use a tool:

```
TOOL: search_codebase
INPUT: how does authentication work
```

The agent parses this with string matching, calls the actual Python function, and feeds the result back. It's fragile — the LLM sometimes formats it wrong — but it works within the free tier constraints.

**Trade-off:** This is a known limitation. If Groq adds free-tier function calling, or if I switch providers, this can be replaced properly.

---

## Phase 4 & 5 — Analyzer and GitHub Issues

The analyzer runs file-by-file analysis looking for bugs, security issues, and anti-patterns. The GitHub issues tool fetches a real issue via the GitHub API and runs the agent against the codebase.

**Problem:** The LLM would sometimes confidently report that an issue was still open and unfixed — even when the fix was already in the codebase.

**Fix:** Updated the prompt to explicitly instruct the LLM to first check whether the issue is already resolved before suggesting fixes.

---

## Phase 6 — Web Research

Detects the tech stack from the codebase (by scanning imports and file types), then runs a DuckDuckGo search grounded in those actual dependencies. A generic "how do I fix X" answer is less useful than one that knows you're using FastAPI + ChromaDB + Python 3.10.

No API key needed — uses `ddgs`.

---

## Phase 7 — FastAPI Backend & Deployment

### The ChromaDB Multiton Bug

Early on, every ingestion was writing to the same ChromaDB collection. Ingest Repo A, then Repo B — Repo B's chunks mix with Repo A's. Questions about Repo A get answers from Repo B's code.

**First attempt:** Singleton pattern — one `VectorStore` instance for the whole app. Still the same problem because one instance still meant one collection.

**Actual fix:** Multiton pattern. A registry (Python dictionary) maps each codebase path to its own `VectorStore` instance with its own isolated collection. The `__new__` method checks the registry before creating anything new.

```python
_instances = {}

def __new__(cls, codebase_path: str):
    collection_name = os.path.basename(codebase_path)
    if collection_name not in cls._instances:
        cls._instances[collection_name] = super().__new__(cls)
    return cls._instances[collection_name]
```

**Lesson:** Shared mutable state is always a bug waiting to happen. Isolate state per resource from the beginning.

---

### Slow Startup Bug

The app was re-loading the embedding model from scratch on every request — a 10-20 second delay on the first query after any restart.

**Root cause:** `QAEngine` was being instantiated inside the request handler. Every request created a new engine, which triggered model loading.

**Fix:** Instantiate `QAEngine` once at module level when FastAPI starts. All requests share the same instance. Model loads once, stays loaded.

---

### Deployment on Render — What Broke

**Problem 1: requirements.txt was enormous**  
The original `requirements.txt` was from `pip freeze` — it included PyTorch, sentence-transformers, and their entire dependency tree. Render was downloading gigabytes of packages on every deploy.

Fix: Used `pipreqs` to generate a minimal requirements.txt from actual imports. Went from ~80 packages to 8.

**Problem 2: ChromaDB PersistentClient on ephemeral filesystem**  
Render's free tier wipes the filesystem on every restart. `PersistentClient` saves to disk — which disappears. Users ingest a codebase, server restarts, all vectors are gone.

Fix: Switched to `chromadb.Client()` (in-memory). Users re-ingest after a restart. Acceptable for now — the right long-term fix is a managed vector DB like Qdrant Cloud, which would make the app fully stateless.

**Problem 3: Frontend hardcoded to localhost**  
`app.js` had `const API = "http://localhost:8000"`. Every user hitting the deployed URL was accidentally routing to their own machine, which had no server running.

Fix: Changed to `const API = ""` — empty string means relative URLs. `fetch("/ingest")` works on both localhost and production with no changes needed between environments.

**Problem 4: Local path ingestion doesn't work in production**  
The ingest endpoint accepted a local filesystem path. On Render's server, no user's local files exist.

Fix: Added `resolve_path()` — detects if the input is a GitHub URL, clones it to a temp directory using `subprocess` + `git clone`, runs ingestion on that directory, then cleans up with `shutil.rmtree()` after all file contents are already read into memory.

---

## Known Issues & Limitations

| Issue | Status | Notes |
|-------|--------|-------|
| In-memory ChromaDB — data lost on restart | Open | Right fix is Qdrant Cloud |
| AST chunking Python-only | Open | tree-sitter planned |
| Text-based tool calling fragile | Open | Needs native function calling from Groq |
| Agent only reads top matched file fully | Open | Multi-file reading planned |
| No auth / persistent sessions | Open | Needed for real multi-user production |
| Large repos slow to ingest | Open | Parallel embedding planned |
| Binary files not filtered in file_parser | Open | Fix planned |
| start_line off-by-one in chunker | Open | Minor, cosmetic |

---

## Privacy Considerations
Wraith currently sends code chunks to two external APIs — Jina (embeddings) and Groq (LLM). This means code leaves the user's system. For privacy-sensitive or proprietary codebases, a fully local mode using Ollama + a local embedding model is planned.

---

## What I Learned

**Retrieval quality determines response quality.**  
The LLM is only as good as the context you give it. Bad chunking, no relevance threshold, wrong embedding model — any of these makes even the best LLM produce confident garbage. Most debugging time was spent on retrieval, not generation.

**API-based vs local models is a real trade-off.**  
Local models are fast and free but heavy. API models are lightweight and deployable but add latency and cost. For production on free tiers, API-based is the only viable option. Design for this from the start — don't switch mid-project like I did.

**Shared state is always a bug.**  
The multiton fix was one of the most impactful changes. One collection for all codebases seemed fine in development (I only tested one codebase at a time). In production with multiple users, it's a disaster. Isolate state early.

**Ship first, optimize later.**  
Parallel embedding, tree-sitter, Qdrant — all better than what's in production now. But the app is live, working, and usable. Perfect is the enemy of shipped.

**Document decisions when you make them.**  
Half the content in this journal came from memory months later. Write down *why* you made a decision at the time you make it. Future you will not remember.

---

## Roadmap

- [ ] Qdrant Cloud for persistent vector storage
- [ ] tree-sitter for multi-language AST chunking
- [ ] Parallel embedding for faster ingestion
- [ ] Native function calling (when Groq supports it)
- [ ] User authentication and persistent sessions
- [ ] Full open source automation pipeline

---

*Last updated: June 2026 — Wraith v1.0 deployed on Render*