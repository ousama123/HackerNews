import os

from dotenv import find_dotenv, load_dotenv
from langchain_ollama import OllamaLLM

# Load environment variables from .env file
load_dotenv(find_dotenv())

# TODO test some other models
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
print("Loading Ollama model:", LLM_MODEL_NAME)


def get_llm():
    """
    Initialize and return an OllamaLLM client for local Ollama models.
    """
    return OllamaLLM(
        model=LLM_MODEL_NAME,
        temperature=0.1,
        max_tokens=1024,
        top_p=0.95,
        top_k=40,
        stop=["###", "```"],
    )
