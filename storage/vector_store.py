import chromadb
from chromadb.config import Settings
import os

COLLECTION_NAME = "wraith_chunks"
PERSIST_DIR = "data/chromadb"

# improvement - here the space is just one and evrything gets stored there. seperate it for different codebases

class VectorStore:

    _instance = {}

    def __new__(cls, codebase_path:str):
        collection_name = os.path.basename(codebase_path)
        if collection_name not in cls._instance:
            cls._instance[collection_name] = super().__new__(cls)
        return cls._instance[collection_name]

    def __init__(self, codebase_path: str):

        if hasattr(self, 'collection'):
            return
        collection_name = os.path.basename(codebase_path)
        self.client = chromadb.PersistentClient(
            path=PERSIST_DIR
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Vector store ready. Collection: {collection_name}")

    def add_chunks(self, embedded_chunks: list[dict]) -> None:
        print(f"\nStoring {len(embedded_chunks)} chunks in vector store...")

        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(embedded_chunks):
            ids.append(f"chunk_{i}")
            embeddings.append(chunk["embedding"])
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Successfully stored {len(embedded_chunks)} chunks")

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]
            })

        return matches

    def get_collection_count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print("Vector store cleared")

if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.file_parser import get_all_files, read_file
    from ingestion.chunker import chunk_codebase
    from ingestion.embedder import CodeEmbedder

    path = sys.argv[1] if len(sys.argv) > 1 else "."

    print("=== wraith Phase 1 - Full Pipeline Test ===\n")

    print("Step 1: Scanning files...")
    files = get_all_files(path)
    print(f"Found {len(files)} files")

    print("\nStep 2: Reading and chunking...")
    contents = [read_file(f) for f in files]
    chunks = chunk_codebase(files, contents)
    print(f"Created {len(chunks)} chunks")

    print("\nStep 3: Embedding chunks...")
    embedder = CodeEmbedder()
    embedded_chunks = embedder.embed_chunks(chunks)

    print("\nStep 4: Storing in vector database...")
    store = VectorStore()
    store.add_chunks(embedded_chunks)
    print(f"Total chunks in DB: {store.get_collection_count()}")

    print("\nStep 5: Running your first semantic search...")
    query = "how is face recognition done"
    print(f"Query: '{query}'")

    query_embedding = embedder.embed_text(query)
    results = store.search(query_embedding, n_results=3)

    print(f"\n{'='*50}")
    print(f"Top 3 results:")
    print(f"{'='*50}")

    for i, result in enumerate(results):
        print(f"\nResult {i+1}")
        print(f"File:  {result['metadata']['file_path']}")
        print(f"Lines: {result['metadata']['start_line']} to {result['metadata']['end_line']}")
        print(f"Score: {result['score']:.3f}")
        print(f"{'-'*40}")
        print(result['text'][:300])
        print("...")