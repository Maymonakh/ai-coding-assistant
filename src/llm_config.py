import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()

# Main folder of the project (so the database is found from anywhere)
BASE_DIR = Path(__file__).resolve().parent.parent


# The language model
llm = ChatOpenRouter(
    model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0
)


# The embedding model 
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)


# The Chroma vector database
vector_store = Chroma(
    collection_name="coding_knowledge",
    persist_directory=str(BASE_DIR / "chroma_db"),
    embedding_function=embeddings
)


# Chunking
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=150
)


def clean_label(response):
    result = response.content.strip().upper()
    result = result.replace("`", "").replace("*", "")

    lines = result.splitlines()
    if not lines:
        return ""

    return lines[0].strip().rstrip(" .:")


def generate_response(prompt, stream=False):
    if stream:
        return (
            chunk.content
            for chunk in llm.stream(prompt)
            if isinstance(chunk.content, str) and chunk.content
        )

    response = llm.invoke(prompt)
    return response.content
