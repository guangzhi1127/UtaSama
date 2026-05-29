from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import app
from skills.music_player_skill import (
    classify_music_action,
    extract_song_query,
    run_music_skill,
    try_open_client_target,
)


def test_intent_detection() -> None:
    assert classify_music_action("放点 Ado") == "play_ado_playlist"
    assert classify_music_action("播放逆光") == "play_ado_playlist"
    assert classify_music_action("我要听新时代") == "play_ado_playlist"
    assert classify_music_action("放一首新时代") == "play_ado_playlist"
    assert classify_music_action("你喜欢音乐吗") == "state"
    assert extract_song_query("播放逆光") == "逆光"
    assert extract_song_query("我要听新时代") == "新时代"
    assert extract_song_query("放一首新时代") == "新时代"
    assert extract_song_query("放点 Ado") == ""


def test_random_track_dry_run() -> None:
    result = run_music_skill("play_ado_playlist", dry_run=True)
    assert result["ok"] is True
    assert result["state"]["selection_mode"] == "random"
    assert result["state"]["selected_track"]
    assert result["state"]["playback_target"] == "client_automation"
    assert result["state"]["dry_run"] is True


def test_requested_track_dry_run() -> None:
    result = run_music_skill("play_ado_playlist", song_query="逆光", dry_run=True)
    assert result["ok"] is True
    assert result["state"]["selection_mode"] == "requested"
    assert result["state"]["selected_track"]["title"] == "逆光"
    assert result["state"]["playback_target"] == "client_automation"

    result = run_music_skill("play_ado_playlist", song_query="新时代", dry_run=True)
    assert result["ok"] is True
    assert result["state"]["selection_mode"] == "requested"
    assert result["state"]["selected_track"]["title"] == "新時代"
    assert result["state"]["playback_target"] == "client_automation"


def test_client_target_priority_dry_run() -> None:
    config = {"netease_path": sys.executable, "launch_wait_seconds": 0}
    playlist = {"client_uri": "orpheus://playlist/test"}
    ok, message, warnings = try_open_client_target(config, playlist, None, dry_run=True)
    assert ok is True
    assert "dry-run" in message
    assert warnings == []


def test_fastapi_music_play_dry_run() -> None:
    client = TestClient(app)
    response = client.post("/skills/music/play", json={"song": "逆光", "dry_run": True})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["state"]["selection_mode"] == "requested"
    assert data["state"]["selected_track"]["title"] == "逆光"
    assert data["state"]["playback_target"] == "client_automation"


def main() -> int:
    test_intent_detection()
    test_random_track_dry_run()
    test_requested_track_dry_run()
    test_client_target_priority_dry_run()
    test_fastapi_music_play_dry_run()
    print("music skill smoke tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
