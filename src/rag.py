"""RAG Engine for HackerNews Question Answering"""

import os
import time
from langchain.chains import RetrievalQA
from dotenv import find_dotenv, load_dotenv

from src.llm import get_llm
from src.prompt import prompt_template
from src.retriever import get_retriever

load_dotenv(find_dotenv())

def run_rag(query: str) -> str:
    """Execute RAG pipeline for HackerNews QA"""
    print(f"🔍 Processing query: {query[:50]}...")
    
    # Time the LLM generation
    start_time = time.time()
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        chain_type="stuff",  # Concatenate all retrieved docs into single prompt
        retriever=get_retriever(),
        return_source_documents=False,  # Don't return sources for faster processing
        chain_type_kwargs={"prompt": prompt_template},
    )
    
    result = qa_chain.invoke(query)["result"]
    
    # Show timing in a human-friendly way with model name
    elapsed_time = time.time() - start_time
    model_name = os.getenv("LLM_MODEL_NAME", "unknown")
    
    if elapsed_time < 1:
        time_str = f"{elapsed_time*1000:.0f}ms"
    else:
        time_str = f"{elapsed_time:.1f}s"
    
    print(f"⚡ Answer generated in {time_str} using {model_name}")
    
    return result
