# HackerNews RAG Search 🔎

Ask questions about HackerNews content using AI. Fetches real HN data and runs everything locally - no API keys needed!

## Quick Start

1. **Install Ollama** (local AI): Download from [ollama.com](https://ollama.com)
   LLM model: 
   ```bash
   ollama pull llama3.2
   ```
   Embedding model:
   ```bash
   ollama pull nomic-embed-text
   ```
   After pulling the models, run 
   ```bash 
   ollama list
   ``` 
   This should list both models

2. **Setup Project**
   ```bash
   git clone https://github.com/ousama123/HackerNews.git
   cd HackerNews
   pip install poetry
   poetry install
   OBS: You need python installed before running poetry install
   ```

3. **Get Data & Start**
   ```bash
   poetry run python src/pipeline/run_pipeline.py  # Fetch HN data
   poetry run streamlit run app/streamlit_app.py   # Start web app
   ```

4. **Use**: Open `http://localhost:8501` and ask questions like:
   - "What are people saying about AI?"
   - "Any Python discussions?"
   - "Show me startup debates"

## Requirements
- Python 3.9+
- 4GB RAM minimum
- Internet connection (for setup & fetching data)

## Getting Fresh Data
```bash
# Fetch new HackerNews content
poetry run python src/pipeline/run_pipeline.py
```
The system automatically tracks what it has already processed, so you can run this anytime to get new content.


## Troubleshooting

- **Ollama errors**: Make sure Ollama is running and try `ollama list`
- **"No module" errors**: Use `poetry run` before Python commands
- **Slow responses**: Normal on CPU (10-30s), try smaller model: `ollama pull llama3.2:1b`
- **No data**: Run pipeline first: `poetry run python src/pipeline/run_pipeline.py`


## Tech Stack
- **AI**: Ollama (Llama 3.2) + Sentence Transformers
- **Database**: FAISS for vector search
- **Framework**: LangChain + Streamlit
- **Data**: HackerNews API
