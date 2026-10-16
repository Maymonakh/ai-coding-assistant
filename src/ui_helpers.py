import re

import streamlit as st

from src.code_runner import run_python_code


def display_execution_result(result):
    """Show the output of the code runner."""
    if result["success"]:
        st.success("Code executed successfully!")
    else:
        st.error("Code execution failed.")

    if result["output"]:
        st.code(result["output"], language="text")


def render_assistant_response(content, message_id, show_run=True):
    """Show text and code blocks separately, with a Run button for Python."""

    # This pattern finds ```language ... ``` blocks
    pattern = re.compile(r"```([A-Za-z0-9_+#.-]*)[ \t]*\n(.*?)```", re.DOTALL)

    last_position = 0
    code_number = 0

    for match in pattern.finditer(content):
        text_before = content[last_position:match.start()]

        if text_before.strip():
            st.markdown(text_before)

        language = match.group(1).lower()
        code = match.group(2).strip()

        st.code(code, language=language or "text") 

        if show_run and language in ("python", "py"):
            code_number += 1
            result_key = f"{message_id}_{code_number}"

            if st.button("▶ Run Python Code", key=f"run_{result_key}"):
                with st.spinner("Running code..."):
                    st.session_state.execution_results[result_key] = run_python_code(code)

            if result_key in st.session_state.execution_results:
                display_execution_result(st.session_state.execution_results[result_key])

        last_position = match.end()

    remaining_text = content[last_position:]

    if remaining_text.strip():
        st.markdown(remaining_text)
