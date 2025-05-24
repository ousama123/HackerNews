# PowerShell script to always set PYTHONPATH and run Streamlit from project root
$env:PYTHONPATH = "."
poetry run streamlit run gui/streamlit_app.py
