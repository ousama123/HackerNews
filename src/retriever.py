"""
HackerNews Document Retriever

Provides intelligent document retrieval capabilities for HackerNews RAG system.
Handles vector database management and optimized search configurations.

Features: Auto database detection, simple path resolution, optimized retrieval

Data Flow:
1. Locate HackerNews data file using fixed relative path structure
2. Check for existing vector database or build new one from processed documents
3. Create retriever instance with optimized search parameters for user queries
"""

import os

from dotenv import find_dotenv, load_dotenv

from src.loader import load_document, split_documents
from src.vector_store import build_vector_store, load_vector_store, vector_store_exists

# Load environment variables from .env file if available
load_dotenv(find_dotenv(), override=True)


# Simple path resolution: data file is always in src/data/ relative to this file
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "hackernews_optimized.txt")

# Simple edge case: verify data file exists
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"HackerNews data file not found at: {DATA_PATH}")


def get_retriever():
    """
    Create optimized retriever for HackerNews knowledge base.

    Returns:
        VectorStoreRetriever: Configured retriever with k=6 search results
    """
    # Smart database loading: use existing vector store if available
    if vector_store_exists():
        print("Loading existing vector database...")
        vectordb = load_vector_store()
        # Report database size for debugging and monitoring
        print(f"Loaded {vectordb._collection.count()} chunks from database")
    else:
        # Fallback: build new vector database from processed documents
        print("No vector database found, building from scratch...")
        docs = load_document(DATA_PATH)
        chunks = split_documents(docs)  # Split documents into searchable chunks
        vectordb = build_vector_store(chunks)
        print(f"Built new database with {len(chunks)} chunks")

    # Return retriever with optimized k=6 for HackerNews content diversity
    return vectordb.as_retriever(search_kwargs={"k": 6})
