from src.llm_config import generate_response
from src.intent_classifier import classify_intent
from src.retrieval import retrieve_documents, evaluate_relevance
from src.memory import format_memory


NOT_FOUND_MESSAGE = (
    "I couldn't find relevant knowledge for your request.\n\n"
    "Could you provide the correct solution or a reference "
    "so I can learn it for future interactions?"
)


def handle_request(message, chat_history=None, preferences=None, stream=False):
    """Router: classify the request and send it to the right path.

    Returns (response, route).
    route is "explain", "generate" or "not_relevant".
    """

    memory_text = format_memory(chat_history or [], preferences or {})

    # Step 1: classify
    intent = classify_intent(message)

    # Path 1: EXPLAIN (no RAG)
    if intent == "EXPLAIN":
        prompt = f"""
You are a helpful Python programming assistant.

Conversation memory:
{memory_text}

User request:
{message}

Instructions:
- Analyze the code in the request and explain it clearly.
- Explain step by step when the user asks for it.
- Point out mistakes if there are any.
- Use Markdown formatting.
"""
        return generate_response(prompt, stream), "explain"

    # Path 2: GENERATE (RAG)
    # Step 2: retrieve from Chroma
    documents = retrieve_documents(message, k=3)

    # Step 3: relevance check
    relevance = evaluate_relevance(message, documents)

    if relevance != "RELEVANT":
        return NOT_FOUND_MESSAGE, "not_relevant"

    # Step 4: generate code using the retrieved context
    context = "\n\n".join(
        document.page_content for document in documents
    )

    prompt = f"""
You are an AI assistant specialized in Python programming.

Conversation memory:
{memory_text}

User request:
{message}

Relevant examples from the knowledge base:
{context}

Instructions:
- Solve EXACTLY what the user asked. The examples above are only references; if they solve a different problem, ignore them.
- Write a complete and runnable solution.
- Add comments, follow best practices and handle errors.
- At the end of the code, add a small example that calls your code and prints the result with print(), so running it shows an output. Skip this for web servers or programs that run forever.
- Follow the user's preferred language/framework if there is one.
- Put the code in ONE Markdown code block, then add a short explanation.
- Do not say the code was executed or tested.
"""
    return generate_response(prompt, stream), "generate"
