import streamlit as st

from src.rag import run_rag


def main():
    st.set_page_config(page_title="HackerNews RAG", page_icon="🔎")

    st.title("🔎 HackerNews RAG Search")

    st.write("Ask a question about HackerNews data:")

    with st.form("search_form"):
        query = st.text_input("Enter your query:")
        submit = st.form_submit_button("Search")
        if submit and query:
            with st.spinner("Searching..."):
                answer = run_rag(query)
            st.success(answer)


if __name__ == "__main__":
    main()
