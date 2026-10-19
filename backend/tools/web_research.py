import os
import sys
sys.path.append("..")
from dotenv import load_dotenv
from groq import Groq
from ddgs import DDGS
from ingestion.file_parser import get_all_files, read_file

load_dotenv()

MODEL = "llama-3.1-8b-instant"

class StackDetector:
  def __init__(self, codebase_path: str):
    self.codebase_path = codebase_path

  def detect(self) -> dict:
    stack = {
      "languages": [],
      "frameworks": [],
      "databases": [],
      "libraries": []
    }

    files = get_all_files(self.codebase_path)
    all_content = ""

    for f in files:
      if f["extension"] in [".txt", ".toml", ".cfg"] or \
         "requirements" in f["relative_path"].lower() or \
         "setup" in f["relative_path"].lower():
        content = read_file(f)
        if content:
          all_content += content + "\n" 

    for f in files:
      ext = f["extension"]
      if ext == ".py" and "python" not in stack["languages"]:
        stack["languages"].append("python")
      elif ext in [".js", ".jsx"] and "JavaScript" not in stack["languages"]:
        stack["languages"].append("javascript")
      elif ext in [".ts", ".tsx"] and "Typescript" not in stack["languages"]:
        stack["languages"].append("TypeScript")

    keywords = {
        "frameworks": {
            "fastapi": "FastAPI",
            "flask": "Flask",
            "django": "Django",
            "express": "Express",
            "react": "React",
            "vue": "Vue"
        },
        "databases": {
            "postgresql": "PostgreSQL",
            "sqlite": "SQLite",
            "mongodb": "MongoDB",
            "mysql": "MySQL",
            "chromadb": "ChromaDB",
            "redis": "Redis"
        },
        "libraries": {
            "sqlalchemy": "SQLAlchemy",
            "pydantic": "Pydantic",
            "numpy": "NumPy",
            "opencv": "OpenCV",
            "insightface": "InsightFace",
            "dlib": "dlib",
            "sentence_transformers": "SentenceTransformers",
            "chromadb": "ChromaDB"
        }
    }

    content_lower = all_content.lower()

    for f in files:
        file_content = read_file(f)
        if file_content:
            content_lower += file_content.lower()

    for category, items in keywords.items():
        for keyword, name in items.items():
            if keyword in content_lower and name not in stack[category]:
                stack[category].append(name)

    return stack


class WebResearcher:
    def __init__(self, codebase_path: str):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.codebase_path = codebase_path
        self.stack_detector = StackDetector(codebase_path)
        self.stack = self.stack_detector.detect()
        print(f"\nDetected stack: {self.stack}")

    def _search_web(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _build_stack_query(self, problem: str) -> str:
        stack_terms = []
        stack_terms.extend(self.stack.get("languages", []))
        stack_terms.extend(self.stack.get("frameworks", []))
        stack_terms.extend(self.stack.get("databases", []))
        stack_string = " ".join(stack_terms[:4])
        return f"{problem} {stack_string}"

    def research(self, problem: str) -> str:
        print(f"\nResearching: '{problem}'")

        query = self._build_stack_query(problem)
        print(f"Search query: '{query}'")

        results = self._search_web(query)

        if not results:
            return "No web results found."

        search_context = ""
        for i, r in enumerate(results):
            search_context += (
                f"Result {i+1}:\n"
                f"Title: {r.get('title', '')}\n"
                f"Summary: {r.get('body', '')[:300]}\n\n"
            )

        stack_description = (
            f"Languages: {', '.join(self.stack['languages'])}\n"
            f"Frameworks: {', '.join(self.stack['frameworks'])}\n"
            f"Databases: {', '.join(self.stack['databases'])}\n"
            f"Libraries: {', '.join(self.stack['libraries'])}"
        )

        prompt = f"""You are Wraith, a developer assistant with knowledge of the user's tech stack.

The user's tech stack is:
{stack_description}

The user has this problem:
{problem}

Here are web search results that may help:
{search_context}

Based on the search results and the user's specific stack, provide:
1. The best solution for their exact stack
2. A concrete code example using their actual libraries
3. Any stack-specific gotchas or warnings
4. Link to the most relevant resource

Be direct and specific to their stack. No generic advice."""

        response = self.client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return response.choices[0].message.content


if __name__ == "__main__":
    codebase = sys.argv[1] if len(sys.argv) > 1 else "."

    researcher = WebResearcher(codebase_path=codebase)

    problems = [
        "how to handle database connection pooling",
        "how to speed up face recognition inference",
        "best way to handle authentication in API"
    ]

    for problem in problems:
        print(f"\n{'='*50}")
        print(f"PROBLEM: {problem}")
        print(f"{'='*50}")
        result = researcher.research(problem)
        print(result)
        