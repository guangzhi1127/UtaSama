import importlib.util
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from core.file_store import load_jsonl_records, load_markdown_library
from core.settings import (
    KNOWLEDGE_DIR,
    RAG_CHUNK_DIR,
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_PATH,
    RAG_CHUNK_SIZE,
    RAG_COLLECTION_NAME,
    RAG_EMBED_BATCH_SIZE,
    RAG_EMBEDDING_MODEL,
    RAG_SOURCE_FOLDERS,
    RAG_TOP_K,
    RAG_VECTOR_DB_DIR,
)
from services.keyword_service import (
    MEMORY_KEYWORDS,
    PERSONA_KEYWORDS,
    WORLD_KEYWORDS,
    contains_any,
    score_document,
)
from services.memory_service import load_memories, load_user_profile


_embedding_model = None


def get_rag_dependency_status() -> dict:
    return {
        "chromadb": importlib.util.find_spec("chromadb") is not None,
        "sentence_transformers": importlib.util.find_spec("sentence_transformers") is not None,
    }


def require_vector_dependencies() -> None:
    status = get_rag_dependency_status()
    missing = [name for name, installed in status.items() if not installed]
    if missing:
        raise RuntimeError(
            "RAG 向量检索依赖未安装："
            + "、".join(missing)
            + "。请先运行：python -m pip install -r requirements.txt"
        )


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_markdown_sections(text: str) -> list[dict]:
    lines = normalize_text(text).splitlines()
    sections = []
    current_title = "正文"
    current_lines: list[str] = []

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({"title": current_title, "content": content})

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if heading_match:
            flush()
            current_title = heading_match.group(2).strip()
            current_lines = [line]
            continue
        current_lines.append(line)

    flush()
    return sections


def split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    text = text.strip()

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

    return chunks


def split_text_into_chunks(
    text: str,
    chunk_size: int = RAG_CHUNK_SIZE,
    overlap: int = RAG_CHUNK_OVERLAP,
) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    chunks = []
    current = ""

    def flush_current() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            flush_current()
            chunks.extend(split_long_text(paragraph, chunk_size, overlap))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        flush_current()
        tail = chunks[-1][-overlap:].strip() if chunks and overlap > 0 else ""
        candidate = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
        current = candidate if len(candidate) <= chunk_size else paragraph

    flush_current()
    return chunks


def load_source_documents() -> list[dict]:
    documents = []
    for source_type in RAG_SOURCE_FOLDERS:
        folder = KNOWLEDGE_DIR / source_type
        for doc in load_markdown_library(folder):
            documents.append(
                {
                    **doc,
                    "source_type": source_type,
                    "relative_path": str(Path(source_type) / doc["filename"]),
                }
            )
    return documents


def make_chunk_id(source_type: str, document_id: str, chunk_index: int) -> str:
    raw_id = f"{source_type}_{document_id}_{chunk_index}"
    return re.sub(r"[^a-zA-Z0-9_\-]+", "_", raw_id)


def build_chunk_records() -> list[dict]:
    records = []
    for doc in load_source_documents():
        chunk_index = 0
        for section in split_markdown_sections(doc["content"]):
            for chunk_text in split_text_into_chunks(section["content"]):
                records.append(
                    {
                        "id": make_chunk_id(doc["source_type"], doc["id"], chunk_index),
                        "source_type": doc["source_type"],
                        "source_name": doc["filename"],
                        "source_path": doc["relative_path"],
                        "document_id": doc["id"],
                        "section": section["title"],
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "char_count": len(chunk_text),
                    }
                )
                chunk_index += 1
    return records


def save_chunks(records: list[dict]) -> None:
    RAG_CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    with RAG_CHUNK_PATH.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_chunks() -> list[dict]:
    return load_jsonl_records(RAG_CHUNK_PATH)


def rebuild_chunks() -> dict:
    records = build_chunk_records()
    save_chunks(records)
    return {
        "status": "ok",
        "chunk_count": len(records),
        "chunk_path": str(RAG_CHUNK_PATH),
        "source_folders": list(RAG_SOURCE_FOLDERS),
        "chunk_size": RAG_CHUNK_SIZE,
        "chunk_overlap": RAG_CHUNK_OVERLAP,
    }


def load_embedding_model():
    global _embedding_model
    require_vector_dependencies()
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(RAG_EMBEDDING_MODEL)
    return _embedding_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = load_embedding_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [vector.tolist() for vector in vectors]


