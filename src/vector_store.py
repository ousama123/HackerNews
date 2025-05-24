from langchain_community.vectorstores import Chroma

from src.embedder import get_embedding_model


def build_vector_store(chunks: list) -> Chroma:
    """
    Create a Chroma vector store from document chunks using open-source embeddings.
    """
    embed_model = get_embedding_model()
    return Chroma.from_documents(chunks, embed_model)
