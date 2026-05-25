import json
from datetime import datetime
from typing import Optional
from uuid import uuid4

from core.file_store import ensure_file, ensure_memory_dir, load_json_dict, load_jsonl_records, save_json_dict
from core.llm_client import client
from core.settings import (
    CHAT_HISTORY_PATH,
    CHAT_MODEL,
    LONG_TERM_MEMORY_PATH,
    MEMORY_RECALL_HISTORY_LIMIT,
    RECENT_HISTORY_LIMIT,
    SESSION_SUMMARIES_PATH,
    SUMMARY_MIN_MESSAGES,
    SUMMARY_PROMPT,
    SUMMARY_REFRESH_EVERY,
    SUMMARY_SOURCE_LIMIT,
    USER_PROFILE_PATH,
)


def bootstrap_memory_files() -> None:
    ensure_file(USER_PROFILE_PATH, "{}\n")
    ensure_file(LONG_TERM_MEMORY_PATH, "")
    ensure_file(CHAT_HISTORY_PATH, "")
    ensure_file(SESSION_SUMMARIES_PATH, "{}\n")


def load_user_profile() -> dict:
    return load_json_dict(USER_PROFILE_PATH)


def load_memories() -> list[dict]:
    return load_jsonl_records(LONG_TERM_MEMORY_PATH)


def load_session_summaries() -> dict:
    return load_json_dict(SESSION_SUMMARIES_PATH)


def get_session_summary(session_id: str) -> str:
    summaries = load_session_summaries()
    data = summaries.get(session_id, {})
    if not isinstance(data, dict):
        return ""
    return str(data.get("summary", "")).strip()


def save_session_summary(session_id: str, summary: str, message_count: int) -> None:
    summaries = load_session_summaries()
    summaries[session_id] = {
        "summary": summary.strip(),
        "message_count": message_count,
        "updated_at": current_timestamp(),
    }
    save_json_dict(SESSION_SUMMARIES_PATH, summaries)


def should_refresh_session_summary(session_id: str) -> bool:
    history = load_chat_history(session_id)
    message_count = len(history)

    if message_count < SUMMARY_MIN_MESSAGES:
        return False

    summaries = load_session_summaries()
    current = summaries.get(session_id, {})

    if not isinstance(current, dict):
        return True

    last_count = int(current.get("message_count", 0))
    return message_count - last_count >= SUMMARY_REFRESH_EVERY


def build_summary_source_text(session_id: str, limit: int = SUMMARY_SOURCE_LIMIT) -> str:
    previous_summary = get_session_summary(session_id)
    recent_records = load_chat_history(session_id)[-limit:]

    lines = []
    for item in recent_records:
        role = "用户" if item.get("role") == "user" else "助手"
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")

    sections = []

    if previous_summary:
        sections.append("[已有摘要]\n" + previous_summary)

    if lines:
        sections.append("[最新对话]\n" + "\n".join(lines))

    return "\n\n".join(sections).strip()


def generate_session_summary(session_id: str) -> str:
    source_text = build_summary_source_text(session_id)
    if not source_text:
        return ""

    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": source_text},
        ],
        stream=False,
    )

    return (completion.choices[0].message.content or "").strip()


def update_session_summary_if_needed(session_id: str) -> None:
    if not should_refresh_session_summary(session_id):
        return

    history = load_chat_history(session_id)
    summary = generate_session_summary(session_id)

    if not summary:
        return

    save_session_summary(session_id, summary, len(history))


def build_memory_recall_context(
    session_id: str,
    limit: int = MEMORY_RECALL_HISTORY_LIMIT,
) -> str:
    session_summary = get_session_summary(session_id)
    history = load_chat_history(session_id)[-limit:]
    user_lines = []

    for item in history:
        if item.get("role") != "user":
            continue
        content = str(item.get("content", "")).strip()
        if content:
            user_lines.append(f"- {content}")

    sections = []

    if session_summary:
        sections.append("[会话摘要]\n" + session_summary)

    if user_lines:
        sections.append("[用户最近说过的话]\n" + "\n".join(user_lines[-6:]))

    return "\n\n".join(sections).strip()


def ensure_session_id(session_id: Optional[str]) -> str:
    if session_id and session_id.strip():
        return session_id.strip()
    return f"sess_{uuid4().hex[:12]}"


def current_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_chat_message(
    session_id: str,
    role: str,
    content: str,
    agent_id: Optional[str] = None,
    intent: Optional[str] = None,
) -> dict:
    ensure_memory_dir()
    record = {
        "id": f"msg_{uuid4().hex[:12]}",
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": current_timestamp(),
    }

    if agent_id and agent_id.strip():
        record["agent_id"] = agent_id.strip()

    if intent and intent.strip():
        record["intent"] = intent.strip()

    with CHAT_HISTORY_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def load_chat_history(session_id: str) -> list[dict]:
    records = [
        item
        for item in load_jsonl_records(CHAT_HISTORY_PATH)
        if item.get("session_id") == session_id
    ]
    records.sort(key=lambda item: item.get("created_at", ""))
    return records


def load_recent_messages(session_id: str, limit: int = RECENT_HISTORY_LIMIT) -> list[dict]:
    if limit <= 0:
        return []
    return load_chat_history(session_id)[-limit:]


def build_history_messages(session_id: str, limit: int = RECENT_HISTORY_LIMIT) -> list[dict]:
    history_messages = []
    for item in load_recent_messages(session_id, limit):
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        history_messages.append({"role": role, "content": content})
    return history_messages
