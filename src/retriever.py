import os

from dotenv import find_dotenv, load_dotenv

from src.loader import load_document, split_documents
from src.vector_store import build_vector_store, load_vector_store, vector_store_exists

load_dotenv(find_dotenv(), override=True)
DATA_PATH = os.getenv("DATA_PATH", "src/data/hackernews_optimized.txt")


def get_retriever():
    """Get a retriever for the HackerNews data."""

    # Check if vector store needs rebuilding
    if vector_store_exists():
        vector_dir = "src/data/vector_db"

        if os.path.exists(DATA_PATH):
            data_modified = os.path.getmtime(DATA_PATH)
            vector_modified = os.path.getmtime(vector_dir)

            if data_modified > vector_modified:
                print("Data file is newer than vector store - rebuilding...")
                docs = load_document(DATA_PATH)
                chunks = split_documents(docs)
                vectordb = build_vector_store(chunks)
            else:
                print("Loading existing vector database...")
                vectordb = load_vector_store()
        else:
            print("No data file found - loading existing vector database...")
            vectordb = load_vector_store()
    else:
        print("Building new vector database...")
        docs = load_document(DATA_PATH)
        chunks = split_documents(docs)
        vectordb = build_vector_store(chunks)

    return vectordb.as_retriever()
