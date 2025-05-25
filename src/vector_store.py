import os

from langchain_community.vectorstores import Chroma

from src.embedder import get_embedding_model


def build_vector_store(chunks):
    """Create a new Chroma vector store."""
    embeddings = get_embedding_model()

    vectordb = Chroma.from_documents(
        documents=chunks, embedding=embeddings, persist_directory="src/data/vector_db"
    )

    print(f"Built vector database with {len(chunks)} chunks")
    return vectordb


def add_new_chunks_to_vector_store(new_chunks):
    """Add new chunks to existing vector store."""
    if not new_chunks:
        print("No new chunks to add")
        return load_vector_store()

    vectordb = load_vector_store()
    vectordb.add_documents(new_chunks)
    print(f"Added {len(new_chunks)} new chunks to vector database")
    return vectordb


def get_chunks_from_new_documents(output_file, num_new_items):
    """Get chunks from documents."""
    from src.loader import load_document, split_documents

    docs = load_document(output_file)
    chunks = split_documents(docs)

    return chunks


def load_vector_store():
    """Load existing vector store."""
    embeddings = get_embedding_model()

    return Chroma(embedding_function=embeddings, persist_directory="src/data/vector_db")


def vector_store_exists():
    """Check if vector store exists."""
    vector_dir = "src/data/vector_db"
    return os.path.exists(vector_dir) and os.listdir(vector_dir)