def get_chroma_client():
    require_vector_dependencies()
    import chromadb
    from chromadb.config import Settings

    os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
    logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
    RAG_VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(RAG_VECTOR_DB_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_vector_collection(create: bool = False):
    client = get_chroma_client()
    if create:
        return client.get_or_create_collection(
            name=RAG_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    try:
        return client.get_collection(name=RAG_COLLECTION_NAME)
    except Exception:
        return None


def reset_vector_collection() -> None:
    client = get_chroma_client()
    try:
        client.delete_collection(name=RAG_COLLECTION_NAME)
    except Exception:
        pass


def rebuild_vector_index(force_rebuild_chunks: bool = True) -> dict:
    require_vector_dependencies()

    if force_rebuild_chunks or not RAG_CHUNK_PATH.exists():
        chunk_result = rebuild_chunks()
    else:
        chunk_result = {
            "status": "skipped",
            "chunk_count": len(load_chunks()),
            "chunk_path": str(RAG_CHUNK_PATH),
        }

    chunks = load_chunks()
    if not chunks:
        raise RuntimeError("没有可索引的 chunk，请先检查 knowledge/persona 和 knowledge/world。")

    reset_vector_collection()
    collection = get_vector_collection(create=True)

    for start in range(0, len(chunks), RAG_EMBED_BATCH_SIZE):
        batch = chunks[start : start + RAG_EMBED_BATCH_SIZE]
        texts = [item["text"] for item in batch]
        embeddings = embed_texts(texts)
        metadatas = [
            {
                "source_type": item["source_type"],
                "source_name": item["source_name"],
                "source_path": item["source_path"],
                "document_id": item["document_id"],
                "section": item["section"],
                "chunk_index": int(item["chunk_index"]),
                "char_count": int(item["char_count"]),
            }
            for item in batch
        ]
        collection.add(
            ids=[item["id"] for item in batch],
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    return {
        "status": "ok",
        "chunk": chunk_result,
        "vector_db_dir": str(RAG_VECTOR_DB_DIR),
        "collection": RAG_COLLECTION_NAME,
        "embedding_model": RAG_EMBEDDING_MODEL,
        "indexed_count": collection.count(),
    }


def get_vector_collection_count() -> int:
    try:
        collection = get_vector_collection(create=False)
        return collection.count() if collection else 0
    except Exception:
        return 0


def search_vector_index(query: str, top_k: int = RAG_TOP_K) -> list[dict]:
    if not query.strip():
        return []

    require_vector_dependencies()
    collection = get_vector_collection(create=False)
    if collection is None or collection.count() <= 0:
        return []

    query_embedding = embed_texts([query])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=max(1, top_k),
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    ids = result.get("ids", [[]])[0]

    matches = []
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        score = None if distance is None else round(1 - float(distance), 4)
        matches.append(
            {
                "id": ids[index] if index < len(ids) else "",
                "text": document,
                "metadata": metadata,
                "distance": distance,
                "score": score,
            }
        )

    return matches


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


def build_keyword_rag_context(query: str) -> str:
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


def format_vector_results_as_context(matches: list[dict]) -> str:
    blocks = []
    for index, match in enumerate(matches, start=1):
        metadata = match.get("metadata") or {}
        source = metadata.get("source_path") or metadata.get("source_name") or "unknown"
        section = metadata.get("section") or "正文"
        score = match.get("score")
        score_text = "未知" if score is None else str(score)
        blocks.append(
            f"[资料 {index}] 来源：{source} / 小节：{section} / 相似度：{score_text}\n"
            f"{match.get('text', '').strip()}"
        )

    return "[向量知识库检索结果]\n" + "\n\n".join(blocks)


def build_rag_payload(query: str, top_k: int = RAG_TOP_K) -> dict:
    memory_chunks = retrieve_memory_items(query)

    try:
        vector_matches = search_vector_index(query, top_k=top_k)
    except Exception as error:
        keyword_context = build_keyword_rag_context(query)
        return {
            "context": keyword_context,
            "mode": "keyword-fallback",
            "matches": [],
            "error": str(error),
        }

    sections = []
    if vector_matches:
        sections.append(format_vector_results_as_context(vector_matches))

    if memory_chunks:
        sections.append("[长期记忆]\n" + "\n".join(f"- {item}" for item in memory_chunks))

    if sections:
        return {
            "context": "\n\n".join(sections).strip(),
            "mode": "vector",
            "matches": vector_matches,
            "error": "",
        }

    keyword_context = build_keyword_rag_context(query)
    return {
        "context": keyword_context,
        "mode": "keyword-fallback",
        "matches": [],
        "error": "向量库为空或没有命中，已使用关键词检索降级。",
    }


def build_rag_context(query: str) -> str:
    return build_rag_payload(query)["context"]


def get_rag_status() -> dict:
    chunks = load_chunks()
    dependency_status = get_rag_dependency_status()
    vector_available = all(dependency_status.values())
    return {
        "dependency_status": dependency_status,
        "vector_available": vector_available,
        "embedding_model": RAG_EMBEDDING_MODEL,
        "collection": RAG_COLLECTION_NAME,
        "chunk_path": str(RAG_CHUNK_PATH),
        "chunk_count": len(chunks),
        "vector_db_dir": str(RAG_VECTOR_DB_DIR),
        "vector_indexed_count": get_vector_collection_count() if vector_available else 0,
        "source_folders": list(RAG_SOURCE_FOLDERS),
        "chunk_size": RAG_CHUNK_SIZE,
        "chunk_overlap": RAG_CHUNK_OVERLAP,
        "top_k": RAG_TOP_K,
    }
