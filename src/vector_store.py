"""HackerNews Vector Store Management"""

import os

from langchain_community.vectorstores import Chroma

from src.embedder import get_embedding_model
from src.loader import load_document, split_documents


def get_vector_db_path():
    """Get vector database path"""
    vector_db_path = os.path.join(os.path.dirname(__file__), "data", "vector_db")
    if not os.path.exists(data_dir := os.path.dirname(vector_db_path)):
        raise FileNotFoundError(f"Data directory not found at: {data_dir}")
    return vector_db_path


def build_vector_store(chunks):
    """Create new Chroma vector store from chunks"""
    vectordb = Chroma.from_documents(documents=chunks, embedding=get_embedding_model(), persist_directory=get_vector_db_path())
    print(f"Built vector database with {len(chunks)} chunks")
    return vectordb


def add_new_chunks_to_vector_store(new_chunks):
    """Add new chunks to existing vector store with proper ID management"""
    if not new_chunks:
        print("No new chunks to add")
        return load_vector_store()

    vectordb = load_vector_store()
    current_count = vectordb._collection.count()  # Get current count to prevent ID conflicts
    print(f"Vector database has {current_count} chunks")
    # Create sequential IDs starting from current count to avoid conflicts
    vectordb.add_documents(new_chunks, ids=[str(current_count + i) for i in range(len(new_chunks))])
    return vectordb


def get_chunks_from_new_documents(output_file, num_new_items):
    """Get document chunks from processed file (legacy utility function)"""
    return split_documents(load_document(output_file))


def load_vector_store():
    """Load existing Chroma vector store"""
    return Chroma(embedding_function=get_embedding_model(), persist_directory=get_vector_db_path())


def vector_store_exists():
    """Check if vector store exists and contains data"""
    return (path := get_vector_db_path()) and os.path.exists(path) and os.listdir(path)
