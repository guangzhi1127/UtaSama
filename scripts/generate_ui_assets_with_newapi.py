from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "image"
UI_DIR = ROOT / "frontend" / "assets" / "ui"
TMP_DIR = ROOT / "tmp" / "imagegen_ui"

DEFAULT_BASE_URL = "http://y.ainiaini.xyz/v1"
DEFAULT_MODEL = "gpt-image-2"
CHROMA_KEY = (0, 255, 0)


@dataclass(frozen=True)
class AssetSpec:
    name: str
    output_name: str
    prompt: str
    size: tuple[int, int]


ASSET_SPECS = [
    AssetSpec(
        name="irregular-frame",
        output_name="uta-irregular-chat-frame.png",
        size=(1600, 980),
        prompt=(
            "Create a transparent-style anime game UI chat frame inspired by the reference character's split hair design. "
            "The frame must be an irregular rounded rectangle border only, with a large empty center for a chat app. "
            "Left half red-pink hair-like border with a few curved hair bang shapes near the top; right half ivory-white hair-like border "
            "with matching curved bang shapes; thin gold outline tracing the whole frame; subtle gold highlight strokes prepared for future flowing glow animation. "
            "No text, no logo, no face, no full character body, no filled center panel. "
            "Use a perfectly flat pure chroma green background #00FF00, keep the inside of the frame also chroma green so it can be removed to transparency."
        ),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate UtaSama UI assets through a NewAPI-compatible image endpoint.")
    parser.add_argument("--base-url", default=os.environ.get("NEWAPI_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.environ.get("NEWAPI_IMAGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--quality", default="standard")
    parser.add_argument("--style", default="vivid")
    parser.add_argument("--reference-limit", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def require_key() -> str:
    api_key = os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NEWAPI_API_KEY. Set it in the shell before running this script.")
    return api_key


def image_to_data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def selected_reference_images(limit: int) -> list[Path]:
    preferred = [
        "f16681575fca31106bbd64ad574579ac.jpg",
        "40fe591411ffa6d103109cc19e506969.jpg",
        "d4cca5491344233b5ea14dfe7755c51b.jpg",
        "038329dae66a23c40416a90506f5706e.jpg",
        "8508f69e79cc16f3b6aa75acce51f335.jpg",
    ]
    paths = [REFERENCE_DIR / name for name in preferred if (REFERENCE_DIR / name).exists()]
    return paths[:limit]


def post_json(url: str, api_key: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:1200]}")
    return response.json()


def extract_image_bytes(data: dict[str, Any], output_dir: Path, name: str) -> bytes:
    candidates: list[str] = []

    for item in data.get("data") or []:
        if isinstance(item, dict):
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                candidates.append(str(item["url"]))

    for choice in data.get("choices") or []:
        message = choice.get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            candidates.extend(re.findall(r"https?://[^\s)'\"]+", content))
            data_urls = re.findall(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", content)
            if data_urls:
                return base64.b64decode(data_urls[0])
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    image_url = part.get("image_url") or {}
                    if isinstance(image_url, dict) and image_url.get("url"):
                        candidates.append(str(image_url["url"]))
                    if part.get("b64_json"):
                        return base64.b64decode(part["b64_json"])

    for url in candidates:
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                return response.read()
        except Exception:
            continue

    debug_path = output_dir / f"{name}.response.json"
    debug_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    raise RuntimeError(f"No image URL or base64 image found. Saved response to {debug_path}")


def call_images_api(base_url: str, api_key: str, model: str, spec: AssetSpec, args: argparse.Namespace) -> bytes:
    url = f"{base_url.rstrip('/')}/images/generations"
    payload = {
        "model": model,
        "prompt": spec.prompt,
        "size": "1024x1024",
        "quality": args.quality,
        "style": args.style,
        "n": 1,
        "response_format": "b64_json",
    }
    data = post_json(url, api_key, payload)
    return extract_image_bytes(data, TMP_DIR, spec.name)


def call_chat_api(base_url: str, api_key: str, model: str, spec: AssetSpec, args: argparse.Namespace) -> bytes:
    url = f"{base_url.rstrip('/')}/chat/completions"
    references = selected_reference_images(args.reference_limit)
    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                spec.prompt
                + "\nUse the attached reference images only for character colors and motif: red/white split hair and idol-stage anime UI feeling."
                + "\nReturn the generated image directly or an image URL. Do not return explanations."
            ),
        }
    ]
    for path in references:
        content.append({"type": "image_url", "image_url": {"url": image_to_data_url(path)}})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "size": "1024x1024",
        "quality": args.quality,
        "style": args.style,
        "n": 1,
    }
    data = post_json(url, api_key, payload)
    return extract_image_bytes(data, TMP_DIR, spec.name)


def remove_chroma_key(image_path: Path, output_path: Path, target_size: tuple[int, int]) -> None:
    image = Image.open(image_path).convert("RGBA")
    image = ImageOps.contain(image, target_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((target_size[0] - image.width) // 2, (target_size[1] - image.height) // 2))
    rgb = canvas.convert("RGB")

    key = Image.new("RGB", target_size, CHROMA_KEY)
    diff = ImageChops.difference(rgb, key).convert("L")
    alpha = diff.point(lambda value: 0 if value < 58 else min(255, int((value - 58) * 2.2)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))

    r, g, b, _ = canvas.split()
    rgba = Image.merge("RGBA", (r, g, b, alpha))

    # Slightly despill green edges left by the chroma background.
    pixels = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            rr, gg, bb, aa = pixels[x, y]
            if aa and gg > rr * 1.18 and gg > bb * 1.18:
                pixels[x, y] = (rr, int((rr + bb) / 2), bb, aa)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(output_path)


def create_flow_mask(frame_path: Path, mask_path: Path) -> None:
    frame = Image.open(frame_path).convert("RGBA")
    r, g, b, a = frame.split()
    # Gold/yellow parts are useful as a future flowing-highlight mask.
    gold_mask = Image.new("L", frame.size, 0)
    src = frame.load()
    dst = gold_mask.load()
    for y in range(frame.height):
        for x in range(frame.width):
            rr, gg, bb, aa = src[x, y]
            if aa > 16 and rr > 150 and gg > 105 and bb < 120:
                dst[x, y] = min(255, aa + 40)

    gold_mask = gold_mask.filter(ImageFilter.GaussianBlur(1.2))
    glow = Image.new("RGBA", frame.size, (255, 226, 128, 0))
    glow.putalpha(ImageEnhance.Contrast(gold_mask).enhance(1.5))
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    glow.save(mask_path)


def main() -> int:
    args = parse_args()
    api_key = require_key()
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    UI_DIR.mkdir(parents=True, exist_ok=True)

    for spec in ASSET_SPECS:
        print(f"generating {spec.name}...")
        if args.dry_run:
            continue

        raw_path = TMP_DIR / f"{spec.name}.raw.png"
        try:
            image_bytes = call_chat_api(args.base_url, api_key, args.model, spec, args)
        except Exception as chat_error:
            print(f"chat endpoint failed for {spec.name}: {chat_error}", file=sys.stderr)
            image_bytes = call_images_api(args.base_url, api_key, args.model, spec, args)

        raw_path.write_bytes(image_bytes)
        output_path = UI_DIR / spec.output_name
        remove_chroma_key(raw_path, output_path, spec.size)
        print(f"saved {output_path.relative_to(ROOT)}")
        time.sleep(1)

    create_flow_mask(UI_DIR / "uta-irregular-chat-frame.png", UI_DIR / "uta-irregular-chat-frame-flow-mask.png")
    print("saved frontend/assets/ui/uta-irregular-chat-frame-flow-mask.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
