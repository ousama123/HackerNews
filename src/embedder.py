import os

from dotenv import find_dotenv, load_dotenv
from langchain_ollama import OllamaEmbeddings

# Load environment variables from .env file
load_dotenv(find_dotenv())

# TODO test some other OS embedders
OLLAMA_EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "nomic-embed-text")


def get_embedding_model():
    """
    Initialize and return an OllamaEmbeddings client for local Ollama embedding models.
    """
    return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL_NAME)
