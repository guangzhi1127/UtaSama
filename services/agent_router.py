from services.keyword_service import (
    COMFORT_KEYWORDS,
    MEMORY_KEYWORDS,
    PROJECT_KEYWORDS,
    SPECIALIST_ROUTE_ALIASES,
    WORLD_KEYWORDS,
    collect_keyword_hits,
    contains_any,
)
from services.runtime_service import build_agent_system_prompt, get_agent_display_name, summarize_items


def detect_message_intent(message: str) -> str:
    if contains_any(message, MEMORY_KEYWORDS):
        return "memory-recall"
    if contains_any(message, WORLD_KEYWORDS):
        return "world-knowledge"
    if contains_any(message, PROJECT_KEYWORDS):
        return "project-support"
    if contains_any(message, COMFORT_KEYWORDS):
        return "comfort"
    return "companion-chat"


def detect_route(message: str, runtime_bundle: dict) -> dict:
    entry_agent = runtime_bundle["entry_agent"]
    best_agent = entry_agent
    best_hits: list[str] = []

    for agent in runtime_bundle["agents"]:
        agent_id = str(agent.get("id", "")).strip()
        if not agent_id or agent_id == entry_agent:
            continue

        keywords = [
            str(item).strip()
            for item in agent.get("inputHints", [])
            if str(item).strip()
        ]
        keywords.extend(SPECIALIST_ROUTE_ALIASES.get(agent_id, []))

        hits = collect_keyword_hits(message, keywords)
        if len(hits) > len(best_hits):
            best_agent = agent_id
            best_hits = hits

    intent = detect_message_intent(message)
    agent = runtime_bundle.get("agent_index", {}).get(best_agent, {})
    preferred_skills = [
        str(item).strip() for item in agent.get("preferredSkills", []) if str(item).strip()
    ]
    preferred_mcp = [
        str(item).strip() for item in agent.get("preferredMcp", []) if str(item).strip()
    ]

    if best_agent != entry_agent and best_hits:
        route_reason = (
            f"命中 {get_agent_display_name(best_agent, runtime_bundle)} 关键词："
            f"{summarize_items(best_hits)}"
        )
    elif intent == "memory-recall":
        route_reason = "命中记忆追问，保留主聊天 Agent 并优先参考会话历史。"
    elif intent == "world-knowledge":
        route_reason = "命中设定问答，保留主聊天 Agent 并结合知识库回答。"
    elif intent == "project-support":
        route_reason = "命中项目协作语境，保留主聊天 Agent 处理任务沟通。"
    elif intent == "comfort":
        route_reason = "命中情绪陪伴语境，保留主聊天 Agent 温柔接住。"
    else:
        route_reason = "未命中专项 Agent，按主聊天 Agent 处理。"

    return {
        "intent": intent,
        "active_agent": best_agent,
        "route_reason": route_reason,
        "matched_hints": best_hits,
        "preferred_skills": preferred_skills,
        "preferred_mcp": preferred_mcp,
    }


def build_specialist_route_context(route: dict, runtime_bundle: dict) -> str:
    active_agent = route.get("active_agent", runtime_bundle["entry_agent"])
    if active_agent == runtime_bundle["entry_agent"]:
        return ""

    specialist_prompt = build_agent_system_prompt(active_agent, runtime_bundle)
    display_name = get_agent_display_name(active_agent, runtime_bundle)

    sections = [
        f"当前这轮由 {display_name} 提供专项思路。",
        f"意图：{route.get('intent', 'companion-chat')}",
        f"路由原因：{route.get('route_reason', '未说明')}",
        f"优先 Skills：{summarize_items(route.get('preferred_skills', []))}",
        f"优先 MCP：{summarize_items(route.get('preferred_mcp', []))}",
        "最终回复仍然直接面向用户，用 UtaSama 主聊天 Agent 的自然口吻收口，"
        "不要把内部路由过程生硬地念出来。",
    ]

    if specialist_prompt:
        sections.append("[专项 Agent 指令]\n" + specialist_prompt)

    return "\n\n".join(sections).strip()
