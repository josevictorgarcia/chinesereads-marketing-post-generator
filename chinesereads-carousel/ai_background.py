#!/usr/bin/env python3
"""
ai_background.py — fondos fotorrealistas con una API de imagen
===============================================================

Claude no genera imágenes. Este script llama a una API que sí, y deja el
resultado en assets/backgrounds/ listo para el generador de carruseles.

    export OPENAI_API_KEY=sk-...
    python ai_background.py "chinatown alley at night"
    python ai_background.py --preset chinatown_night --count 3
    python ai_background.py --preset tea_hills --quality high

Coste aproximado con gpt-image-1-mini: menos de un céntimo por imagen.
"""

from __future__ import annotations

import argparse
import base64
import os
import random
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Falta requests:  pip install -r requirements-ai.txt")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).parent

# El sufijo importa tanto como el tema: sin él salen imágenes con el motivo
# centrado y de frente, que es justo donde va el título y donde estorba.
STYLE = ("photorealistic, shot on a 35mm lens, natural available light, "
         "shallow depth of field, uncluttered composition with open space in "
         "the upper middle of the frame, no text, no watermark, no people "
         "facing the camera")

PRESETS = {
    "chinatown_night": "a narrow chinatown alley at night, red paper lanterns "
                       "strung overhead, warm glow from shop signs, wet cobblestones",
    "chinatown_day":   "a chinatown street in the afternoon, red and gold shopfronts, "
                       "hanging signs in Chinese characters, quiet and sunlit",
    "tea_hills":       "terraced green tea fields on a misty hillside in southern China, "
                       "early morning light",
    "old_town":        "a quiet old town lane in China, grey brick walls, "
                       "curved tiled rooftops, a red door, soft overcast light",
    "night_market":    "a Chinese night market from a distance, warm lantern light, "
                       "steam rising, bokeh lights out of focus",
    "calligraphy":     "close-up of an ink brush and rice paper on a dark wooden desk, "
                       "soft side light, minimal",
}


def generate(prompt: str, quality: str, out: Path) -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        sys.exit("Falta OPENAI_API_KEY. Si prefieres otro proveedor, cambia esta "
                 "función: sólo tiene que devolver bytes PNG cuadrados.")

    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": os.getenv("IMAGE_MODEL", "gpt-image-1-mini"),
              "prompt": f"{prompt}. {STYLE}",
              "size": "1024x1024",
              "quality": quality,
              "n": 1},
        timeout=180)

    if r.status_code != 200:
        sys.exit(f"Error {r.status_code}: {r.text[:400]}")

    payload = r.json()["data"][0]
    if "b64_json" in payload:
        out.write_bytes(base64.b64decode(payload["b64_json"]))
    else:
        out.write_bytes(requests.get(payload["url"], timeout=120).content)


def main():
    ap = argparse.ArgumentParser(description="Genera fondos con una API de imagen")
    ap.add_argument("prompt", nargs="?", help="descripción libre de la escena")
    ap.add_argument("--preset", choices=list(PRESETS))
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--quality", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--outdir", default="assets/backgrounds")
    ap.add_argument("--list", action="store_true", help="ver los presets")
    args = ap.parse_args()

    if args.list:
        for k, v in PRESETS.items():
            print(f"  {k:<18} {v[:66]}…")
        return

    prompt = args.prompt or (PRESETS[args.preset] if args.preset else None)
    if not prompt:
        ap.error("indica un prompt o un --preset (o usa --list)")

    out = ROOT / args.outdir
    out.mkdir(parents=True, exist_ok=True)
    tag = args.preset or "custom"

    for i in range(args.count):
        path = out / f"ai_{tag}_{int(time.time())}_{random.randint(100, 999)}.png"
        print(f"  generando {i + 1}/{args.count}…", flush=True)
        generate(prompt, args.quality, path)
        print(f"✓ {path.relative_to(ROOT)}")

    print("\nRevisa que no haya salido texto raro incrustado antes de usarlas.")


if __name__ == "__main__":
    main()
