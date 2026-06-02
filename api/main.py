import os
import sys
sys.path.append("..")
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.qa_engine import QAEngine
from agent.agent import WraithAgent
from tools.analyzer import CodeAnalyzer
from tools.github_tool import GitHubIssueSolver
from tools.web_research import WebResearcher

load_dotenv()

app = FastAPI(
    title="Wraith API",
    description="Codebase-aware developer assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Models ---
class IngestRequest(BaseModel):
    codebase_path: str

class QuestionRequest(BaseModel):
    codebase_path: str
    question: str

class AgentRequest(BaseModel):
    codebase_path: str
    question: str

class AnalyzeRequest(BaseModel):
    codebase_path: str

class IssueRequest(BaseModel):
    codebase_path: str
    issue_url: str

class ResearchRequest(BaseModel):
    codebase_path: str
    problem: str

# --- State ---
active_codebase = {}
print("about to create QAEngine")
engine = QAEngine()
print("QAEngine created")



# --- Routes ---

app.mount("/static", StaticFiles(directory="api/static"), name="static")


@app.get("/")
def root():
    return FileResponse("api/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest):
    try:
        from ingestion.file_parser import get_all_files, read_file
        from ingestion.chunker import chunk_codebase
        
        from storage.vector_store import VectorStore

        files = get_all_files(request.codebase_path)
        contents = [read_file(f) for f in files]

        from ingestion.chunker import chunk_codebase
        chunks = chunk_codebase(files, contents)

        
        embedded = engine.embedder.embed_chunks(chunks)

        store = VectorStore(request.codebase_path)
        # store.clear()
        store.add_chunks(embedded)

        active_codebase["path"] = request.codebase_path

        return {
            "success": True,
            "files_found": len(files),
            "chunks_stored": len(embedded),
            "codebase_path": request.codebase_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        result = engine.ask(request.question, request.codebase_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent")
def agent(request: AgentRequest):
    try:
        a = WraithAgent(codebase_path=request.codebase_path)
        answer = a.run(request.question)
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        analyzer = CodeAnalyzer(codebase_path=request.codebase_path)
        results = analyzer.analyze_codebase()
        security = analyzer.security_scan()
        return {
            "file_analysis": results,
            "security_scan": security
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/issue")
def solve_issue(request: IssueRequest):
    try:
        solver = GitHubIssueSolver(codebase_path=request.codebase_path)
        result = solver.solve_issue(request.issue_url)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research")
def research(request: ResearchRequest):
    try:
        researcher = WebResearcher(codebase_path=request.codebase_path)
        result = researcher.research(request.problem)
        return {
            "problem": request.problem,
            "stack": researcher.stack,
            "recommendation": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))