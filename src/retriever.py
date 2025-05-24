import os

from dotenv import find_dotenv, load_dotenv

from src.loader import load_document, split_documents
from src.vector_store import build_vector_store

# Load environment variables (force override existing env vars)
load_dotenv(find_dotenv(), override=True)

# Get data path from environment variables
DATA_PATH = os.getenv("DATA_PATH", "src/data/topstories_simple.txt")


def get_retriever() -> object:
    """
    Load, split, embed, and return a retriever over the data file.
    """
    docs = load_document(DATA_PATH)
    chunks = split_documents(docs)
    vectordb = build_vector_store(chunks)
    return vectordb.as_retriever()
