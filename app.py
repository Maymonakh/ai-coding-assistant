import streamlit as st

from src.assistant import handle_request
from src.feedback import save_feedback
from src.code_runner import run_python_code
from src.llm_config import vector_store
from src.memory import (
    create_conversation, list_conversations, update_title, delete_conversation,
    save_message, load_messages,
    load_preferences, save_preferences, update_preferences,
)
from src.ui_helpers import display_execution_result, render_assistant_response


st.set_page_config(
    page_title="AI Coding Assistant",
    page_icon="💻",
    layout="wide"
)

st.title("💻 AI Coding Assistant")
st.write("Ask questions, generate code, and run Python solutions.")


GREETING = "Hi! I'm your AI Coding Assistant. How can I help you?"

# Text shown above each answer to explain which path was used
ROUTE_LABELS = {
    "explain": " Explain → LLM (no RAG)",
    "generate": " Generate → RAG → Relevance → LLM",
    "not_relevant": " Generate → RAG → Not Relevance → asking you for a solution"
}


def open_conversation(conversation_id):
    st.session_state.conversation_id = conversation_id
    st.session_state.messages = load_messages(conversation_id)
    st.session_state.pending_question = None
    st.session_state.feedback_status = None
    st.session_state.execution_results = {}
    st.session_state.manual_result = None


# Session state 

if "conversation_id" not in st.session_state:
    conversations = list_conversations()

    if conversations:
        first_id = conversations[0][0]          # the newest chat
    else:
        first_id = create_conversation()        # first time: make a chat

    st.session_state.preferences = load_preferences()
    open_conversation(first_id)

if "retry_question" not in st.session_state:
    st.session_state.retry_question = None      # question to ask again


with st.sidebar:
    st.header("Memory")
    st.write("Preferences:")
    st.json(st.session_state.preferences)

    if st.button("Reset preferences"):
        st.session_state.preferences = {}
        save_preferences({})
        st.rerun()

    st.header("Knowledge base")
    chunk_count = vector_store._collection.count()
    st.write(f"Stored chunks: {chunk_count}")

    if chunk_count == 0:
        st.warning("The database is empty. Run: python build_vector_db.py")

    st.header("Chats")

    if st.button("➕ New chat", use_container_width=True):
        if st.session_state.messages:           # don't make empty chats
            open_conversation(create_conversation())
        st.rerun()

    if st.button("🗑️ Delete this chat", use_container_width=True):
            delete_conversation(st.session_state.conversation_id)
            remaining = list_conversations()

            if remaining:
                open_conversation(remaining[0][0])
            else:
                open_conversation(create_conversation())
            st.rerun()

    for chat_id, title in list_conversations():
        is_current = chat_id == st.session_state.conversation_id

        if st.button(
            title,
            key=f"chat_{chat_id}",
            use_container_width=True,
            type="primary" if is_current else "secondary"
        ):
            open_conversation(chat_id)
            st.rerun()

   


# Show the conversation history
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(GREETING)

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            if message.get("route"):
                st.caption(ROUTE_LABELS[message["route"]])

            # Run buttons only for generated code (not for explanations)
            show_run = message.get("route") != "explain"
            render_assistant_response(
                message["content"],
                f"history_{st.session_state.conversation_id}_{index}",
                show_run
            )
        else:
            st.markdown(message["content"])


user_message = st.chat_input("Ask me to explain or generate code...")

if st.session_state.retry_question:
    user_message = st.session_state.retry_question
    st.session_state.retry_question = None

if user_message:
    chat_history = st.session_state.messages.copy() 

    st.session_state.messages.append({"role": "user", "content": user_message})

    with st.chat_message("user"):
        st.markdown(user_message)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response, route = handle_request(
                    user_message,
                    chat_history,
                    st.session_state.preferences,
                    stream=True
                )

            st.caption(ROUTE_LABELS[route])

            if isinstance(response, str):
                full_response = response
                st.markdown(full_response)
            else:
                full_response = st.write_stream(response)   # streaming

        except Exception as error:
            st.error("Something went wrong. Please try again.")
            print("Error:", error)
            st.session_state.messages.pop()      # remove the unanswered question
            st.stop()

    st.session_state.messages.append(
        {"role": "assistant", "content": full_response, "route": route}
    )

    chat_id = st.session_state.conversation_id
    save_message(chat_id, "user", user_message)
    save_message(chat_id, "assistant", full_response, route)

    # The first question becomes the title of the chat
    if len(st.session_state.messages) == 2:
        update_title(chat_id, " ".join(user_message.split())[:40])

    if route == "not_relevant":
        st.session_state.pending_question = user_message

    # Update the preferences
    st.session_state.preferences = update_preferences(
        user_message, st.session_state.preferences
    )
    save_preferences(st.session_state.preferences)

    st.rerun()  


# Manual Python code runner
st.divider()

with st.expander("Run Your Own Python Code"):
    manual_code = st.text_area(
        "Python code",
        value='print("Hello, world!")',
        height=180
    )

    if st.button("▶ Execute Code", key="manual_run"):
        with st.spinner("Running code..."):
            st.session_state.manual_result = run_python_code(manual_code)

    if st.session_state.manual_result is not None:
        display_execution_result(st.session_state.manual_result)


# Human feedback: the user gives a solution, we store it in Chroma
if st.session_state.pending_question:
    st.divider()
    st.subheader("Improve the Knowledge Base")
    st.write("I couldn't find relevant knowledge for this question:")
    st.info(st.session_state.pending_question)

    with st.form("feedback_form"):
        solution = st.text_area(
            "Your reference solution",
            placeholder="Paste a correct solution here (code + short explanation).",
            height=250
        )
        submitted = st.form_submit_button("Save Reference Solution")

    if submitted:
        if not solution.strip():
            st.warning("Please enter a solution first.")
        else:
            with st.spinner("Saving..."):
                result = save_feedback(st.session_state.pending_question, solution)

            if result["status"] in ("saved", "duplicate"):
                st.session_state.feedback_status = {
                    "status": result["status"],
                    "question": st.session_state.pending_question
                }
                st.session_state.pending_question = None
                st.rerun()
            else:
                st.error(result["message"])


if st.session_state.feedback_status:
    st.divider()
    status = st.session_state.feedback_status

    if status["status"] == "saved":
        st.success("Reference solution saved! I learned something new.")
    else:
        st.info("This solution already exists in the knowledge base.")

    if st.button("🔄 Try the Original Question Again"):
        st.session_state.retry_question = status["question"]
        st.session_state.feedback_status = None
        st.rerun()