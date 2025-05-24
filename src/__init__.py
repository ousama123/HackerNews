"""
HackerNews RAG System

A retrieval-augmented generation system for HackerNews content using Ollama.
"""

__version__ = "0.1.0"

# Main entry points
from .llm import get_llm
from .rag import run_rag
from .retriever import get_retriever

__all__ = [
    "run_rag",
    "get_retriever",
    "get_llm",
]
