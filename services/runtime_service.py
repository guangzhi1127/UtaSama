from typing import Optional

from core.file_store import (
    load_json_dict,
    load_text_file,
    resolve_config_reference,
    resolve_existing_path,
)
from core.settings import (
    AGENT_REGISTRY_PATH,
    MCP_PROVIDER_CANDIDATES,
    SKILL_REGISTRY_CANDIDATES,
    SYSTEM_PROMPT,
)


def fallback_agent_registry() -> dict:
    return {
        "project": "UtaSama",
        "entryAgent": "utasama-main",
        "agents": [
            {
                "id": "utasama-main",
                "displayName": "UtaSama Main Agent",
                "type": "primary",
                "capabilities": [
                    "chat",
                    "persona-consistency",
                    "task-routing",
                    "response-merge",
                ],
                "delegatesTo": ["music-agent", "image-agent", "pet-agent"],
                "extensionPoints": ["custom-agents", "custom-skills", "custom-mcp"],
            },
            {
                "id": "music-agent",
                "displayName": "Music Agent",
                "type": "specialist",
                "inputHints": ["music", "song", "playlist", "mood"],
                "preferredSkills": ["music-player"],
                "preferredMcp": ["music-library"],
            },
            {
                "id": "image-agent",
                "displayName": "Image Agent",
                "type": "specialist",
                "inputHints": ["draw", "image", "avatar", "pet", "sticker"],
                "preferredSkills": ["image-generation"],
                "preferredMcp": ["asset-storage"],
            },
            {
                "id": "pet-agent",
                "displayName": "Pet Agent",
                "type": "specialist",
                "inputHints": ["pet", "emotion", "idle", "interaction"],
                "preferredSkills": ["pet-animation"],
                "preferredMcp": [],
            },
        ],
    }


def load_agent_registry() -> dict:
    data = load_json_dict(AGENT_REGISTRY_PATH)
    if not data:
        return fallback_agent_registry()
    if not isinstance(data.get("agents"), list):
        data["agents"] = fallback_agent_registry()["agents"]
    if not data.get("entryAgent"):
        data["entryAgent"] = fallback_agent_registry()["entryAgent"]
    return data


def load_skill_registry() -> dict:
    path = resolve_existing_path(SKILL_REGISTRY_CANDIDATES)
    if not path:
        return {"skills": []}
    data = load_json_dict(path)
    if not isinstance(data.get("skills"), list):
        data["skills"] = []
    data["_path"] = str(path)
    return data


def load_mcp_providers() -> dict:
    path = resolve_existing_path(MCP_PROVIDER_CANDIDATES)
    if not path:
        return {"providers": []}
    data = load_json_dict(path)
    if not isinstance(data.get("providers"), list):
        data["providers"] = []
    data["_path"] = str(path)
    return data


def summarize_items(items: list[str], empty: str = "暂无") -> str:
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return empty
    return "、".join(cleaned)


def load_runtime_bundle() -> dict:
    agent_registry = load_agent_registry()
    skills_registry = load_skill_registry()
    mcp_registry = load_mcp_providers()

    agents = [
        item
        for item in agent_registry.get("agents", [])
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    ]
    entry_agent = str(agent_registry.get("entryAgent", "")).strip()
    if not entry_agent and agents:
        entry_agent = str(agents[0].get("id", "")).strip()
    if not entry_agent:
        entry_agent = "utasama-main"

    return {
        "project": str(agent_registry.get("project", "UtaSama")).strip() or "UtaSama",
        "entry_agent": entry_agent,
        "agents": agents,
        "agent_index": {
            str(item.get("id")).strip(): item
            for item in agents
            if str(item.get("id", "")).strip()
        },
        "skills": [
            item
            for item in skills_registry.get("skills", [])
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ],
        "mcp_providers": [
            item
            for item in mcp_registry.get("providers", [])
            if isinstance(item, dict) and str(item.get("id", "")).strip()
        ],
    }


def get_agent_display_name(agent_id: str, runtime_bundle: dict) -> str:
    agent = runtime_bundle.get("agent_index", {}).get(agent_id, {})
    value = str(agent.get("displayName", "")).strip()
    return value or agent_id


def build_runtime_config() -> dict:
    runtime_bundle = load_runtime_bundle()
    entry_agent = runtime_bundle["entry_agent"]

    return {
        "project": runtime_bundle["project"],
        "entry_agent": entry_agent,
        "entry_agent_display_name": get_agent_display_name(entry_agent, runtime_bundle),
        "agents": [
            {
                "id": str(agent.get("id", "")).strip(),
                "display_name": str(agent.get("displayName", "")).strip()
                or str(agent.get("id", "")).strip(),
                "type": str(agent.get("type", "")).strip() or "specialist",
                "summary": summarize_items(
                    agent.get("capabilities", []) or agent.get("inputHints", []),
                    "待补充职责说明",
                ),
                "delegates_to": [
                    str(item).strip()
                    for item in agent.get("delegatesTo", [])
                    if str(item).strip()
                ],
            }
            for agent in runtime_bundle["agents"]
        ],
        "skills": [
            {
                "id": str(skill.get("id", "")).strip(),
                "display_name": str(skill.get("displayName", "")).strip()
                or str(skill.get("id", "")).strip(),
                "category": str(skill.get("category", "")).strip() or "general",
                "status": str(skill.get("status", "")).strip() or "planned",
                "summary": str(skill.get("entry", "")).strip()
                or summarize_items(skill.get("boundAgents", []), "待补充 Skill 入口"),
            }
            for skill in runtime_bundle["skills"]
        ],
        "mcp": [
            {
                "id": str(provider.get("id", "")).strip(),
                "display_name": str(provider.get("displayName", "")).strip()
                or str(provider.get("id", "")).strip(),
                "transport": str(provider.get("transport", "")).strip() or "unknown",
                "summary": summarize_items(provider.get("capabilities", []), "待补充 MCP 能力"),
            }
            for provider in runtime_bundle["mcp_providers"]
        ],
    }


def build_agent_system_prompt(agent_id: str, runtime_bundle: dict) -> str:
    agent = runtime_bundle.get("agent_index", {}).get(agent_id, {})
    sections = []

    persona_path = resolve_config_reference(
        AGENT_REGISTRY_PATH,
        str(agent.get("personaPath", "")).strip(),
    )
    system_prompt_path = resolve_config_reference(
        AGENT_REGISTRY_PATH,
        str(agent.get("systemPromptPath", "")).strip(),
    )

    persona_text = load_text_file(persona_path)
    system_prompt_text = load_text_file(system_prompt_path)

    if persona_text:
        sections.append("[角色人设]\n" + persona_text)

    if system_prompt_text:
        sections.append("[系统指令]\n" + system_prompt_text)

    if sections:
        return "\n\n".join(sections).strip()

    if agent_id == runtime_bundle["entry_agent"]:
        return SYSTEM_PROMPT.strip()

    display_name = get_agent_display_name(agent_id, runtime_bundle)
    return f"你当前按 {display_name} 的专项职责协助主聊天 Agent。"
