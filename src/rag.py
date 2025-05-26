"""RAG Engine for HackerNews Question Answering"""

from langchain.chains import RetrievalQA

from src.llm import get_llm
from src.prompt import prompt_template
from src.retriever import get_retriever


def run_rag(query: str) -> str:
    """Execute RAG pipeline for HackerNews QA"""
    qa_chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",  # Concatenate all retrieved docs into single prompt
        retriever=get_retriever(),
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template},
    )
    return qa_chain.invoke(query)["result"]
