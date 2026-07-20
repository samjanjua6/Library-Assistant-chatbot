import os
import json
import uuid
# pyrefly: ignore [missing-import]
import chromadb
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

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

def sliding_window_chunker(text: str, chunk_size: int, chunk_overlap: int):
    """Chunks text using a simple sliding window based on character count."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += (chunk_size - chunk_overlap)
    return chunks

def add_document_to_kb(filename: str, content: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """Chunks a document and adds it to ChromaDB."""
    chunks = sliding_window_chunker(content, chunk_size, chunk_overlap)
    if not chunks:
        return
        
    documents = []
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        doc_id = f"{filename}_{uuid.uuid4().hex[:8]}_chunk_{i}"
        documents.append(chunk)
        metadatas.append({"source": filename, "chunk_index": i})
        ids.append(doc_id)
        
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

def clear_knowledge_base():
    """Deletes all documents from the knowledge base collection."""
    existing = collection.get()
    if existing and existing['ids']:
        collection.delete(ids=existing['ids'])

