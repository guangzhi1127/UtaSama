import json

from core.file_store import load_markdown_library
from core.settings import KNOWLEDGE_DIR
from services.keyword_service import (
    MEMORY_KEYWORDS,
    PERSONA_KEYWORDS,
    WORLD_KEYWORDS,
    contains_any,
    score_document,
)
from services.memory_service import load_memories, load_user_profile


def retrieve_persona_docs(query: str) -> list[str]:
    docs = load_markdown_library(KNOWLEDGE_DIR / "persona")
    if not docs:
        return []

    results = []

    # 核心人设默认带上，帮助角色稳定。
    for doc in docs:
        if doc["filename"].startswith("00_"):
            results.append(doc["content"])

    if contains_any(query, PERSONA_KEYWORDS):
        scored = sorted(
            docs,
            key=lambda doc: score_document(query, doc["content"], doc["filename"]),
            reverse=True,
        )
        for doc in scored[:2]:
            if doc["content"] not in results:
                results.append(doc["content"])

    return results[:3]


def retrieve_world_docs(query: str) -> list[str]:
    if not contains_any(query, WORLD_KEYWORDS):
        return []

    docs = load_markdown_library(KNOWLEDGE_DIR / "world")
    if not docs:
        return []

    scored = sorted(
        docs,
        key=lambda doc: score_document(query, doc["content"], doc["filename"]),
        reverse=True,
    )
    return [doc["content"] for doc in scored[:2]]


def retrieve_memory_items(query: str) -> list[str]:
    results = []

    if contains_any(query, MEMORY_KEYWORDS):
        profile = load_user_profile()
        if profile:
            results.append(json.dumps(profile, ensure_ascii=False, indent=2))

    memories = load_memories()
    if not memories:
        return results

    scored_memories = []
    for item in memories:
        text = item.get("text", "")
        tags = " ".join(item.get("tags", []))
        importance = float(item.get("importance", 0))
        score = score_document(query, f"{text} {tags}") + int(importance * 10)
        scored_memories.append((score, text))

    scored_memories.sort(key=lambda pair: pair[0], reverse=True)

    for score, text in scored_memories[:3]:
        if score > 0:
            results.append(text)

    return results[:4]


def build_rag_context(query: str) -> str:
    persona_chunks = retrieve_persona_docs(query)
    world_chunks = retrieve_world_docs(query)
    memory_chunks = retrieve_memory_items(query)

    sections = []

    if persona_chunks:
        sections.append("[角色设定资料]\n" + "\n\n".join(persona_chunks))

    if world_chunks:
        sections.append("[世界设定资料]\n" + "\n\n".join(world_chunks))

    if memory_chunks:
        sections.append("[长期记忆]\n" + "\n".join(f"- {item}" for item in memory_chunks))

    return "\n\n".join(sections).strip()
