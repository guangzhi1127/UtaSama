from __future__ import annotations

import json
import os
import random
import re
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

try:
    from ctypes import windll
except ImportError:  # pragma: no cover - only relevant outside Windows.
    windll = None

from core.settings import BASE_DIR, CONFIG_DIR, MEMORY_DIR
from skills.netease_ui_automation import automate_netease_search_play, normalize_automation_config


CONFIG_PATH = CONFIG_DIR / "music_player.json"
STATE_PATH = MEMORY_DIR / "music_player_state.json"
DEFAULT_SEARCH_URL = "https://music.163.com/#/search/m/?s=Ado&type=1000"
VALID_MODES = {"background", "stage"}
DEFAULT_PLAYLIST_ID = "ado"

MEDIA_KEYS = {
    "pause": 0xB3,
    "resume": 0xB3,
    "next": 0xB0,
    "previous": 0xB1,
    "stop": 0xB2,
}

COMMAND_WORDS = [
    "我想听",
    "我要听",
    "想听",
    "听一下",
    "听听",
    "听",
    "给我放",
    "帮我放",
    "放一首",
    "放首",
    "播放",
    "放歌",
    "听歌",
    "放点",
    "来点",
    "放",
    "打开",
    "启动",
    "网易云",
    "音乐",
    "歌单",
    "ado",
    "Ado",
    "一首",
    "随机",
    "随便",
    "来一首",
    "给我",
    "帮我",
    "请",
]


def default_tracks() -> list[dict[str, Any]]:
    return [
        {"title": "新時代", "artist": "Ado", "aliases": ["新时代", "New Genesis"]},
        {"title": "私は最強", "artist": "Ado", "aliases": ["我是最强", "I'm invincible"]},
        {"title": "逆光", "artist": "Ado", "aliases": ["Backlight"]},
        {"title": "ウタカタララバイ", "artist": "Ado", "aliases": ["泡影摇篮曲", "Fleeting Lullaby"]},
        {"title": "Tot Musica", "artist": "Ado", "aliases": ["托特穆吉卡"]},
        {"title": "踊", "artist": "Ado", "aliases": ["Odo"]},
        {"title": "うっせぇわ", "artist": "Ado", "aliases": ["吵死了", "Usseewa"]},
        {"title": "唱", "artist": "Ado", "aliases": ["Show"]},
    ]


def default_config() -> dict[str, Any]:
    return {
        "netease_path": "",
        "preferred_playlist": DEFAULT_PLAYLIST_ID,
        "ado_playlist_url": DEFAULT_SEARCH_URL,
        "default_mode": "background",
        "launch_wait_seconds": 1.2,
        "allow_web_fallback": False,
        "automation": {
            "enabled": True,
            "backend": "uia",
            "window_title_regex": ".*(网易云音乐|NetEase|CloudMusic|云音乐).*",
            "try_find_search_edit": True,
            "search_edit_name_keywords": ["搜索", "Search"],
            "search_shortcut": "^f",
            "play_enter_presses": 2,
        },
        "playlists": [
            {
                "id": DEFAULT_PLAYLIST_ID,
                "name": "Ado",
                "playlist_url": DEFAULT_SEARCH_URL,
                "client_uri": "",
                "tracks": default_tracks(),
            }
        ],
    }


def default_state() -> dict[str, Any]:
    return {
        "status": "idle",
        "mode": "background",
        "source": "netease",
        "playlist_id": DEFAULT_PLAYLIST_ID,
        "playlist_name": "Ado",
        "playlist_url": "",
        "selected_track": None,
        "selection_mode": "none",
        "playback_target": "none",
        "last_action": "idle",
        "last_message": "Music skill is ready.",
        "stage": {
            "enabled": False,
            "visual": "reserved",
            "asset": "image/Mask group.png",
            "effects": ["blink", "color_wave"],
        },
    }


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback.copy()
    if not isinstance(data, dict):
        return fallback.copy()
    return {**fallback, **data}


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_tracks(tracks: Any) -> list[dict[str, Any]]:
    if not isinstance(tracks, list):
        return default_tracks()

    normalized: list[dict[str, Any]] = []
    for item in tracks:
        if isinstance(item, str):
            normalized.append({"title": item, "artist": "Ado", "aliases": []})
        elif isinstance(item, dict) and str(item.get("title", "")).strip():
            normalized.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "artist": str(item.get("artist", "Ado")).strip() or "Ado",
                    "aliases": item.get("aliases") if isinstance(item.get("aliases"), list) else [],
                    "web_url": str(item.get("web_url", "")).strip(),
                    "client_uri": str(item.get("client_uri", "")).strip(),
                }
            )

    return normalized or default_tracks()


