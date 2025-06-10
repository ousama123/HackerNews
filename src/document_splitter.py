from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

CHUNK_SIZE = 800  # TODO: test different chunk sizes for optimal retrieval
CHUNK_OVERLAP = 80  # TODO: play with chunk overlap for better context


def load_document(path: str) -> list[Document]:
    """Load HN export as one Document per item, carrying through its type, id & author."""
    text = open(path, encoding="utf-8").read()
    blocks = text.split("\n\n")  # each HN item (story/comment/user) is separated by a blank line

    docs = []
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue

        # parse the Metadata line to get the type
        # e.g. "Metadata: type=story, category=ask_hn"
        m = re.search(r"type=(\w+)", lines[0])
        item_type = m.group(1) if m else "unknown"

        # parse ID and author/username
        item_id = None
        author = None
        for L in lines:
            if L.startswith("Story ID:") or L.startswith("Comment ID:"):
                item_id = L.split(":",1)[1].strip()
            if L.startswith("Username:") or L.startswith("Author:"):
                author = L.split(":",1)[1].strip()

        # fall back if we didn’t find them
        item_id = item_id or "unknown"
        author  = author  or "unknown"

        docs.append(
            Document(
                page_content=block,
                metadata={
                    "source": path,
                    "item_type": item_type,
                    "item_id": item_id,
                    "author": author,
                },
            )
        )
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into chunks for embedding and retrieval"""
    # TODO: test different text splitters for HackerNews content
    return RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, length_function=len).split_documents(docs)
