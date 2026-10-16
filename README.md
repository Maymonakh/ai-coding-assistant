# AI Coding Assistant (Cellula AI Engineering Internship - Task4)

An AI assistant that explains code, generates code, remembers the conversation,
learns from the user, and runs Python code safely.

## How it works

```
User message
    |
Intent classifier (LLM)
    |-- EXPLAIN  -> LLM -> answer                      (no RAG)
    |-- GENERATE -> search Chroma -> relevance check (LLM)
                        |-- relevant     -> LLM writes code -> [Run] button -> Docker
                        |-- not relevant -> ask the user for a solution
                                            -> embeddings -> save in Chroma
```

## Project structure

```
ai-coding-assistant/
├── app.py                  # Streamlit user interface
├── build_vector_db.py      # fills Chroma (run once)
├── requirements.txt
├── .env.example            # copy to .env and add your key
├── extra_knowledge/        # our own examples (Flask, sorting, CNN)
└── src/
    ├── assistant.py          # router: sends the request to the right path
    ├── intent_classifier.py  # EXPLAIN or GENERATE
    ├── retrieval.py          # search Chroma + relevance check
    ├── feedback.py           # learn from the user's solution
    ├── memory.py             # SQLite: chats, messages, preferences
    ├── code_runner.py        # runs code inside Docker
    ├── ui_helpers.py         # code blocks + Run buttons
    └── llm_config.py         # LLM, embeddings, Chroma, chunking
```

## How to run

1. `pip install -r requirements.txt`
2. Put your OpenRouter key inside `.env`.
3. Install Docker Desktop, start it, then run `docker pull python:3.12-alpine`.
4. `python build_vector_db.py`
5. `streamlit run app.py`

## Try these

1. "Explain this code: ..." -> the caption shows no RAG.
2. "Build a Flask API" -> RAG finds an example -> code + Run button.
3. "Write a Rust web scraper" -> not relevant -> paste a solution -> saved -> ask again.
4. "I prefer Django" -> check the Memory panel in the sidebar.