# Wraith — Development Progress

## Project Overview
A codebase-aware developer assistant that ingests any Python project,
answers questions with file and line references, detects bugs,
analyzes GitHub issues, and suggests fixes grounded in your actual code.

---

## Phase 1 — Ingestion Pipeline
**Status:** Complete
**Files:** ingestion/file_parser.py, ingestion/chunker.py, 
           ingestion/embedder.py, storage/vector_store.py

**What was built:**
- File scanner that walks any project folder and filters junk
- AST-based function-level chunker with sliding window fallback
- Embedding engine using all-MiniLM-L6-v2 (384 dimensions, runs locally)
- ChromaDB vector store with cosine similarity search

**Key decisions:**
- Upgraded from sliding window to AST chunking mid-build
- Chunks went from 72 to 108 on Smart Attendance System
- Non-Python files use sliding window automatically

---

## Phase 2 — Q&A Core
**Status:** Complete
**Files:** agent/qa_engine.py

**What was built:**
- Full RAG pipeline: embed question, search chunks, build prompt, call LLM
- Groq API integration with LLaMA 3.1 8B
- Temperature set to 0.2 for precise factual answers
- Source citations with file names and line numbers in every answer

---

## Phase 3 — Agent Brain
**Status:** Complete
**Files:** agent/agent.py, tools/code_tools.py

**What was built:**
- ReAct reasoning loop: Reason, Act, Observe, Repeat
- 4 tools: search_codebase, read_file, list_files, get_file_summary
- Max 3 iterations to stay within Groq free tier token limits
- Conversation history grows with each iteration

**Key decisions:**
- Reduced MAX_ITERATIONS from 5 to 3 due to Groq TPM limits
- Reduced n_results from 5 to 3 per search for same reason

---

## Phase 4 — Bug Detection & Security Analysis
**Status:** Complete
**Files:** tools/analyzer.py

**What was built:**
- File-by-file code analysis for bugs, security issues, anti-patterns
- Security scan using semantic search for dangerous patterns
- Skips test files and scripts, focuses on core logic

**Results on Smart Attendance System:**
- Found student_id type mismatch between database tables
- Found echo=True exposing SQL queries in logs
- Found missing error handling in end_session method
- Found potential resource leak in cv2.VideoCapture

---

## Phase 5 — GitHub Issues Integration
**Status:** Complete
**Files:** tools/github_tool.py

**What was built:**
- GitHub API integration to fetch real issues by URL
- Semantic search to find relevant code for the issue
- Multi-file reading for better context
- Strict prompt rules to reduce hallucination
- Confidence scoring — responses below 80/100 are flagged

**Known limitation:**
- If relevant code spans files not returned by semantic search,
  Wraith may analyze the wrong file. Documented in KNOWN_ISSUES.md

---

## Phase 6 — Web Research Assistant
**Status:** complete
**Files:** tools/web_research.py 

**What was built:**
- Automatic tech stack detection from codebase
- Web search via DuckDuckGo (free, no API key)
- Stack-aware recommendations grounded in actual dependencies
- LLM synthesizes web results into recommendations for your exact stack

---

## Phase 7 — FastAPI Backend & Dashboard
**Status:** Not Started
**Files:** api/main.py, api/static/index.html (to be created)

**What will be built:**
- REST API wrapping all Wraith capabilities
- Clean web dashboard for non-terminal usage
- Endpoints for Q&A, bug analysis, issue solving, web research

---

## Known Issues & Limitations
See dev_journal.md for full details.

Summary:
- LLM hallucination when retrieved context is incomplete (partially fixed)
- Groq free tier token limits cap iteration depth
- AST chunking only works for Python files

---

## Stack
- Python 3.10.11
- ChromaDB (local vector database)
- sentence-transformers / all-MiniLM-L6-v2 (local embeddings)
- Groq API / LLaMA 3.1 8B (LLM)
- duckduckgo-search (Phase 6, web research)
- FastAPI (Phase 7, backend)

---

## Timeline
- Phase 1-5: Built over approximately 5 weeks
- Phase 6-7: In progress