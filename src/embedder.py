import os

from dotenv import find_dotenv, load_dotenv
from langchain_ollama import OllamaEmbeddings

load_dotenv(find_dotenv())
# TODO: test other OS embedders like all-minilm, sentence-transformers
OLLAMA_EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "nomic-embed-text")


def get_embedding_model():
    """Initialize OllamaEmbeddings client for local embedding models"""
    return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL_NAME)
