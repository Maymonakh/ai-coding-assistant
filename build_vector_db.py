#python build_vector_db.py

from pathlib import Path

from datasets import load_dataset
from langchain_core.documents import Document

from src.llm_config import vector_store, text_splitter


documents = []
ids = []


def add_text(text, base_id, metadata):
    
    chunks = text_splitter.split_text(text)

    for number, chunk in enumerate(chunks):
        chunk_metadata = dict(metadata)
        chunk_metadata["chunk"] = number

        documents.append(Document(page_content=chunk, metadata=chunk_metadata))
        ids.append(f"{base_id}_{number}")


# Part 1: HumanEval dataset (164 Python problems with solutions)
dataset = load_dataset("openai/openai_humaneval", split="test")

for item in dataset:
    text = f"""Problem:
{item['prompt']}

Reference Solution:
{item['canonical_solution']}"""

    add_text(
        text,
        item["task_id"],
        {
            "task_id": item["task_id"],
            "entry_point": item["entry_point"],
            "source": "openai_humaneval"
        }
    )

# Part 2: our own examples (Flask, sorting, CNN ...) from extra_knowledge/
for file in sorted(Path("extra_knowledge").glob("*.md")):
    add_text(
        file.read_text(encoding="utf-8"),
        file.stem,
        {"source": file.name}
    )

# Embeddings are created automatically when we add the documents
vector_store.add_documents(documents=documents, ids=ids)

print("Vector database created successfully!")
print("Number of chunks:", vector_store._collection.count())
