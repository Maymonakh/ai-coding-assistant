import hashlib
from datetime import datetime

from langchain_core.documents import Document
from src.llm_config import vector_store, text_splitter


def save_feedback(question, solution):
    """Save a solution given by the user into Chroma (learning)."""

    question = question.strip()
    solution = solution.strip()

    if not question or not solution:
        return {
            "status": "invalid",
            "message": "The question and solution cannot be empty."
        }

    # Make an ID from the text, so the same solution is not saved twice
    text = f"{question}\n{solution}"
    short_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]
    base_id = f"user_feedback_{short_hash}"

    if vector_store.get(ids=[base_id + "_0"])["ids"]:
        return {
            "status": "duplicate",
            "message": "This feedback is already stored."
        }

    # Step 1: build the document text
    full_text = f"Problem:\n{question}\n\nReference Solution:\n{solution}"

    # Step 2: chunking
    chunks = text_splitter.split_text(full_text)

    # Step 3: metadata + ids
    documents = []
    ids = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for number, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "source": "user_feedback",
                    "added_at": now,
                    "chunk": number
                }
            )
        )
        ids.append(f"{base_id}_{number}")

    # Step 4: embeddings are created automatically and saved in Chroma
    vector_store.add_documents(documents=documents, ids=ids)

    return {
        "status": "saved",
        "message": "User feedback stored successfully!"
    }
