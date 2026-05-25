import json
from pathlib import Path
from typing import Optional

from core.settings import MEMORY_DIR


def ensure_memory_dir() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def ensure_file(path: Path, default_text: str) -> None:
    ensure_memory_dir()
    if not path.exists():
        path.write_text(default_text, encoding="utf-8")


def load_markdown_library(folder: Path) -> list[dict]:
    docs = []
    if not folder.exists():
        return docs

    for path in sorted(folder.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        docs.append(
            {
                "id": path.stem,
                "filename": path.name,
                "path": str(path),
                "content": content,
            }
        )
    return docs


def load_json_dict(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def save_json_dict(path: Path, data: dict) -> None:
    ensure_memory_dir()
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_jsonl_records(path: Path) -> list[dict]:
    if not path.exists():
        return []

    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)

    return records


def resolve_existing_path(candidates: list[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists():
            return path
    return None


def resolve_config_reference(base_file: Path, raw_path: str) -> Optional[Path]:
    value = str(raw_path or "").strip()
    if not value:
        return None
    return (base_file.parent / value).resolve()


def load_text_file(path: Optional[Path]) -> str:
    if not path or not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()
