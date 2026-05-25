import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.settings import RAG_TOP_K  # noqa: E402
from services.rag_service import search_vector_index  # noqa: E402


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        raise SystemExit("用法：python scripts/search_rag.py 乌塔和路飞是什么关系")

    result = {
        "query": query,
        "top_k": RAG_TOP_K,
        "matches": search_vector_index(query, top_k=RAG_TOP_K),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
