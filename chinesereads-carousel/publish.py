#!/usr/bin/env python3
"""
publish.py — sube el carrusel y lo publica por API REST
========================================================

    python publish.py output/qing                 # Instagram + TikTok
    python publish.py output/qing --only instagram
    python publish.py output/qing --dry-run       # sube y enseña el payload, no publica

Flujo: R2 (o cualquier bucket S3) -> URLs públicas -> Graph API + TikTok Content Posting API.

Ambas plataformas descargan las imágenes desde una URL pública, así que el bucket
no es opcional. TikTok además exige que el dominio esté verificado como tuyo, por
eso conviene servir desde un subdominio propio (cdn.chinesereads.com) y no desde
la URL r2.dev que te da Cloudflare por defecto.

Configuración en .env — ver .env.example
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Faltan dependencias del publicador:\n"
                     "    pip install -r requirements-publish.txt")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GRAPH = os.getenv("GRAPH_BASE", "https://graph.instagram.com/v23.0")
TIKTOK = "https://open.tiktokapis.com/v2"
TIMEOUT = 60


def env(key: str, required: bool = True) -> str:
    v = os.getenv(key, "")
    if required and not v:
        sys.exit(f"Falta {key} en el entorno (.env)")
    return v


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# 1. Subida a R2 / S3
# ---------------------------------------------------------------------------

def upload(images: list[Path], slug: str) -> list[str]:
    """Sube las imágenes y devuelve sus URLs públicas, en orden."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        sys.exit("Falta boto3:  pip install -r requirements-publish.txt")

    bucket = env("R2_BUCKET")
    base = env("CDN_BASE_URL").rstrip("/")

    s3 = boto3.client(
        "s3",
        endpoint_url=env("R2_ENDPOINT"),
        aws_access_key_id=env("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=env("R2_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

    urls = []
    for img in images:
        key = f"carousels/{slug}/{img.name}"
        ctype = mimetypes.guess_type(img.name)[0] or "image/png"
        s3.upload_file(str(img), bucket, key,
                       ExtraArgs={"ContentType": ctype,
                                  "CacheControl": "public, max-age=31536000"})
        urls.append(f"{base}/{key}")
        log(f"  ↑ {img.name}")
    return urls


# ---------------------------------------------------------------------------
# 2. Instagram — modelo de contenedores
# ---------------------------------------------------------------------------

def ig_call(method: str, path: str, **params) -> dict:
    params["access_token"] = env("IG_ACCESS_TOKEN")
    r = requests.request(method, f"{GRAPH}/{path}", params=params, timeout=TIMEOUT)
    data = r.json()
    if "error" in data:
        e = data["error"]
        sys.exit(f"Instagram error {e.get('code')}: {e.get('message')}\n"
                 f"  {e.get('error_user_msg') or ''}")
    return data


def ig_wait(container_id: str, timeout: int = 240) -> None:
    """Un contenedor pasa por IN_PROGRESS antes de estar listo. Publicar antes falla."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = ig_call("GET", container_id, fields="status_code,status")["status_code"]
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram: el contenedor {container_id} terminó en {st}")
        time.sleep(5)
    sys.exit(f"Instagram: el contenedor {container_id} no estuvo listo a tiempo")


def publish_instagram(urls: list[str], caption: str, dry: bool = False) -> str | None:
    ig_user = env("IG_USER_ID")

    if len(urls) > 10:
        sys.exit(f"Instagram admite 10 imágenes por carrusel como máximo, tienes {len(urls)}")

    if dry:
        log(f"  [dry-run] carrusel de {len(urls)} imágenes, caption de {len(caption)} caracteres")
        return None

    children = []
    for i, url in enumerate(urls, 1):
        c = ig_call("POST", f"{ig_user}/media", image_url=url, is_carousel_item="true")
        children.append(c["id"])
        log(f"  · contenedor {i}/{len(urls)}")

    parent = ig_call("POST", f"{ig_user}/media", media_type="CAROUSEL",
                     children=",".join(children), caption=caption)
    ig_wait(parent["id"])

    result = ig_call("POST", f"{ig_user}/media_publish", creation_id=parent["id"])
    log(f"  ✓ Instagram publicado — media id {result['id']}")
    return result["id"]


def ig_refresh_token() -> None:
    """El token de larga duración caduca a los 60 días. Refréscalo antes."""
    r = requests.get(f"{GRAPH}/refresh_access_token",
                     params={"grant_type": "ig_refresh_token",
                             "access_token": env("IG_ACCESS_TOKEN")}, timeout=TIMEOUT)
    d = r.json()
    if "access_token" not in d:
        sys.exit(f"No se pudo refrescar: {d}")
    days = int(d.get("expires_in", 0)) // 86400
    log(f"Nuevo token (caduca en {days} días). Guárdalo en .env como IG_ACCESS_TOKEN:\n")
    log(d["access_token"])


# ---------------------------------------------------------------------------
# 3. TikTok — Content Posting API, modo foto
# ---------------------------------------------------------------------------

def tt_token() -> str:
    """Los access token de TikTok duran 24 h; se renuevan con el refresh_token."""
    r = requests.post(f"{TIKTOK}/oauth/token/",
                      data={"client_key": env("TIKTOK_CLIENT_KEY"),
                            "client_secret": env("TIKTOK_CLIENT_SECRET"),
                            "grant_type": "refresh_token",
                            "refresh_token": env("TIKTOK_REFRESH_TOKEN")},
                      headers={"Content-Type": "application/x-www-form-urlencoded"},
                      timeout=TIMEOUT)
    d = r.json()
    if "access_token" not in d:
        sys.exit(f"TikTok: no se pudo refrescar el token: {d}")
    if d.get("refresh_token") and d["refresh_token"] != os.getenv("TIKTOK_REFRESH_TOKEN"):
        log("  ⚠  TikTok ha rotado el refresh_token. Actualiza .env con:")
        log(f"     TIKTOK_REFRESH_TOKEN={d['refresh_token']}")
    return d["access_token"]


def tt_post(token: str, path: str, body: dict) -> dict:
    r = requests.post(f"{TIKTOK}/{path}", json=body, timeout=TIMEOUT,
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type": "application/json; charset=UTF-8"})
    d = r.json()
    err = d.get("error", {})
    if err.get("code") not in (None, "ok"):
        sys.exit(f"TikTok error {err.get('code')}: {err.get('message')}")
    return d.get("data", {})


def publish_tiktok(urls: list[str], title: str, description: str,
                   dry: bool = False) -> str | None:
    token = tt_token()
    mode = os.getenv("TIKTOK_MODE", "draft").lower()

    post_info = {"title": title[:90]}
    if mode == "direct":
        # Obligatorio antes de publicar directo: los ajustes permitidos los
        # decide el creador, no tú, y enviar uno no permitido es un rechazo.
        info = tt_post(token, "post/publish/creator_info/query/", {})
        allowed = info.get("privacy_level_options", [])
        level = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in allowed else \
            (allowed[0] if allowed else "SELF_ONLY")
        if level != "PUBLIC_TO_EVERYONE":
            log(f"  ⚠  TikTok sólo permite {level} — ¿tu app sigue sin auditar?")
        post_info.update({
            "description": description[:4000],
            "privacy_level": level,
            "disable_comment": False,
            "auto_add_music": True,
        })

    body = {
        "post_info": post_info,
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_cover_index": 0,
            "photo_images": urls,
        },
        "post_mode": "DIRECT_POST" if mode == "direct" else "MEDIA_UPLOAD",
        "media_type": "PHOTO",
    }

    if dry:
        log("  [dry-run] payload TikTok:")
        log(json.dumps(body, ensure_ascii=False, indent=2)[:900])
        return None

    data = tt_post(token, "post/publish/content/init/", body)
    publish_id = data["publish_id"]

    # TikTok descarga las imágenes de forma asíncrona: hay que esperar
    for _ in range(40):
        time.sleep(5)
        st = tt_post(token, "post/publish/status/fetch/", {"publish_id": publish_id})
        status = st.get("status")
        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            log("  ✓ TikTok " + ("publicado" if mode == "direct"
                                 else "enviado a tus borradores — ábrelo en la app y publica"))
            return publish_id
        if status == "FAILED":
            sys.exit(f"TikTok falló: {st.get('fail_reason')}")
    log("  ⚠  TikTok sigue procesando. Revisa la app en unos minutos.")
    return publish_id


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def load_carousel(folder: Path) -> tuple[list[Path], str]:
    images = sorted(p for p in folder.iterdir()
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    if not images:
        sys.exit(f"No hay imágenes en {folder}")
    cap = folder / "caption.txt"
    return images, cap.read_text(encoding="utf-8").strip() if cap.exists() else ""


def main():
    ap = argparse.ArgumentParser(description="Publica un carrusel ya generado")
    ap.add_argument("folder", nargs="?", help="carpeta output/<slug>")
    ap.add_argument("--only", choices=["instagram", "tiktok"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="republicar aunque ya se publicara")
    ap.add_argument("--refresh-ig-token", action="store_true")
    args = ap.parse_args()

    if args.refresh_ig_token:
        return ig_refresh_token()
    if not args.folder:
        ap.error("indica la carpeta del carrusel")

    folder = Path(args.folder)
    state = folder / ".published.json"
    if state.exists() and not args.force and not args.dry_run:
        sys.exit(f"Ya publicado el {json.loads(state.read_text())['at']}. Usa --force.")

    images, caption = load_carousel(folder)
    title = caption.split("\n")[0][:90] if caption else folder.name
    log(f"→ {folder.name}: {len(images)} imágenes")

    urls = upload(images, folder.name)

    done = {}
    if args.only != "tiktok":
        done["instagram"] = publish_instagram(urls, caption, args.dry_run)
    if args.only != "instagram":
        done["tiktok"] = publish_tiktok(urls, title, caption, args.dry_run)

    if not args.dry_run:
        state.write_text(json.dumps(
            {"at": time.strftime("%Y-%m-%d %H:%M"), "urls": urls, "ids": done},
            ensure_ascii=False, indent=2), encoding="utf-8")
        log("\nListo.")


if __name__ == "__main__":
    main()
