from langchain.chains import RetrievalQA

from src.llm import get_llm
from src.prompt import prompt_template
from src.retriever import get_retriever


def run_rag(query: str) -> str:
    """
    Execute retrieval-augmented generation: retrieve context and generate an answer.
    """
    llm = get_llm()
    retriever = get_retriever()
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_template},
    )
    result = qa_chain.invoke(query)
    return result["result"]
