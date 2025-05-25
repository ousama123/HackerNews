"""
HackerNews Vector Store Management

Manages Chroma vector database for HackerNews RAG system.
Handles creation, updates, loading, and path resolution.

Features: Document vectorization, incremental updates, database validation

Flow: Build initial store → Add incremental chunks → Load for retrieval → Validate existence
"""

import os

from langchain_community.vectorstores import Chroma

from src.embedder import get_embedding_model
from src.loader import load_document, split_documents


def get_vector_db_path():
    """
    Get the absolute path to the vector database directory.

    Returns:
        str: Absolute path to the vector_db directory
    """
    # Simple path resolution: vector_db is always in src/data/ relative to this file
    vector_db_path = os.path.join(os.path.dirname(__file__), "data", "vector_db")

    # Simple edge case: ensure data directory exists (vector_db will be created as needed)
    data_dir = os.path.dirname(vector_db_path)
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory not found at: {data_dir}")

    return vector_db_path


def build_vector_store(chunks):
    """
    Create a new Chroma vector store from document chunks.

    Args:
        chunks (list): List of LangChain Document objects to vectorize

    Returns:
        Chroma: Initialized vector database with embedded documents
    """
    # Get embedding model for vector generation
    embeddings = get_embedding_model()
    vector_db_path = get_vector_db_path()

    # Create new Chroma database with documents and embeddings
    vectordb = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=vector_db_path)

    print(f"Built vector database with {len(chunks)} chunks")
    return vectordb


def add_new_chunks_to_vector_store(new_chunks):
    """
    Add new chunks to existing vector store with proper ID management.

    Args:
        new_chunks (list): List of new Document objects to add

    Returns:
        Chroma: Updated vector database with new chunks added
    """
    if not new_chunks:
        print("No new chunks to add")
        return load_vector_store()  # Load the existing vector database

    # Load existing vector database
    vectordb = load_vector_store()

    # Get current count to determine starting ID for new chunks
    current_count = vectordb._collection.count()
    print(f"Vector database has {current_count} chunks")

    # Create sequential IDs for new chunks starting from current count
    new_ids = [str(current_count + i) for i in range(len(new_chunks))]

    # Add documents with specific IDs to prevent conflicts
    vectordb.add_documents(new_chunks, ids=new_ids)

    return vectordb


def get_chunks_from_new_documents(output_file, num_new_items):
    """
    Get document chunks from a processed file (legacy utility function).

    Args:
        output_file (str): Path to the processed document file
        num_new_items (int): Number of new items (not currently used)

    Returns:
        list: Document chunks ready for vector store insertion
    """

    # Load and split documents from the output file
    docs = load_document(output_file)
    chunks = split_documents(docs)

    return chunks


def load_vector_store():
    """
    Load existing Chroma vector store from disk.

    Returns:
        Chroma: Loaded vector database ready for queries
    """
    # Get embedding model matching the one used during creation
    embeddings = get_embedding_model()
    vector_db_path = get_vector_db_path()

    # Initialize Chroma with existing database directory
    return Chroma(embedding_function=embeddings, persist_directory=vector_db_path)


def vector_store_exists():
    """
    Check if vector store database exists and contains data.

    Returns:
        bool: True if database directory exists and is not empty
    """
    vector_db_path = get_vector_db_path()
    # Check both existence and non-empty status
    return os.path.exists(vector_db_path) and os.listdir(vector_db_path)
