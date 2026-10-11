import os, dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

dotenv.load_dotenv()

class VectorStore:

    _instance = {}

    def __new__(cls, codebase_path:str):
        collection_name = os.path.basename(codebase_path)
        if collection_name not in cls._instance:
            cls._instance[collection_name] = super().__new__(cls)
        return cls._instance[collection_name]

    def __init__(self, codebase_path: str):

        if hasattr(self, 'client'):
            return
        self.collection_name = os.path.basename(os.path.abspath(codebase_path))
        self.client = QdrantClient(
            url = os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        print(f"Vector store ready. Collection: {self.collection_name}")

    def add_chunks(self, embedded_chunks: list[dict]) -> None:
        print(f"\nStoring {len(embedded_chunks)} chunks in vector store...")


        points = []

        for i, chunk in enumerate(embedded_chunks):
            points.append(PointStruct(
                id=i,
                vector=chunk["embedding"],
                payload={"text": chunk["text"], "metadata": chunk["metadata"]}
            ))
        for i in range(0, len(points), 50):
            batch = points[i:i+50]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
        print(f"Successfully stored {len(embedded_chunks)} chunks")

    def search(self, query_embedding: list[float], n_results: int = 5) -> list[dict]:
        results = self.client.query_points(collection_name=self.collection_name,query=query_embedding,limit=n_results)

        matches = []
        for result in results.points:
            matches.append({
                "text": result.payload["text"],
                "metadata": result.payload["metadata"],
                "score": result.score
            })

        return matches

    def get_collection_count(self) -> int:
        return self.client.count(self.collection_name).count

    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=1536,distance=Distance.COSINE)
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
    store = VectorStore(path)
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