def normalize_playlists(config: dict[str, Any]) -> list[dict[str, Any]]:
    playlists = config.get("playlists")
    if not isinstance(playlists, list) or not playlists:
        playlists = [
            {
                "id": DEFAULT_PLAYLIST_ID,
                "name": "Ado",
                "playlist_url": config.get("ado_playlist_url") or DEFAULT_SEARCH_URL,
                "client_uri": config.get("ado_client_uri") or "",
                "tracks": config.get("ado_tracks") or default_tracks(),
            }
        ]

    normalized: list[dict[str, Any]] = []
    for item in playlists:
        if not isinstance(item, dict):
            continue
        playlist_id = str(item.get("id", "")).strip() or DEFAULT_PLAYLIST_ID
        playlist_url = str(item.get("playlist_url") or item.get("web_url") or "").strip()
        if not playlist_url and playlist_id == DEFAULT_PLAYLIST_ID:
            playlist_url = str(config.get("ado_playlist_url") or DEFAULT_SEARCH_URL)
        normalized.append(
            {
                "id": playlist_id,
                "name": str(item.get("name", playlist_id)).strip() or playlist_id,
                "playlist_url": playlist_url or DEFAULT_SEARCH_URL,
                "client_uri": str(item.get("client_uri", "")).strip(),
                "tracks": normalize_tracks(item.get("tracks")),
            }
        )

    return normalized or default_config()["playlists"]


def load_music_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, default_config())
    if not str(config.get("ado_playlist_url", "")).strip():
        config["ado_playlist_url"] = DEFAULT_SEARCH_URL
    if normalize_mode(str(config.get("default_mode", ""))) not in VALID_MODES:
        config["default_mode"] = "background"
    config["allow_web_fallback"] = bool(config.get("allow_web_fallback", False))
    config["automation"] = normalize_automation_config(config)
    config["preferred_playlist"] = str(config.get("preferred_playlist") or DEFAULT_PLAYLIST_ID).strip()
    config["playlists"] = normalize_playlists(config)
    return config


def load_music_state() -> dict[str, Any]:
    state = load_json(STATE_PATH, default_state())
    state["mode"] = normalize_mode(str(state.get("mode", "background")))
    state["stage"] = {
        **default_state()["stage"],
        **(state.get("stage") if isinstance(state.get("stage"), dict) else {}),
    }
    return state


def save_music_state(state: dict[str, Any]) -> dict[str, Any]:
    state["mode"] = normalize_mode(str(state.get("mode", "background")))
    state["stage"] = {
        **default_state()["stage"],
        **(state.get("stage") if isinstance(state.get("stage"), dict) else {}),
    }
    state["stage"]["enabled"] = state["mode"] == "stage"
    save_json(STATE_PATH, state)
    return state


def normalize_mode(mode: str) -> str:
    value = mode.strip().lower()
    if value in {"stage", "idle", "standby", "show", "舞台", "待机", "舞台模式"}:
        return "stage"
    return "background"


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def iter_known_track_terms(config: Optional[dict[str, Any]] = None) -> list[str]:
    config = config or load_music_config()
    terms: list[str] = []
    for playlist in config.get("playlists", []):
        for track in playlist.get("tracks", []):
            terms.append(str(track.get("title", "")).strip())
            terms.append(str(track.get("artist", "")).strip())
            aliases = track.get("aliases") if isinstance(track.get("aliases"), list) else []
            terms.extend(str(alias).strip() for alias in aliases)
    return [term for term in terms if term]


def contains_known_track_mention(message: str, config: Optional[dict[str, Any]] = None) -> bool:
    text = normalize_text(message)
    if not text:
        return False
    return any(normalize_text(term) in text for term in iter_known_track_terms(config))


def resolve_path(path_value: str) -> Optional[Path]:
    value = str(path_value or "").strip().strip('"')
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def is_dry_run(dry_run: bool = False) -> bool:
    return dry_run or os.environ.get("UTASAMA_MUSIC_DRY_RUN", "").strip() == "1"


