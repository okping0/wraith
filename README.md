# Wraith
> It knows your code better than you do.

## The Story

Everyone around me was doing open source contributions, so I decided to give it a try. I opened a large codebase and felt completely lost — no idea where anything was, what connected to what, or where to even start. That's when it clicked: what if there was a tool that could just *tell* you?

Wraith is a codebase-aware AI agent. Paste a GitHub repo URL, and start asking questions. No cloning, no IDE setup, no local environment needed.

It's built for developers who are new to a codebase, or open source contributors who want help understanding and solving real issues.

## Live Demo
🔗 [wraith-6efg.onrender.com](https://wraith-6efg.onrender.com)

> Note: Hosted on Render free tier — first load may take ~50 seconds to wake up.

## Features

- **Q&A Engine** — Ask anything about a codebase. Get answers with file and line references.
- **Agent** — Give Wraith a task and it reasons through which tools to use to solve it.
- **Analyzer** — Scans the codebase for bugs, anti-patterns, and potential issues.
- **GitHub Issues** — Paste an issue URL and Wraith analyzes it against the actual codebase.
- **Web Research** — Research coding problems with context from your actual tech stack.

## What Makes It Different

Tools like Copilot and Cursor require you to have the code locally and install IDE extensions. Wraith just needs a GitHub URL — paste it, hit ingest, start asking questions.

## How It Works
GitHub URL → git clone → file parsing → AST chunking →
Jina embeddings → ChromaDB → semantic search → LLaMA 3 → answer

- Files are parsed and chunked using AST-based splitting for Python (functions and classes as chunks) with sliding window fallback for other languages
- Chunks are embedded using Jina's `jina-embeddings-v2-base-code` model
- Stored in ChromaDB for semantic search
- A ReAct agent loop decides which tools to use for each query
- LLaMA 3.1 8B Instant (via Groq) generates the final response

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Embeddings | Jina AI |
| LLM | LLaMA 3.1 8B via Groq |
| Vector DB | ChromaDB |

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/okping0/wraith
cd wraith

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Add your GROQ_API_KEY and JINA_API_KEY

# 4. Run the server
uvicorn api.main:app --reload
```

Then open `http://localhost:8000` and paste a GitHub repo URL to get started.

## Roadmap

- [ ] Auto-clone directly from a gitHub issue URL
- [ ] User authentication and persistent sessions
- [ ] Parallel embedding for faster ingestion
- [ ] Local mode — fully offline with Ollama + local embeddings for privacy-sensitive codebases
- [ ] Support for private repositories
- [ ] Full open source automation pipeline

## Known Limitations

- In-memory ChromaDB — ingested data is lost on server restart
- Large repos (1000+ chunks) take longer to ingest due to Jina API rate limits
- Agent tool calling is text-based (Groq free tier workaround)