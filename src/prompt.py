from langchain.prompts import PromptTemplate

# TODO do some prompt engineering to improve results
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a HackerNews analyst. Answer the question concisely based on the provided context.

Guidelines:
- Keep answers short and focused
- Directly answer the question asked
- Only include the most relevant information
- Use bullet points for lists when appropriate
- If no relevant information is found, say so briefly

Context:
{context}

Question: {question}

Answer:""",
)
