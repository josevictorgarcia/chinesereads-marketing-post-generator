#!/usr/bin/env python3
"""
doctor.py — comprueba qué está listo y qué falta

    python doctor.py

No modifica nada. Sólo mira dependencias, assets y variables de entorno,
y te dice qué herramientas puedes usar ahora mismo.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).parent
OK, NO, WARN = "  ✓", "  ✗", "  ·"


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def has_file(rel: str) -> bool:
    return (ROOT / rel).exists()


def has_env(*keys: str) -> bool:
    return all(os.getenv(k) for k in keys)


def section(title: str, checks: list[tuple[bool, str]], hint: str) -> bool:
    ready = all(c[0] for c in checks)
    print(f"\n{'✓' if ready else '✗'} {title}")
    for ok, label in checks:
        print(f"{OK if ok else NO} {label}")
    if not ready:
        print(f"{WARN} {hint}")
    return ready


def in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def main():
    print("Chinese Reads — estado del montaje")
    print("=" * 46)
    print(f"\nPython {sys.version.split()[0]} — {sys.executable}")
    if in_venv():
        print(f"{OK} entorno virtual activo")
    else:
        print(f"{NO} sin entorno virtual")
        print(f"{WARN} python3 -m venv .venv && source .venv/bin/activate")
        print(f"{WARN} sin él, pip puede fallar con 'externally-managed-environment'")

    core = section("generate_carousel.py — generar carruseles", [
        (has_module("PIL"), "Pillow instalado"),
        (has_module("fontTools"), "fontTools instalado (opcional pero recomendado)"),
        (has_file("assets/content_bg.png"), "assets/content_bg.png"),
        (has_file("assets/final_slide.png"), "assets/final_slide.png"),
        (has_file("assets/logo.png"), "assets/logo.png"),
        (any((ROOT / "assets/backgrounds").glob("*"))
         if (ROOT / "assets/backgrounds").exists() else False,
         "al menos una foto en assets/backgrounds/"),
    ], "pip install -r requirements.txt")

    section("make_background.py — fondos por código", [
        (has_module("PIL"), "Pillow instalado"),
    ], "pip install -r requirements.txt")

    section("write_post.py — textos con Claude", [
        (has_module("anthropic"), "SDK anthropic instalado"),
        (has_env("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY"),
    ], "pip install -r requirements-ai.txt  +  clave en .env")

    section("ai_background.py — fondos por IA", [
        (has_module("requests"), "requests instalado"),
        (has_env("OPENAI_API_KEY"), "OPENAI_API_KEY"),
    ], "pip install -r requirements-ai.txt  +  clave en .env")

    pub = section("publish.py — publicar en redes", [
        (has_module("boto3"), "boto3 instalado"),
        (has_env("R2_ENDPOINT", "R2_ACCESS_KEY_ID",
                 "R2_SECRET_ACCESS_KEY", "R2_BUCKET"), "credenciales de R2"),
        (has_env("CDN_BASE_URL"), "CDN_BASE_URL"),
        (has_env("IG_USER_ID", "IG_ACCESS_TOKEN"), "credenciales de Instagram"),
        (has_env("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET",
                 "TIKTOK_REFRESH_TOKEN"), "credenciales de TikTok"),
    ], "ver SETUP.md — es opcional, puedes subir a mano")

    cdn = os.getenv("CDN_BASE_URL", "")
    if cdn and ".r2.dev" in cdn:
        print("\n  ⚠  CDN_BASE_URL apunta a un dominio *.r2.dev. TikTok no lo puede "
              "verificar\n     y rechazará las publicaciones. Usa un subdominio tuyo.")

    print("\n" + "=" * 46)
    if core:
        print("Puedes generar carruseles. " +
              ("También publicar por API." if pub else
               "Para publicar: sube las imágenes a mano o configura publish.py."))
    else:
        print("Falta lo básico. Empieza por: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
