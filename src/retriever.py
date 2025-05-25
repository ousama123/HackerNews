import os

from dotenv import find_dotenv, load_dotenv

from src.loader import load_document, split_documents
from src.vector_store import build_vector_store, load_vector_store, vector_store_exists

load_dotenv(find_dotenv(), override=True)


def get_data_path():
    """Get the absolute path to the data file."""
    # Find the project root by looking for pyproject.toml
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)

    # Walk up the directory tree until we find pyproject.toml
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
            project_root = current_dir
            break
        current_dir = os.path.dirname(current_dir)
    else:
        # Fallback: assume we're in src/ and go up one level
        project_root = os.path.dirname(os.path.dirname(current_file))

    # Check if DATA_PATH is set in environment, otherwise use default
    env_data_path = os.getenv("DATA_PATH")
    if env_data_path and os.path.isabs(env_data_path):
        return env_data_path
    else:
        return os.path.join(project_root, "src", "data", "hackernews_optimized.txt")


DATA_PATH = get_data_path()


def get_retriever():
    """Get a retriever for the HackerNews data."""

    if vector_store_exists():
        print("Loading existing vector database...")
        vectordb = load_vector_store()
        print(f"Loaded {vectordb._collection.count()} chunks from database")
    else:
        print("No vector database found, building from scratch...")
        docs = load_document(DATA_PATH)
        chunks = split_documents(docs)
        vectordb = build_vector_store(chunks)
        print(f"Built new database with {len(chunks)} chunks")

    return vectordb.as_retriever()
