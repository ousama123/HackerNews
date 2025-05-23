from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 50


# TODO test different loader later
def load_document(path: str) -> list[Document]:
    """
    Load a local text file and wrap its contents in a Document.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return [Document(page_content=text, metadata={"source": path})]


# TODO test different textsplitter
# TODO play with chunk size and chunk overlap
def split_documents(docs: list[Document]) -> list[Document]:
    """
    Split documents into chunks for embedding and retrieval.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return splitter.split_documents(docs)
