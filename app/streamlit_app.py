import streamlit as st
import sys
import os

# Ensure correct path resolution for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.rag import run_rag


def main():
    st.set_page_config(page_title="HackerNews RAG", page_icon="🔎")

    st.title("🔎 HackerNews RAG Search")
    
    # Add cache clear button for debugging
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.rerun()

    st.write("Ask a question about HackerNews data:")

    with st.form("search_form"):
        query = st.text_input("Enter your query:")
        submit = st.form_submit_button("Search")
        if submit and query:
            with st.spinner("Searching..."):
                # Debug information
                #st.write(f"🔍 Query: `{query}`")
                
                try:
                    answer = run_rag(query)
                    st.success(f"✅ Answer: {answer}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.exception(e)


if __name__ == "__main__":
    main()
