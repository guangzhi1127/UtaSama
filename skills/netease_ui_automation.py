from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional


DEFAULT_AUTOMATION_CONFIG = {
    "enabled": True,
    "backend": "uia",
    "window_title_regex": ".*(网易云音乐|NetEase|CloudMusic|云音乐).*",
    "connect_timeout_seconds": 8,
    "launch_wait_seconds": 2.5,
    "try_find_search_edit": True,
    "search_edit_name_keywords": ["搜索", "Search"],
    "search_shortcut": "^f",
    "search_focus_wait_seconds": 0.5,
    "result_wait_seconds": 1.8,
    "play_enter_presses": 2,
    "play_enter_interval_seconds": 0.45,
    "search_query_template": "{artist} {title}",
}


def normalize_automation_config(config: dict[str, Any]) -> dict[str, Any]:
    candidate = config.get("automation") if isinstance(config.get("automation"), dict) else {}
    return {**DEFAULT_AUTOMATION_CONFIG, **candidate}


def build_search_query(track: Optional[dict[str, Any]], song_query: str = "", template: str = "{artist} {title}") -> str:
    if track:
        artist = str(track.get("artist", "Ado")).strip() or "Ado"
        title = str(track.get("title", "")).strip()
        if title:
            return template.format(artist=artist, title=title).strip()
    return f"Ado {song_query}".strip() if song_query else "Ado"


def set_clipboard_text(text: str) -> None:
    import win32clipboard
    import win32con

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def connect_or_start_window(netease_path: Path, automation: dict[str, Any]):
    from pywinauto import Application

    backend = str(automation.get("backend") or "uia")
    timeout = float(automation.get("connect_timeout_seconds") or 8)
    title_re = str(automation.get("window_title_regex") or DEFAULT_AUTOMATION_CONFIG["window_title_regex"])

    app = Application(backend=backend)
    try:
        app.connect(path=str(netease_path), timeout=timeout)
    except Exception:
        try:
            app.connect(title_re=title_re, timeout=timeout)
        except Exception:
            app = Application(backend=backend).start(str(netease_path))
            time.sleep(float(automation.get("launch_wait_seconds") or 2.5))
            try:
                app.connect(path=str(netease_path), timeout=timeout)
            except Exception:
                app.connect(title_re=title_re, timeout=timeout)

    window = app.top_window()
    try:
        window.restore()
    except Exception:
        pass
    window.set_focus()
    return window


def focus_search_input(window, automation: dict[str, Any]) -> bool:
    if not automation.get("try_find_search_edit", True):
        return False

    keywords = automation.get("search_edit_name_keywords")
    if not isinstance(keywords, list) or not keywords:
        keywords = DEFAULT_AUTOMATION_CONFIG["search_edit_name_keywords"]

    try:
        edits = window.descendants(control_type="Edit")
    except Exception:
        return False

    for edit in edits:
        try:
            name = edit.window_text() or ""
            if any(str(keyword).lower() in name.lower() for keyword in keywords):
                edit.set_focus()
                return True
        except Exception:
            continue

    if edits:
        try:
            edits[0].set_focus()
            return True
        except Exception:
            return False

    return False


def automate_netease_search_play(
    netease_path: Optional[Path],
    config: dict[str, Any],
    track: Optional[dict[str, Any]],
    song_query: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    automation = normalize_automation_config(config)
    if not automation.get("enabled", True):
        return {"ok": False, "message": "NetEase UI automation is disabled.", "query": ""}
    if netease_path is None:
        return {"ok": False, "message": "netease_path is not configured.", "query": ""}
    if not netease_path.exists():
        return {"ok": False, "message": f"netease_path does not exist: {netease_path}", "query": ""}

    query = build_search_query(
        track,
        song_query=song_query,
        template=str(automation.get("search_query_template") or "{artist} {title}"),
    )
    if dry_run:
        return {"ok": True, "message": f"dry-run: would search and play in NetEase client: {query}", "query": query}

    try:
        window = connect_or_start_window(netease_path, automation)
        from pywinauto import keyboard

        if not focus_search_input(window, automation):
            keyboard.send_keys(str(automation.get("search_shortcut") or "^f"))
        time.sleep(float(automation.get("search_focus_wait_seconds") or 0.5))
        set_clipboard_text(query)
        keyboard.send_keys("^a")
        keyboard.send_keys("^v")
        keyboard.send_keys("{ENTER}")
        time.sleep(float(automation.get("result_wait_seconds") or 1.8))

        presses = int(automation.get("play_enter_presses") or 2)
        interval = float(automation.get("play_enter_interval_seconds") or 0.45)
        for _ in range(max(1, presses)):
            keyboard.send_keys("{ENTER}")
            time.sleep(max(0.05, interval))

        return {"ok": True, "message": f"searched and triggered first result: {query}", "query": query}
    except Exception as error:
        return {"ok": False, "message": f"NetEase UI automation failed: {error}", "query": query}
