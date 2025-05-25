"""
RAG Engine for HackerNews Question Answering

Orchestrates retrieval-augmented generation pipeline combining vector search
with LLM inference for HackerNews content queries.

Features: Semantic retrieval, custom prompts, source tracking

"""

from langchain.chains import RetrievalQA

from src.llm import get_llm
from src.prompt import prompt_template
from src.retriever import get_retriever


def run_rag(query: str) -> str:
    """
    Execute complete RAG pipeline for HackerNews question answering.

    Args:
        query (str): User question about HackerNews content

    Returns:
        str: Generated answer based on retrieved context
    """
    # Initialize core RAG components
    llm = get_llm()  # Load configured language model
    retriever = get_retriever()  # Get HackerNews vector database retriever

    # Build RetrievalQA chain with "stuff" strategy for context injection
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",  # Concatenate all retrieved docs into single prompt
        retriever=retriever,
        return_source_documents=True,  # Include source docs in response metadata
        chain_type_kwargs={"prompt": prompt_template},  # Custom HackerNews prompt
    )

    # Execute RAG pipeline: retrieve → contextualize → generate
    result = qa_chain.invoke(query)
    return result["result"]  # Extract final answer from response dict
