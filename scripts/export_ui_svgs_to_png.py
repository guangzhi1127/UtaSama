from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "frontend" / "assets" / "ui"

EXPORTS = [
    ("uta-irregular-chat-frame.svg", "uta-irregular-chat-frame.png", QSize(1600, 980)),
]


def export_svg_to_png(svg_name: str, png_name: str, size: QSize) -> None:
    svg_path = ASSET_DIR / svg_name
    png_path = ASSET_DIR / png_name
    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG: {svg_path}")

    image = QImage(size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    try:
        renderer.render(painter)
    finally:
        painter.end()

    if not image.save(str(png_path), "PNG"):
        raise RuntimeError(f"Failed to save PNG: {png_path}")


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    for svg_name, png_name, size in EXPORTS:
        export_svg_to_png(svg_name, png_name, size)
        print(f"exported {png_name}")
    app.quit()


if __name__ == "__main__":
    main()
