from loader import load_document, split_documents
from vector_store import build_vector_store


def get_retriever() -> object:
    """
    Load, split, embed, and return a retriever over the data file.
    """
    docs = load_document()
    chunks = split_documents(docs)
    vectordb = build_vector_store(chunks)
    return vectordb.as_retriever()
