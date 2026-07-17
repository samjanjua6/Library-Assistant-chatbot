import os
import json
# pyrefly: ignore [missing-import]
import chromadb
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

# Get or create the collection (this uses the default all-MiniLM-L6-v2 embedding model)
collection = chroma_client.get_or_create_collection(name="library_knowledge_base")

def ingest_documents():
    """Reads all text files in knowledge_base directory and adds them to ChromaDB."""
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"Directory not found: {KNOWLEDGE_BASE_DIR}")
        return

    documents = []
    metadatas = []
    ids = []
    
    # We will just split files into paragraphs for simple chunking
    doc_id_counter = 0
    for file_path in KNOWLEDGE_BASE_DIR.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 10]
        
        for i, paragraph in enumerate(paragraphs):
            doc_id = f"{file_path.stem}_para_{i}"
            documents.append(paragraph)
            metadatas.append({"source": file_path.name, "chunk_index": i})
            ids.append(doc_id)
            doc_id_counter += 1

    if documents:
        # Add to Chroma DB (this automatically handles embeddings!)
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully ingested {len(documents)} chunks from {len(list(KNOWLEDGE_BASE_DIR.glob('*.txt')))} files into ChromaDB.")
    else:
        print("No documents found to ingest.")


def search_knowledge_base(query: str, n_results: int = 3) -> str:
    """
    Search the library knowledge base for the given query.
    Returns a JSON string containing the most relevant text passages.
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format the output for the AI
        passages = []
        if results and results["documents"]:
            for i, doc_text in enumerate(results["documents"][0]):
                source = results["metadatas"][0][i].get("source", "Unknown")
                distance = results["distances"][0][i]
                
                # Only include relevant matches (Chroma uses L2 distance by default, lower is better. usually < 1.5 is okay)
                if distance < 1.5:
                    passages.append({
                        "source": source,
                        "text": doc_text
                    })
        
        if passages:
            return json.dumps({
                "status": "success",
                "results": passages
            })
        else:
            return json.dumps({
                "status": "not_found",
                "message": "No relevant information found in the knowledge base."
            })
            
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    # Test ingestion when run directly
    ingest_documents()
