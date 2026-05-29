from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from desktop.ui.main_window import MainWindow


def run_desktop_client(
    api_base_url: str = "http://127.0.0.1:8000",
    smoke: bool = False,
) -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    app = QApplication(sys.argv)
    window = MainWindow(api_base_url=api_base_url, skip_initial_requests=smoke)
    window.show()
    if smoke:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(600, app.quit)
    return app.exec()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the UtaSama PySide6 desktop client.")
    parser.add_argument(
        "--api-base-url",
        default=os.environ.get("UTASAMA_API_BASE_URL", "http://127.0.0.1:8000"),
        help="FastAPI backend base URL.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Start and close the window quickly for smoke testing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_desktop_client(api_base_url=args.api_base_url, smoke=args.smoke)


if __name__ == "__main__":
    raise SystemExit(main())
