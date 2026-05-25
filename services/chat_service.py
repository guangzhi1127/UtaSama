from core.llm_client import client
from core.settings import CHAT_MODEL
from schemas.chat import ChatRequest
from services.agent_router import detect_route, build_specialist_route_context
from services.keyword_service import MEMORY_KEYWORDS, contains_any
from services.memory_service import (
    append_chat_message,
    build_history_messages,
    build_memory_recall_context,
    ensure_session_id,
    get_session_summary,
    load_chat_history,
    update_session_summary_if_needed,
)
from services.pet_service import build_pet_state
from services.rag_service import build_rag_context
from services.runtime_service import (
    build_agent_system_prompt,
    get_agent_display_name,
    load_runtime_bundle,
)


def build_model_messages(
    payload: ChatRequest,
    session_id: str,
    runtime_bundle: dict,
    route: dict,
) -> tuple[list[dict], dict]:
    system_prompt = build_agent_system_prompt(runtime_bundle["entry_agent"], runtime_bundle)
    specialist_route_context = build_specialist_route_context(route, runtime_bundle)
    rag_context = build_rag_context(payload.message)
    session_summary = get_session_summary(session_id)
    history_messages = build_history_messages(session_id)
    memory_recall_context = ""

    if contains_any(payload.message, MEMORY_KEYWORDS):
        memory_recall_context = build_memory_recall_context(session_id)

    messages = [{"role": "system", "content": system_prompt}]

    if specialist_route_context:
        messages.append({"role": "system", "content": specialist_route_context})

    if rag_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "以下是与当前问题相关的知识库资料和长期记忆。"
                    "请优先依据这些内容回答；如果资料没有明确依据，不要编造。\n\n"
                    f"{rag_context}"
                ),
            }
        )

    if session_summary:
        messages.append(
            {
                "role": "system",
                "content": (
                    "以下是当前会话的阶段性摘要。"
                    "当最近几轮上下文不够时，可以参考这段摘要保持连贯。\n\n"
                    f"{session_summary}"
                ),
            }
        )

    if memory_recall_context:
        messages.append(
            {
                "role": "system",
                "content": (
                    "如果用户在问“还记得、刚才、最近、之前、我说过什么”之类的记忆问题，"
                    "请优先依据以下会话记录回答。"
                    "优先复述用户自己明确提到过的信息，不要替用户编造新的经历。\n\n"
                    f"{memory_recall_context}"
                ),
            }
        )

    messages.extend(history_messages)
    messages.append({"role": "user", "content": payload.message})

    debug_context = {
        "rag_context": rag_context,
        "session_summary": session_summary,
        "memory_recall_context": memory_recall_context,
        "history_messages": history_messages,
    }
    return messages, debug_context


def chat_with_agent(payload: ChatRequest) -> dict:
    session_id = ensure_session_id(payload.session_id)
    runtime_bundle = load_runtime_bundle()
    route = detect_route(payload.message, runtime_bundle)
    active_agent_id = route["active_agent"]
    agent_display_name = get_agent_display_name(active_agent_id, runtime_bundle)
    messages, debug_context = build_model_messages(payload, session_id, runtime_bundle, route)

    append_chat_message(
        session_id,
        "user",
        payload.message,
        agent_id=active_agent_id,
        intent=route["intent"],
    )

    completion = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        stream=False,
    )

    reply_text = completion.choices[0].message.content or ""
    if not reply_text:
        reply_text = "我接住你的话了，但这次回复是空的。"

    append_chat_message(
        session_id,
        "assistant",
        reply_text,
        agent_id=active_agent_id,
        intent=route["intent"],
    )

    updated_summary = debug_context["session_summary"]
    try:
        update_session_summary_if_needed(session_id)
        updated_summary = get_session_summary(session_id)
    except Exception as summary_error:
        print("Session summary update failed:", summary_error)

    pet_state = build_pet_state(payload.message, reply_text, route)

    return {
        "session_id": session_id,
        "reply_text": reply_text,
        "pet_state": pet_state,
        "pet_mood": pet_state["mood"],
        "pet_line": pet_state["voiceLine"],
        "entry_agent": runtime_bundle["entry_agent"],
        "active_agent": active_agent_id,
        "agent_display_name": agent_display_name,
        "intent": route["intent"],
        "route_reason": route["route_reason"],
        "matched_hints": route["matched_hints"],
        "preferred_skills": route["preferred_skills"],
        "preferred_mcp": route["preferred_mcp"],
        "rag_used": bool(debug_context["rag_context"]),
        "summary_used": bool(debug_context["session_summary"]),
        "memory_recall_used": bool(debug_context["memory_recall_context"]),
        "history_used": len(debug_context["history_messages"]),
        "history_message_count": len(load_chat_history(session_id)),
        "rag_preview": debug_context["rag_context"][:600],
        "summary_preview": updated_summary[:300],
    }