def launch_netease(config: dict[str, Any], dry_run: bool = False) -> tuple[bool, str]:
    path = resolve_path(str(config.get("netease_path", "")))
    if path is None:
        return False, "config/music_player.json has no netease_path."
    if not path.exists():
        return False, f"netease_path does not exist: {path}"
    if is_dry_run(dry_run):
        return True, f"dry-run: would launch NetEase Cloud Music: {path}"

    try:
        subprocess.Popen(
            [str(path)],
            cwd=str(path.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        wait_seconds = float(config.get("launch_wait_seconds", 1.2) or 1.2)
        time.sleep(max(0.0, min(wait_seconds, 5.0)))
        return True, f"launched NetEase Cloud Music: {path}"
    except Exception as error:
        return False, f"failed to launch NetEase Cloud Music: {error}"


def open_target(target: str, dry_run: bool = False) -> tuple[bool, str]:
    value = str(target or "").strip()
    if not value:
        return False, "empty playback target"
    if is_dry_run(dry_run):
        return True, f"dry-run: would open target: {value}"

    try:
        if os.name == "nt":
            os.startfile(value)  # type: ignore[attr-defined]
        else:
            webbrowser.open(value)
        return True, f"opened target: {value}"
    except Exception as error:
        return False, f"failed to open target: {error}"


def send_media_key(action: str) -> tuple[bool, str]:
    key = MEDIA_KEYS.get(action)
    if key is None:
        return False, f"unsupported media key action: {action}"
    if os.name != "nt" or windll is None:
        return False, "media keys are currently implemented for Windows only."

    try:
        windll.user32.keybd_event(key, 0, 0, 0)
        windll.user32.keybd_event(key, 0, 2, 0)
        return True, f"sent Windows media key: {action}"
    except Exception as error:
        return False, f"failed to send media key: {error}"


def classify_music_action(message: str) -> str:
    text = message.lower()
    if any(word in text for word in ["上一首", "上首", "previous"]):
        return "previous"
    if any(word in text for word in ["下一首", "下首", "切歌", "next"]):
        return "next"
    if any(word in text for word in ["暂停", "停一下", "pause"]):
        return "pause"
    if any(word in text for word in ["继续", "恢复", "接着放", "resume"]):
        return "resume"
    if any(word in text for word in ["停止", "关闭音乐", "stop"]):
        return "stop"
    if any(word in text for word in ["舞台模式", "待机模式", "电脑待机", "stage"]):
        return "stage_mode"
    if any(word in text for word in ["后台模式", "聊天后台", "background"]):
        return "background_mode"

    direct_play_words = ["放歌", "听歌", "放点", "来点", "歌单", "ado"]
    launch_words = ["打开", "启动"]
    music_context_words = ["网易云", "音乐", "歌单", "ado"]
    song_play_words = ["播放", "听", "想听", "我要听", "我想听", "放", "放一首", "放首", "来一首"]
    if any(word in text for word in direct_play_words):
        return "play_ado_playlist"
    if ("播放" in text or any(word in text for word in launch_words)) and any(
        word in text for word in music_context_words
    ):
        return "play_ado_playlist"
    if contains_known_track_mention(message) and any(word in text for word in song_play_words):
        return "play_ado_playlist"
    if "播放" in text and extract_song_query(message):
        return "play_ado_playlist"
    return "state"


def extract_song_query(message: str) -> str:
    query = message
    for word in sorted(COMMAND_WORDS, key=len, reverse=True):
        query = query.replace(word, " ")
    query = re.sub(r"[，。！？、,.!?；;：:（）()\[\]【】\"'“”‘’]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    if query in {"", "首", "一首", "随机", "随便", "歌曲"}:
        return ""
    return query


def get_preferred_playlist(config: dict[str, Any]) -> dict[str, Any]:
    playlist_id = str(config.get("preferred_playlist") or DEFAULT_PLAYLIST_ID).strip()
    for playlist in config["playlists"]:
        if playlist["id"] == playlist_id:
            return playlist
    return config["playlists"][0]


def track_matches(track: dict[str, Any], query: str) -> bool:
    if not query:
        return False
    needle = normalize_text(query)
    candidates = [track.get("title", ""), track.get("artist", "")]
    candidates.extend(track.get("aliases", []) if isinstance(track.get("aliases"), list) else [])
    return any(needle in normalize_text(str(item)) or normalize_text(str(item)) in needle for item in candidates)


def choose_track(playlist: dict[str, Any], song_query: str = "") -> tuple[Optional[dict[str, Any]], str]:
    tracks = playlist.get("tracks") if isinstance(playlist.get("tracks"), list) else []
    if not tracks:
        return None, "playlist"
    if song_query:
        for track in tracks:
            if track_matches(track, song_query):
                return track, "requested"
    return random.choice(tracks), "random"


def build_search_url(track: dict[str, Any]) -> str:
    title = str(track.get("title", "")).strip()
    artist = str(track.get("artist", "Ado")).strip() or "Ado"
    return f"https://music.163.com/#/search/m/?s={quote_plus(f'{artist} {title}')}&type=1"


def track_public_view(track: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not track:
        return None
    return {
        "title": track.get("title", ""),
        "artist": track.get("artist", ""),
        "web_url": track.get("web_url", ""),
        "client_uri": track.get("client_uri", ""),
    }


def try_open_client_target(
    config: dict[str, Any],
    playlist: dict[str, Any],
    track: Optional[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[bool, str, list[str]]:
    warnings: list[str] = []
    launched, launch_message = launch_netease(config, dry_run=dry_run)
    if not launched:
        warnings.append(launch_message)
        return False, launch_message, warnings

    client_target = ""
    if track:
        client_target = str(track.get("client_uri", "")).strip()
    if not client_target:
        client_target = str(playlist.get("client_uri", "")).strip()
    if not client_target:
        warnings.append("No client_uri configured for selected track or playlist.")
        return False, "NetEase client opened, but no client_uri is configured for the selected track or playlist.", warnings

    opened, open_message = open_target(client_target, dry_run=dry_run)
    if not opened:
        warnings.append(open_message)
        return False, open_message, warnings
    return True, open_message, warnings


def try_ui_automation_target(
    config: dict[str, Any],
    track: Optional[dict[str, Any]],
    song_query: str = "",
    dry_run: bool = False,
) -> tuple[bool, str, list[str]]:
    warnings: list[str] = []
    result = automate_netease_search_play(
        resolve_path(str(config.get("netease_path", ""))),
        config,
        track,
        song_query=song_query,
        dry_run=dry_run,
    )
    if not result.get("ok"):
        warnings.append(str(result.get("message", "NetEase UI automation failed.")))
        return False, str(result.get("message", "NetEase UI automation failed.")), warnings
    return True, str(result.get("message", "NetEase UI automation finished.")), warnings


def open_web_fallback(
    playlist: dict[str, Any],
    track: Optional[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[bool, str, str]:
    if track and str(track.get("web_url", "")).strip():
        target = str(track["web_url"]).strip()
    elif track:
        target = build_search_url(track)
    else:
        target = str(playlist.get("playlist_url") or DEFAULT_SEARCH_URL)

    opened, message = open_target(target, dry_run=dry_run)
    return opened, message, target


def should_handle_music_message(message: str, route: dict[str, Any]) -> bool:
    action = classify_music_action(message)
    if action == "state":
        return False

    text = message.lower()
    active_agent = str(route.get("active_agent", ""))
    preferred_skills = route.get("preferred_skills", [])
    has_music_context = any(word in text for word in ["网易云", "音乐", "歌", "播放", "ado", "bgm"])
    if action in {"pause", "resume", "next", "previous", "stop"}:
        current_status = str(load_music_state().get("status", "idle"))
        return (
            active_agent == "music-agent"
            or "music-player" in preferred_skills
            or has_music_context
            or current_status in {"playing", "paused"}
        )

    return True


def build_skill_reply(result: dict[str, Any]) -> str:
    action = result.get("action")
    ok = bool(result.get("ok"))
    state = result.get("state", {})
    track = state.get("selected_track") if isinstance(state, dict) else None
    mode_text = "舞台待机模式" if state.get("mode") == "stage" else "聊天后台模式"

    if action == "play_ado_playlist" and ok:
        if isinstance(track, dict) and track.get("title"):
            target_text = f"{track.get('artist', 'Ado')} 的《{track.get('title')}》"
        else:
            target_text = "Ado 歌单"
        via = (
            "网易云客户端自动搜索"
            if state.get("playback_target") == "client_automation"
            else "网易云客户端"
            if state.get("playback_target") == "client"
            else "网页兜底"
        )
        return f"好呀，我帮你抽到了 {target_text}。现在用{via}打开，模式是{mode_text}。"
    if action == "play_ado_playlist" and state.get("playback_target") == "client_pending":
        return (
            "我已经尝试打开网易云客户端了，但现在还没有配置可直接定位歌曲的 client_uri，"
            "所以不会再打开网页端。要让我自动点歌，需要补客户端深链或接入 UI 自动化。"
        )
    if action == "stage_mode":
        return "舞台待机模式已经预留好了。之后这里会接人物头贴眨眼和音乐波浪背景。"
    if action == "background_mode":
        return "已经切回聊天后台模式啦，音乐可以在后面轻轻放着。"
    if action == "pause" and ok:
        return "嗯，我先把音乐暂停一下。"
    if action == "resume" and ok:
        return "继续播放啦。"
    if action == "next" and ok:
        return "我切到下一首了。"
    if action == "previous" and ok:
        return "我切回上一首了。"
    if action == "stop" and ok:
        return "音乐先停下来了。"

    return f"音乐 skill 已经收到指令，但还需要检查配置：{result.get('message', 'unknown error')}"


def run_music_skill(
    action: str,
    playlist_url: Optional[str] = None,
    mode: Optional[str] = None,
    song_query: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    config = load_music_config()
    state = load_music_state()
    warnings: list[str] = []
    ok = True
    effective_dry_run = is_dry_run(dry_run)

    if mode:
        state["mode"] = normalize_mode(mode)
    elif state.get("mode") not in VALID_MODES:
        state["mode"] = normalize_mode(str(config.get("default_mode", "background")))

    if action in {"stage_mode", "background_mode"}:
        state["mode"] = "stage" if action == "stage_mode" else "background"
        state["last_action"] = action
        state["last_message"] = "mode switched"
        if effective_dry_run:
            state["dry_run"] = True
        else:
            save_music_state(state)
        return {
            "ok": True,
            "action": action,
            "message": state["last_message"],
            "state": state,
            "warnings": warnings,
        }

    if action == "play_ado_playlist":
        playlist = get_preferred_playlist(config)
        if playlist_url:
            playlist = {**playlist, "playlist_url": playlist_url}
        track, selection_mode = choose_track(playlist, song_query or "")

        client_ok, client_message, client_warnings = try_open_client_target(
            config,
            playlist,
            track,
            dry_run=effective_dry_run,
        )
        warnings.extend(client_warnings)

        playback_target = "client"
        playback_url = ""
        message = client_message
        if not client_ok:
            automation_ok, automation_message, automation_warnings = try_ui_automation_target(
                config,
                track,
                song_query=song_query or "",
                dry_run=effective_dry_run,
            )
            warnings.extend(automation_warnings)
            if automation_ok:
                ok = True
                playback_target = "client_automation"
                message = automation_message
            elif config.get("allow_web_fallback", False):
                web_ok, web_message, playback_url = open_web_fallback(playlist, track, dry_run=effective_dry_run)
                ok = web_ok
                playback_target = "web" if web_ok else "error"
                message = web_message
                if not web_ok:
                    warnings.append(web_message)
            else:
                ok = False
                playback_target = "client_pending"
                message = automation_message or client_message

        state.update(
            {
                "status": "playing" if ok else playback_target,
                "source": "netease",
                "playlist_id": playlist.get("id", DEFAULT_PLAYLIST_ID),
                "playlist_name": playlist.get("name", "Ado"),
                "playlist_url": playlist.get("playlist_url", ""),
                "selected_track": track_public_view(track),
                "selection_mode": selection_mode,
                "playback_target": playback_target,
                "playback_url": playback_url,
                "last_action": action,
                "last_message": message if ok else "; ".join(warnings),
            }
        )
        if effective_dry_run:
            state["dry_run"] = True
        else:
            save_music_state(state)
        return {
            "ok": ok,
            "action": action,
            "message": state["last_message"],
            "state": state,
            "warnings": warnings,
        }

    if action in MEDIA_KEYS:
        sent, message = send_media_key(action)
        ok = sent
        if not sent:
            warnings.append(message)
        if action == "pause" and sent:
            state["status"] = "paused"
        elif action == "resume" and sent:
            state["status"] = "playing"
        elif action == "stop" and sent:
            state["status"] = "stopped"
        state["last_action"] = action
        state["last_message"] = message
        save_music_state(state)
        return {
            "ok": ok,
            "action": action,
            "message": message,
            "state": state,
            "warnings": warnings,
        }

    state["last_action"] = "state"
    state["last_message"] = "state returned"
    save_music_state(state)
    return {
        "ok": True,
        "action": "state",
        "message": state["last_message"],
        "state": state,
        "warnings": warnings,
    }


def handle_music_message(message: str, route: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    action = classify_music_action(message)
    song_query = extract_song_query(message) if action == "play_ado_playlist" else ""
    result = run_music_skill(action, song_query=song_query, dry_run=dry_run)
    result["reply_text"] = build_skill_reply(result)
    result["handled_by"] = "music-agent"
    result["preferred_skill"] = "music-player"
    result["song_query"] = song_query
    return result
