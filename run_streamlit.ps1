# PowerShell script to always set PYTHONPATH and run Streamlit from project root
$env:PYTHONPATH = "."
poetry run streamlit run app/streamlit_app.py
