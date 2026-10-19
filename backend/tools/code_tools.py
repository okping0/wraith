import sys
sys.path.append("..")
from ingestion.file_parser import get_all_files, read_file as read_file_content
from storage.vector_store import VectorStore
from ingestion.embedder import CodeEmbedder

RELEVANCE_THRESHOLD = 0.4

embedder = CodeEmbedder()

def search_codebase(query: str, codebase_path: str, n_results: int = 3) -> str:
  query_embedding = embedder.embed_text(query)
  results = VectorStore(codebase_path).search(query_embedding, n_results)
  
  if not results:
    return "No relevant Code found."
   
  output = []
  for i, r in enumerate(results):
    if r['score'] >=RELEVANCE_THRESHOLD:
        output.append(
        f"Result {i+1}: \n"
        f"File: {r['metadata']['file_path']}\n"
        f"Lines: {r['metadata']['start_line']} - {r['metadata']['end_line']}\n"
        f"Score: {r['score']:.3f}\n"
        f"Code:\n{r['text']}\n"
        )
  if not output:
      return "No relevant code found above confidence threshold"
    
  output = [o[:500] for o in output]
#   improvement - result is cut to 500 characters individually
  return "\n".join(output)

def read_file(file_path: str, codebase_path: str) -> str:
    import os
    full_path = os.path.join(codebase_path, file_path)
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        numbered = [f"{i+1:4d} | {line}" for i, line in enumerate(lines)]
        return "".join(numbered)
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"
    


def list_files(codebase_path: str) -> str:
    files = get_all_files(codebase_path)
    if not files:
        return "No files found."
    output = []
    for f in files:
        size_kb = f['size_bytes'] / 1024
        output.append(f"{f['relative_path']:<50} {size_kb:.1f} KB")
    return "\n".join(output)


def get_file_summary(file_path: str, codebase_path: str) -> str:
    content = read_file(file_path, codebase_path)
    if "Error" in content or "not found" in content:
        return content
    preview = "\n".join(content.split("\n")[:50])
    return f"First 50 lines of {file_path}:\n{preview}"



TOOLS = {
    "search_codebase": {
        "fn": search_codebase,
        "description": "Search the codebase semantically. Use this when you need to find code related to a concept or feature.",
        "params": ["query", "codebase_path"]
    },
    "read_file": {
        "fn": read_file,
        "description": "Read the full contents of a specific file with line numbers.",
        "params": ["file_path", "codebase_path"]
    },
    "list_files": {
        "fn": list_files,
        "description": "List all files in the codebase with their sizes.",
        "params": ["codebase_path"]
    },
    "get_file_summary": {
        "fn": get_file_summary,
        "description": "Get the first 50 lines of a file as a quick summary.",
        "params": ["file_path", "codebase_path"]
    },
}