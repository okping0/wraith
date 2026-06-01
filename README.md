# Wraith
> It knows your code better than you do.

A codebase-aware developer assistant that understands your code,
answers questions with file and line references, detects bugs,
reads GitHub issues, and suggests fixes.

## Built With
- Python 3.10
- ChromaDB
- Sentence Transformers
- FastAPI (Phase 7)

## Phase 1 — Foundation & Ingestion Engine
Project setup, folder structure, parsing a real codebase into chunks, generating embeddings, storing in a vector DB. Understanding why chunking strategy matters and how semantic search works.
(COMPLETED)


## Phase 2 — The Q&A Core (RAG from scratch)
Build the retrieve → augment → generate pipeline. Ask questions, get answers with file + line references. No magic wrappers.
(COMPLETED)
### Known Limitations (Phase 2)
- May hallucinate implementation details
- Retrieval may miss relevant files
- Responses may repeat or lack grounding

These will be addressed in Phase 3 (Agent + Retrieval Improvements)

## Phase 3 — The Agent Brain & Tool Use
Give assistant tools: search the vector DB, read a file, call the GitHub API, search the web. Build a reasoning loop that decides which tool to use and when.

## Phase 4 — Bug Detection & Security Analysis
Static analysis integration + LLM-powered anti-pattern detection. The agent reads code and flags issues with explanations.

## Phase 5 — GitHub Issues Integration
Pull issues via API, run the full issue → locate → fix → explain pipeline.

## Phase 6 — Web Research Assistant
Stack-aware search: detect your tech stack from the codebase, then answer questions using live web search grounded in your actual dependencies.

## Phase 7 — Dashboard & API
FastAPI backend + a clean frontend so this feels like a real product, not a script.

### CURRENT - 
improving the whole app ui, ux, bugs, and making it ready for deployment
