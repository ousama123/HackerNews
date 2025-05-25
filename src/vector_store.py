import os

from langchain_community.vectorstores import Chroma

from src.embedder import get_embedding_model


def get_vector_db_path():
    """Get the absolute path to the vector database directory."""
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

    vector_db_path = os.path.join(project_root, "src", "data", "vector_db")
    return vector_db_path


def build_vector_store(chunks):
    """Create a new Chroma vector store."""
    embeddings = get_embedding_model()
    vector_db_path = get_vector_db_path()

    vectordb = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=vector_db_path)

    print(f"Built vector database with {len(chunks)} chunks")
    return vectordb


def add_new_chunks_to_vector_store(new_chunks):
    """Add new chunks to existing vector store with proper ID management."""
    if not new_chunks:
        print("No new chunks to add")
        return load_vector_store()  # Load the existing vector database
    vectordb = load_vector_store()

    # Get current count to determine starting ID for new chunks
    current_count = vectordb._collection.count()
    print(f"Vector database has {current_count} chunks")

    # Create IDs for new chunks starting from current count
    new_ids = [str(current_count + i) for i in range(len(new_chunks))]

    # Check that the first new ID doesn't exist yet
    first_new_id = new_ids[0]
    print(f"Validating ID {first_new_id}...")
    check_result = vectordb._collection.get(ids=[first_new_id])
    print(f"Found {len(check_result['documents'])} existing documents for ID {first_new_id}")
    # Add documents with specific IDs
    vectordb.add_documents(new_chunks, ids=new_ids)  # Check the addition worked
    new_count = vectordb._collection.count()
    print(f"Added {len(new_chunks)} chunks to database")
    print(f"Database now contains {new_count} total chunks")

    # Verify the first new document was added
    verify_result = vectordb._collection.get(ids=[first_new_id])
    print(f"Confirmed: ID {first_new_id} contains {len(verify_result['documents'])} documents")

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
    vector_db_path = get_vector_db_path()

    return Chroma(embedding_function=embeddings, persist_directory=vector_db_path)


def vector_store_exists():
    """Check if vector store exists."""
    vector_db_path = get_vector_db_path()
    return os.path.exists(vector_db_path) and os.listdir(vector_db_path)
