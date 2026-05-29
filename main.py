from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from core.settings import RAG_TOP_K, RECENT_HISTORY_LIMIT
from schemas.chat import ChatRequest
from schemas.music import MusicModeRequest, MusicPlayRequest
from services.chat_service import chat_with_agent
from services.memory_service import bootstrap_memory_files, get_session_summary, load_chat_history
from services.rag_service import (
    get_rag_status,
    rebuild_chunks,
    rebuild_vector_index,
    search_vector_index,
)
from services.runtime_service import build_runtime_config
from skills.music_player_skill import load_music_state, normalize_mode, run_music_skill


bootstrap_memory_files()

app = FastAPI(title="UtaSama Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/runtime/config")
def runtime_config():
    return build_runtime_config()


@app.get("/history/{session_id}")
def history(session_id: str, limit: int = RECENT_HISTORY_LIMIT):
    full_history = load_chat_history(session_id)
    session_summary = get_session_summary(session_id)
    return {
        "session_id": session_id,
        "message_count": len(full_history),
        "recent_messages": full_history[-limit:] if limit > 0 else full_history,
        "summary": session_summary,
    }


@app.get("/rag/status")
def rag_status():
    return get_rag_status()


@app.post("/rag/chunks/rebuild")
def rag_rebuild_chunks():
    try:
        return rebuild_chunks()
    except Exception as error:
        print("RAG chunk rebuild failed:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/rag/vector/rebuild")
def rag_rebuild_vector(force_rebuild_chunks: bool = True):
    try:
        return rebuild_vector_index(force_rebuild_chunks=force_rebuild_chunks)
    except Exception as error:
        print("RAG vector rebuild failed:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/rag/search")
def rag_search(query: str = Query(..., min_length=1), top_k: int = RAG_TOP_K):
    try:
        return {
            "query": query,
            "top_k": top_k,
            "matches": search_vector_index(query, top_k=top_k),
        }
    except Exception as error:
        print("RAG search failed:", error)
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/skills/music/state")
def music_state():
    return load_music_state()


@app.post("/skills/music/play")
def music_play(payload: Optional[MusicPlayRequest] = None):
    payload = payload or MusicPlayRequest()
    return run_music_skill(
        "play_ado_playlist",
        playlist_url=payload.playlist_url,
        mode=payload.mode,
        song_query=payload.song,
        dry_run=payload.dry_run,
    )


@app.post("/skills/music/pause")
def music_pause():
    return run_music_skill("pause")


@app.post("/skills/music/resume")
def music_resume():
    return run_music_skill("resume")


@app.post("/skills/music/next")
def music_next():
    return run_music_skill("next")


@app.post("/skills/music/previous")
def music_previous():
    return run_music_skill("previous")


@app.post("/skills/music/stop")
def music_stop():
    return run_music_skill("stop")


@app.post("/skills/music/mode")
def music_mode(payload: MusicModeRequest):
    action = "stage_mode" if normalize_mode(payload.mode) == "stage" else "background_mode"
    return run_music_skill(action)


@app.post("/chat")
def chat(payload: ChatRequest):
    try:
        return chat_with_agent(payload)
    except Exception as error:
        print("DeepSeek request failed:", error)
        raise HTTPException(status_code=500, detail="DeepSeek request failed")
