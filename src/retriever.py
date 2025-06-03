"""HackerNews Document Retriever"""

import os

from dotenv import find_dotenv, load_dotenv

from src.document_splitter import load_document, split_documents
from src.vector_store import build_vector_store, load_vector_store, vector_store_exists

load_dotenv(find_dotenv(), override=True)

# Simple path resolution: data file is always in src/data/ relative to this file
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "hackernews_optimized.txt")


def get_retriever():
    """Create optimized retriever for HackerNews knowledge base"""
    # Check if data file exists when function is called, not at import time
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"HackerNews data file not found at: {DATA_PATH}")

    # Smart database loading: use existing vector store if available
    if vector_store_exists():
        print("Loading existing vector database...")
        vectordb = load_vector_store()
        print(f"Loaded {vectordb._collection.count()} chunks from database")
    else:
        print("No vector database found, building from scratch...")
        chunks = split_documents(load_document(DATA_PATH))
        vectordb = build_vector_store(chunks)
        print(f"Built new database with {len(chunks)} chunks")

    # Return retriever with optimized k=6 for HackerNews content diversity
    return vectordb.as_retriever(search_kwargs={"k": 6})
