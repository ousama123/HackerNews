import os

from dotenv import find_dotenv, load_dotenv
from langchain_ollama import OllamaLLM

load_dotenv(find_dotenv())
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")  # TODO: test other models like llama, mistral
print("Loading Ollama model:", LLM_MODEL_NAME)


def get_llm():
    """Initialize OllamaLLM client with optimized parameters"""
    return OllamaLLM(
        model=LLM_MODEL_NAME,
        temperature=0.7,
        max_tokens=500, # Increased for more complex queries
        stop=["###", "```"],  # Stop tokens prevent code block issues
    )
