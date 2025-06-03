from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 800  # TODO: test different chunk sizes for optimal retrieval
CHUNK_OVERLAP = 80  # TODO: play with chunk overlap for better context


def load_document(path: str) -> list[Document]:
    """Load local text file as Document"""
    with open(path, encoding="utf-8") as f:
        return [Document(page_content=f.read(), metadata={"source": path})]


def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into chunks for embedding and retrieval"""
    # TODO: test different text splitters for HackerNews content
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len).split_documents(docs)
