from __future__ import annotations

import argparse
import atexit
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_TIMEOUT = 45
BACKEND_LOG_PATH = PROJECT_ROOT / "logs" / "launcher-backend.log"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_base_url(host: str, port: int) -> str:
    return f"http://{host}:{port}"


def check_backend_health(base_url: str, timeout: float = 1.5) -> bool:
    try:
        response = requests.get(f"{base_url}/health", timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return False

    return isinstance(data, dict) and data.get("status") == "ok"


def tail_log(path: Path, max_chars: int = 1600) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text[-max_chars:]


def start_backend(host: str, port: int) -> tuple[subprocess.Popen, object]:
    BACKEND_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_file = BACKEND_LOG_PATH.open("a", encoding="utf-8")
    log_file.write("\n\n=== UtaSama backend launch ===\n")
    log_file.flush()

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    return process, log_file


def wait_for_backend(
    base_url: str,
    process: Optional[subprocess.Popen],
    timeout_seconds: int,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if check_backend_health(base_url):
            return

        if process is not None and process.poll() is not None:
            log_tail = tail_log(BACKEND_LOG_PATH)
            raise RuntimeError(
                "后端启动后立即退出。请查看 logs/launcher-backend.log。\n"
                + (f"\n最近日志：\n{log_tail}" if log_tail else "")
            )

        time.sleep(0.6)

    raise TimeoutError(f"等待后端启动超时：{base_url}/health")


def stop_backend(process: Optional[subprocess.Popen], log_file: Optional[object]) -> None:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    if log_file is not None:
        try:
            log_file.close()
        except Exception:
            pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="One-click launcher for UtaSama desktop client.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Backend host.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Backend port.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="Seconds to wait for backend startup.",
    )
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Do not start backend; only open the desktop client.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Start backend and desktop briefly for smoke testing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_url = build_base_url(args.host, args.port)
    backend_process: Optional[subprocess.Popen] = None
    backend_log_file = None
    owns_backend = False

    print(f"[UtaSama] 后端地址：{base_url}")

    try:
        if args.no_backend:
            print("[UtaSama] 已跳过后端启动。")
            wait_for_backend(base_url, None, timeout_seconds=3)
        elif check_backend_health(base_url):
            print("[UtaSama] 检测到后端已在线，直接打开客户端。")
        else:
            print("[UtaSama] 正在启动 FastAPI 后端...")
            backend_process, backend_log_file = start_backend(args.host, args.port)
            owns_backend = True
            wait_for_backend(base_url, backend_process, timeout_seconds=args.timeout)
            print("[UtaSama] 后端启动成功。")

        if owns_backend:
            atexit.register(stop_backend, backend_process, backend_log_file)

        os.environ["UTASAMA_API_BASE_URL"] = base_url
        from desktop.app import run_desktop_client

        return run_desktop_client(api_base_url=base_url, smoke=args.smoke)
    except KeyboardInterrupt:
        print("\n[UtaSama] 已取消启动。")
        return 130
    except Exception as error:
        print(f"[UtaSama] 启动失败：{error}")
        return 1
    finally:
        if owns_backend:
            stop_backend(backend_process, backend_log_file)


if __name__ == "__main__":
    raise SystemExit(main())
