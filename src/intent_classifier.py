from src.llm_config import llm, clean_label


def classify_intent(message):
    """Ask the LLM: does the user want an EXPLANATION or new CODE?"""

    prompt = f"""
Classify the user's request into one category.

EXPLAIN: the user wants to understand existing code.
Examples: "Explain this code", "What does this function do?",
"Why is this loop incorrect?", "Explain line by line".

GENERATE: the user wants new code to be written.
Examples: "Write Python code", "Generate a CNN model",
"Build a Flask API", "Create a sorting algorithm".

User request:
{message}

Return only one label:
EXPLAIN
or
GENERATE
"""

    response = llm.invoke(prompt)
    label = clean_label(response)

    if label.startswith("EXPLAIN"):
        return "EXPLAIN"

    return "GENERATE"
