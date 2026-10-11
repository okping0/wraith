import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "jina-code-embeddings-1.5b"
BATCH_SIZE = 50


class CodeEmbedder:
  def __init__(self):
    self.url = "https://api.jina.ai/v1/embeddings"
    self.headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer jina_{os.getenv('JINA_API_KEY')}"
    }
    print("model loaded successfully")


  def embed_text(self,text:str) -> list[float]:
    self.data = {
      "model": MODEL_NAME,
      "task": "nl2code.query",
      "truncate": False,
      "input": [text]
    }
    response = requests.post(self.url, headers=self.headers, data=json.dumps(self.data))
    embedding = [item["embedding"] for item in response.json()["data"]]
    return embedding[0]
  

  def embed_batch_with_retry(self, batch):
    self.data = {
      "model": MODEL_NAME,
      "task": "nl2code.passage",
      "truncate": True,
      "input": batch
    }
    response = requests.post(self.url, headers=self.headers, data=json.dumps(self.data))
    
    if "data" in response.json():
        return [item["embedding"] for item in response.json()["data"]]
    
    if len(batch) == 1:
        print(f"Skipping bad chunk: {batch[0][:50]}")
        return [None]
    
    mid = len(batch) // 2
    left = self.embed_batch_with_retry(batch[:mid])
    right = self.embed_batch_with_retry(batch[mid:])
    return left + right



  def embed_chunks(self, chunks : list[dict]) -> list[dict]:
    print(f"\nEmbedding {len(chunks)} chunks...")
    texts = [chunk["text"] for chunk in chunks]

    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]
        print(f"Sending batch {i} to {i+len(batch)}, sample: {batch[0][:5]}")
        all_embeddings.extend(self.embed_batch_with_retry(batch))

    embedded_chunks = []
    for chunk, embedding in zip(chunks, all_embeddings):
      if embedding is None:
         continue
      embedded_chunks.append({
        "text": chunk["text"],
        "embedding": embedding,
        "metadata": chunk["metadata"]
      }) 
    return embedded_chunks



if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.file_parser import get_all_files, read_file
    from ingestion.chunker import chunk_codebase

    path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    files = get_all_files(path)
    contents = [read_file(f) for f in files]
    chunks = chunk_codebase(files, contents)

    embedder = CodeEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks)

    print(f"\nWraith Embedder")
    print(f"{'='*40}")
    print(f"Chunks embedded:     {len(embedded_chunks)}")
    print(f"Embedding dimension: {len(embedded_chunks[0]['embedding'])}")
    print(f"Sample file:         {embedded_chunks[0]['metadata']['file_path']}")
    print(f"Sample lines:        {embedded_chunks[0]['metadata']['start_line']} to {embedded_chunks[0]['metadata']['end_line']}")
    print(f"\nFirst 5 embedding values:")
    print(embedded_chunks[0]['embedding'][:5])