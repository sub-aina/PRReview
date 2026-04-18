import os
import chromadb
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils import embedding_functions

# File types we care about indexing
SUPPORTED_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".go", ".rb",
    ".html", ".css", ".md"
]

# Folders we want to skip
IGNORED_DIRS = [
    "venv", "node_modules", ".git", "__pycache__",
    ".pytest_cache", "dist", "build"
]

def get_all_files(repo_path: str) -> list[str]:
    """Walk the repo and return all supported file paths."""
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        # Remove ignored directories so os.walk skips them
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for filename in filenames:
            if any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                files.append(os.path.join(root, filename))
    return files

def index_repository(repo_path: str, collection_name: str = "codebase"):
    """Read all files in repo, chunk them, store in ChromaDB."""
    print(f" Indexing repository: {repo_path}")

    # 1. Connect to ChromaDB (runs locally, stores in ./chroma_db folder)
    client = chromadb.PersistentClient(path="./chroma_db")

    # 2. Use a free local embedding model
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # 3. Create or get the collection (like a table in a database)
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    # 4. Get all files
    files = get_all_files(repo_path)
    print(f" Found {len(files)} files to index")

    # 5. Split files into chunks and store
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    documents = []
    metadatas = []
    ids = []
    chunk_id = 0

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                continue

            chunks = splitter.split_text(content)

            for chunk in chunks:
                documents.append(chunk)
                metadatas.append({"filepath": filepath})
                ids.append(f"chunk_{chunk_id}")
                chunk_id += 1

        except Exception as e:
            print(f" Skipping {filepath}: {e}")

    # 6. Store everything in ChromaDB
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f" Indexed {len(documents)} chunks from {len(files)} files")
    else:
        print("  No documents found to index")

    return collection

def search_codebase(query: str, n_results: int = 5, collection_name: str = "codebase") -> list[dict]:
    """Search ChromaDB for code related to the query."""
    client = chromadb.PersistentClient(path="./chroma_db")

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    # Format results nicely
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "content": doc,
            "filepath": results["metadatas"][0][i]["filepath"]
        })

    return output