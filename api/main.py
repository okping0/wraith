import os
import sys
import tempfile
import shutil
import subprocess
import stat
from dotenv import load_dotenv

sys.path.append("..")
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel


from agent.qa_engine import QAEngine
from agent.agent import WraithAgent
from tools.analyzer import CodeAnalyzer
from tools.github_tool import GitHubIssueSolver
from tools.web_research import WebResearcher

from typing import Optional
from database.models import User


load_dotenv()

app = FastAPI(
    title="Wraith API",
    description="Codebase-aware developer assistant",
    version="1.0.0",
    swagger_ui_parameters={"persistentAuthorization": True}
)

security = HTTPBearer(auto_error=False)

from database.database import engine as db_engine
from database import models
models.Base.metadata.create_all(bind=db_engine)


from auth.dependencies import get_current_user

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


def resolve_path(codebase_path: str) -> tuple[str, bool]:
    """Returns(actual_path, is_temp). If is_temp=True caller must delete after"""
    if codebase_path.startswith("https://github.com"):
        tmp_dir = tempfile.mkdtemp()
        subprocess.run(["git", "clone", codebase_path, tmp_dir], check=True)
        return tmp_dir, True
    return codebase_path, False

def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)



# --- Routes ---

from auth.auth_router import router as auth_router
app.include_router(auth_router)

app.mount("/static", StaticFiles(directory="api/static"), name="static")


@app.get("/")
def root():
    return FileResponse("api/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(request: IngestRequest, current_user:Optional[User]=Depends(get_current_user)):
    try:
        from ingestion.file_parser import get_all_files, read_file
        from ingestion.chunker import chunk_codebase
        
        from storage.vector_store import VectorStore

        path, is_temp = resolve_path(request.codebase_path)
        try:
            files = get_all_files(path)
            contents = [read_file(f) for f in files]

        finally:
            if is_temp:
                shutil.rmtree(path, onerror=remove_readonly)

        from ingestion.chunker import chunk_codebase
        chunks = chunk_codebase(files, contents)

        
        embedded = engine.embedder.embed_chunks(chunks)

        store = VectorStore(request.codebase_path)
        # store.clear()
        store.add_chunks(embedded)

        if current_user:
            print(f"Authenticated ingest for user : {current_user.username}")
        else:
            print("guest ingest - no persistent tracking")

        active_codebase["path"] = request.codebase_path

        return {
            "success": True,
            "files_found": len(files),
            "chunks_stored": len(embedded),
            "codebase_path": request.codebase_path
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
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