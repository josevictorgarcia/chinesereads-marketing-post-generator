#!/usr/bin/env python3
"""
write_post.py — genera el JSON de un post con Claude, listo para el generador
=============================================================================

    export ANTHROPIC_API_KEY=sk-ant-...
    pip install anthropic

    python write_post.py "characters that share the 青 phonetic component"
    python write_post.py "HSK3 verbs about travelling" --slides 6 --bg autumn_hutong.jpg
    python write_post.py "..." --build          # genera el JSON y el carrusel de una

Sale un fichero en posts/<slug>.json que puedes revisar y editar antes de renderizar.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).parent
MODEL = "claude-sonnet-4-6"

SYSTEM = """You write Instagram carousel content for Chinese Reads, a web app for \
learning Chinese through reading (chinesereads.com). The audience is intermediate \
learners of Mandarin; captions are in English.

House style:
- Cover title: a hook, a question or a surprising claim. Max 55 characters. Plain \
  English, no emoji, no hashtags.
- Cover subtitle: a short swipe prompt. Max 40 characters.
- Each slide teaches ONE item: a character, a word or a short phrase.
- "meaning" is short: max 32 characters, use " / " to separate senses.
- "pinyin" must carry correct tone marks (qīng, qíng, qǐng, qìng), lowercase.
- The caption is 2-3 sentences that add real insight — the kind of thing a learner \
  would not get from a dictionary. No filler, no "did you know".

Return ONLY a JSON object, no markdown fences, no preamble, with this shape:
{"slug": "...", "cover": {"title": "...", "subtitle": "..."},
 "slides": [{"hanzi": "...", "pinyin": "...", "meaning": "..."}],
 "caption": "...", "hashtags": ["#...", "..."]}"""


def pick_background() -> str:
    """Elige una foto al azar de assets/backgrounds/."""
    d = ROOT / "assets" / "backgrounds"
    imgs = [p for p in d.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    if not imgs:
        sys.exit("No hay fotos en assets/backgrounds/ — añade alguna antes de seguir.")
    return f"assets/backgrounds/{random.choice(imgs).name}"


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "post"


def generate(topic: str, n_slides: int) -> dict:
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("Falta el SDK anthropic:\n    pip install -r requirements-ai.txt")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Falta ANTHROPIC_API_KEY en el entorno.")

    client = Anthropic()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user",
                   "content": f"Topic: {topic}\nNumber of content slides: {n_slides}"}],
    )

    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"Claude no devolvió JSON válido: {e}\n---\n{text[:600]}")


def main():
    ap = argparse.ArgumentParser(description="Escribe un post con Claude")
    ap.add_argument("topic", help="tema del carrusel")
    ap.add_argument("--slides", type=int, default=5, help="número de slides de contenido")
    ap.add_argument("--bg", help="nombre del fichero en assets/backgrounds/ (si no, aleatorio)")
    ap.add_argument("--build", action="store_true", help="renderizar el carrusel al terminar")
    args = ap.parse_args()

    post = generate(args.topic, args.slides)

    post["slug"] = slugify(post.get("slug") or args.topic)
    post.setdefault("cover", {})["background"] = (
        f"assets/backgrounds/{args.bg}" if args.bg else pick_background()
    )
    post.setdefault("cta", "Read real Chinese texts for free at chinesereads.com 📖 (link in bio)")
    post.setdefault("include_final", True)

    out = ROOT / "posts" / f"{post['slug']}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(post, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ {out.relative_to(ROOT)}")
    print(f"  portada:  {post['cover']['title']}")
    for s in post["slides"]:
        print(f"  {s['hanzi']}  {s['pinyin']:<10} {s['meaning']}")
    print("\nRevísalo y ajusta lo que haga falta antes de renderizar.")

    if args.build:
        subprocess.run([sys.executable, str(ROOT / "generate_carousel.py"), str(out)], check=True)


if __name__ == "__main__":
    main()
