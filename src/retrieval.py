from src.llm_config import llm, clean_label, vector_store


def retrieve_documents(question, k=3):
    return vector_store.similarity_search(question, k=k)


def evaluate_relevance(question, documents):
    """A second LLM checks if the retrieved chunks are useful."""

    if not documents:
        return "NOT_RELEVANT"

    context = "\n\n".join(
        document.page_content for document in documents
    )

    prompt = f"""
You are a relevance evaluator for a coding assistant.

User question:
{question}

Retrieved documents:
{context}

Is the retrieved context sufficiently relevant to answer the
user's request? Check the required behavior, not just similar words.

Return exactly one label:
RELEVANT
or
NOT_RELEVANT
"""

    response = llm.invoke(prompt)
    label = clean_label(response)

    if label == "RELEVANT":
        return "RELEVANT"

    return "NOT_RELEVANT"
