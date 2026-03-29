import os
import sys
sys.path.append("..")
from dotenv import load_dotenv
from groq import Groq
from storage.vector_store import VectorStore
from ingestion.embedder import CodeEmbedder

load_dotenv()

MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHUNKS = 5

class QAEngine:
  def __init__(self):
    self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    self.vector_store = VectorStore()
    self.embedder = CodeEmbedder()
    print("Wraith QA Engine ready")

  def _build_context(self, chunks: list[dict]) -> str:
    context_parts = []

    for i, chunk in enumerate(chunks):
      file_path = chunk["metadata"]["file_path"]
      start_line = chunk["metadata"]["start_line"]
      end_line = chunk["metadata"]["end_line"]
      score = chunk["score"]

      context_parts.append(
        f"--Chunk {i+1} --\n"
        f"File: {file_path}\n"
        f"Lines: {start_line} to {end_line}\n"
        f"Relevance: {score:.3f}\n"
        f"Code:\n{chunk['text']}\n"
      )

    return "\n".join(context_parts)
  
  def _build_prompt(self, question: str, context:str) -> str:
            return f"""You are Wraith, an expert developer assistant with deep knowledge of the codebase provided below.

Your job is to answer questions about this codebase precisely and technically.

Always:
- Reference specific file names and line numbers in your answer
- Explain what the code is doing, not just where it is
- If you see a bug or issue while answering, mention it
- Be direct and precise — no fluff

Codebase context:
{context}

Developer question: {question}

Answer:"""
  
  def ask(self, question: str) -> dict:
      print(f"\nSearching codebase forf : {question}")

      query_embedding = self.embedder.embed_text(question)
      relevant_chunks = self.vector_store.search(
          query_embedding,
          n_results= MAX_CONTEXT_CHUNKS)
      
      context = self._build_context(relevant_chunks)
      prompt = self._build_prompt(question, context)

      print("Thinking...")

      response = self.client.chat.completions.create(
          model=MODEL,
          messages=[
              {"role": "user", "content": prompt}
          ],
          temperature=0.2
      )

      answer = response.choices[0].message.content

      return {
          "question": question,
          "answer":answer,
          "sources": [
              {
                  "file": c["metadata"]["file_path"],
                  "lines":f"{c['metadata']['start_line']} - {c['metadata']['end_line']}",
                  "score": c["score"]
              }
              for c in relevant_chunks
          ]
      }