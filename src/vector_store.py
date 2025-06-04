import os
import pickle

from langchain_community.vectorstores import FAISS

from src.embedder import get_embedding_model


def get_vector_db_path():
    """Get vector database path"""
    vector_db_path = os.path.join(os.path.dirname(__file__), "data", "vector_db")
    if not os.path.exists(data_dir := os.path.dirname(vector_db_path)):
        raise FileNotFoundError(f"Data directory not found at: {data_dir}")
    return vector_db_path


def build_vector_store(chunks):
    """Create new FAISS vector store from chunks"""
    vectordb = FAISS.from_documents(documents=chunks, embedding=get_embedding_model())
    vectordb.save_local(get_vector_db_path())
    print(f"Built vector database with {len(chunks)} chunks")
    return vectordb


def add_new_chunks_to_vector_store(new_chunks):
    """Add new chunks to existing vector store with proper ID management"""
    if not new_chunks:
        print("No new chunks to add")
        return load_vector_store()

    vectordb = load_vector_store()
    print("before count...")
    current_count = vectordb.index.ntotal
    print("after count...")
    print(f"Vector database has {current_count} chunks")
    # Create sequential IDs starting from current count to avoid conflicts
    vectordb.add_documents(new_chunks, ids=[str(current_count + i) for i in range(len(new_chunks))])
    return vectordb


def load_vector_store():
    """Load existing FAISS vector store"""
    return FAISS.load_local(get_vector_db_path(), get_embedding_model(), allow_dangerous_deserialization=True)


def vector_store_exists():
    """Check if vector store exists and contains data"""
    path = get_vector_db_path()
    return os.path.exists(path) and any(f.endswith('.faiss') or f.endswith('.pkl') for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)))