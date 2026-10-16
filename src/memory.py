import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from src.llm_config import llm


DB_FILE = Path(__file__).resolve().parent.parent / "chat_memory.db"

# How many last messages are sent to the LLM each time
MAX_HISTORY = 6


# Database basics
def run_query(sql, params=(), fetch=False):
    """Run one SQL command. If fetch=True, return the rows."""
    connection = sqlite3.connect(DB_FILE)

    try:
        cursor = connection.execute(sql, params)
        rows = cursor.fetchall() if fetch else None
        last_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    if fetch:
        return rows

    return last_id


def init_db():
    run_query("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT
        )
    """)

    run_query("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            role TEXT,
            content TEXT,
            route TEXT,
            created_at TEXT
        )
    """)

    run_query("""
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)


init_db()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Conversations
def create_conversation(title="New chat"):
    """Add a new empty conversation and return its id."""
    return run_query(
        "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
        (title, now())
    )


def list_conversations():
    """Return [(id, title), ...] with the newest chat first."""
    return run_query(
        "SELECT id, title FROM conversations ORDER BY id DESC",
        fetch=True
    )


def update_title(conversation_id, title):
    run_query(
        "UPDATE conversations SET title = ? WHERE id = ?",
        (title, conversation_id)
    )


def delete_conversation(conversation_id):
    run_query("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    run_query("DELETE FROM conversations WHERE id = ?", (conversation_id,))


# Messages
def save_message(conversation_id, role, content, route=None):
    run_query(
        "INSERT INTO messages (conversation_id, role, content, route, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (conversation_id, role, content, route, now())
    )


def load_messages(conversation_id):
    rows = run_query(
        "SELECT role, content, route FROM messages "
        "WHERE conversation_id = ? ORDER BY id",
        (conversation_id,),
        fetch=True
    )

    messages = []

    for role, content, route in rows:
        message = {"role": role, "content": content}
        if route:
            message["route"] = route
        messages.append(message)

    return messages


# Preferences
def load_preferences():
    rows = run_query("SELECT key, value FROM preferences", fetch=True)
    return {key: value for key, value in rows}


def save_preferences(preferences):
    run_query("DELETE FROM preferences")

    for key, value in preferences.items():
        run_query(
            "INSERT INTO preferences (key, value) VALUES (?, ?)",
            (key, value)
        )


def update_preferences(message, preferences):
    prompt = f"""
Read the user's message and find coding preferences.
Return ONLY JSON like this: {{"language": "", "framework": ""}}
Use an empty string if the user did not mention it.

User message:
{message}
"""

    try:
        response = llm.invoke(prompt)
        match = re.search(r"\{.*\}", response.content, re.DOTALL)
        data = json.loads(match.group())
    except Exception:
        return preferences        # if anything fails, keep the old ones

    for key in ("language", "framework"):
        value = str(data.get(key, "")).strip()
        if value:
            preferences[key] = value

    return preferences


def format_memory(messages, preferences):
    """Turn the memory into text that is sent to the LLM."""
    text = ""

    if preferences:
        text += f"User preferences: {json.dumps(preferences)}\n\n"

    for message in messages[-MAX_HISTORY:]:
        text += f"{message['role']}: {message['content'][:2000]}\n"

    return text

