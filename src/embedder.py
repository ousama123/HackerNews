import os

from dotenv import find_dotenv, load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv(find_dotenv())

# TODO test some other OS embedders
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME")


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Initialize open-source sentence-transformer embedding model.
    """
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL_NAME)
