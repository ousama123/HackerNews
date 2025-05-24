import os

from dotenv import find_dotenv, load_dotenv
from langchain_community.llms import HuggingFaceHub

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Example: meta-llama/Llama-2-7b-chat-hf or mistralai/Mistral-7B-Instruct-v0.2
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
HUGGINGFACE_MODEL_NAME = os.getenv("HUGGINGFACE_MODEL_NAME")

if not HUGGINGFACEHUB_API_TOKEN or not HUGGINGFACE_MODEL_NAME:
    raise ValueError(
        "HUGGINGFACEHUB_API_TOKEN and HUGGINGFACE_MODEL_NAME must be set in the environment variables."
    )


def get_llm() -> HuggingFaceHub:
    """
    Initialize and return a HuggingFaceHub LLM client for open-source models.
    """
    return HuggingFaceHub(
        repo_id=HUGGINGFACE_MODEL_NAME,
        huggingfacehub_api_token=HUGGINGFACEHUB_API_TOKEN,
        model_kwargs={
            "temperature": 0.7,
            "max_new_tokens": 256,
        },
    )
