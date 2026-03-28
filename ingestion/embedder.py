from sentence_transformers import SentenceTransformer
from tqdm import tqdm


MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 32

class CodeEmbedder:
  def __init__(self):
    print(f"loading embedding model: {MODEL_NAME}")
    self.model = SentenceTransformer(MODEL_NAME)
    print("model loaded successfully")

  def embed_text(self,text:str) -> list[float]:
    embedding = self.model.encode(text, convert_to_numpy=True)
    return embedding.tolist()
  
  def embed_chunks(self, chunks : list[dict]) -> list[dict]:
    print(f"\nEmbedding {len(chunks)} chunks...")
    texts = [chunk["text"] for chunk in chunks]
    embedidngs = self.model.encode(
      texts,
      batch_size=BATCH_SIZE,
      show_progress_bar=True,
      convert_to_numpy=True
    )

    embedded_chunks = []
    for chunk, embedding in zip(chunks, embedidngs):
      embedded_chunks.append({
        "text": chunk["text"],
        "embedding": embedding.tolist(),
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

    print(f"\nCodeLens Embedder")
    print(f"{'='*40}")
    print(f"Chunks embedded:     {len(embedded_chunks)}")
    print(f"Embedding dimension: {len(embedded_chunks[0]['embedding'])}")
    print(f"Sample file:         {embedded_chunks[0]['metadata']['file_path']}")
    print(f"Sample lines:        {embedded_chunks[0]['metadata']['start_line']} to {embedded_chunks[0]['metadata']['end_line']}")
    print(f"\nFirst 5 embedding values:")
    print(embedded_chunks[0]['embedding'][:5])