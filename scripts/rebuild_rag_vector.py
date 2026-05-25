import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.rag_service import rebuild_vector_index  # noqa: E402


if __name__ == "__main__":
    result = rebuild_vector_index(force_rebuild_chunks=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
