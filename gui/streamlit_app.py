import streamlit as st

st.set_page_config(page_title="HackerNews RAG", page_icon="🔎")

st.title("🔎 HackerNews RAG Search")

st.write("Backend not implemented yet. Stay tuned!")

with st.form("search_form"):
    query = st.text_input("Enter your query:", disabled=True)
    submit = st.form_submit_button("Search")
    if submit:
        st.info("Backend not implemented yet.")
