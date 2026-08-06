#!/usr/bin/env python3
"""
generate_carousel.py — Generador de carruseles para Chinese Reads
================================================================

Convierte un JSON de contenido en un carrusel completo listo para publicar:

    portada  ->  N slides de contenido  ->  slide final de promoción

Uso:
    python generate_carousel.py posts/qing.json
    python generate_carousel.py posts/qing.json -o output/ --format jpg

Estructura esperada:
    assets/content_bg.png              fondo fijo de las slides de contenido
    assets/final_slide.png             slide final de promoción (fija)
    assets/logo.png                    logo con transparencia (portada)
    assets/backgrounds/*.jpg           fotos para las portadas
    posts/*.json                       un fichero por post
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

try:
    from fontTools.ttLib import TTFont, TTCollection
except ImportError:  # el chequeo de glifos es opcional
    TTFont = None

ROOT = Path(__file__).parent
SIZE = 1080  # lienzo cuadrado 1080x1080


# ---------------------------------------------------------------------------
# TEMA — todo lo visual se toca aquí. Las posiciones son fracciones de 1080
#        para que el diseño escale si cambias SIZE.
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    # --- colores ---
    red: str = "#F42C1E"            # rojo de hanzi / pinyin / significado
    red_dark: str = "#8E1B15"       # rojo del dominio en portada
    ink: str = "#2A2A2A"            # handle @chinesereads.com
    cover_fill: str = "#FFFFFF"
    cover_stroke: str = "#000000"

    # --- portada ---
    cover_title_y: float = 0.285     # centro vertical del bloque de título
    cover_title_size: int = 82       # tamaño máximo (se reduce solo si no cabe)
    cover_title_max_w: float = 0.86
    cover_sub_y: float = 0.545
    cover_sub_size: int = 56
    cover_sub_max_w: float = 0.82
    cover_stroke_w: int = 9          # grosor del contorno negro
    cover_logo_y: float = 0.775
    cover_logo_w: float = 0.075
    cover_domain_y: float = 0.828
    cover_domain_size: int = 40

    # --- auto-contraste de la portada ---
    # Mide la luminancia real detrás de cada bloque de texto y oscurece SOLO
    # esas bandas, con degradado, hasta que el texto blanco se lee seguro.
    auto_contrast: bool = True
    target_luma: float = 96.0        # luminancia objetivo detrás del texto (0-255)
    busy_bonus: float = 0.75         # cuánto castiga un fondo con mucho detalle
    scrim_max: float = 0.72          # oscurecimiento máximo, para no matar la foto
    scrim_feather: int = 90          # difuminado del borde de la banda, en px
    cover_darken: float = 0.0        # oscurecimiento global extra, manual (0-1)

    # --- slides de contenido ---
    hanzi_y: float = 0.200
    hanzi_size: int = 165
    pinyin_y: float = 0.447
    pinyin_size: int = 88
    meaning_y: float = 0.660
    meaning_size: int = 62
    meaning_max_w: float = 0.68
    handle_y: float = 0.885
    handle_size: int = 42
    handle_text: str = "@chinesereads.com"

    domain_text: str = "chinesereads.com"

    # --- fuentes: primera que exista gana ---
    font_cover: list = field(default_factory=lambda: [
        "assets/fonts/Cover.ttf",
        "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ])
    font_hanzi: list = field(default_factory=lambda: [
        "assets/fonts/Hanzi.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc#2",  # Noto Sans CJK SC Black
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc#2",
    ])
    font_latin: list = field(default_factory=lambda: [
        "assets/fonts/Latin.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc#2",  # cubre tonos ǎ ǐ ǒ ǔ ǚ
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ])


THEME = Theme()


# ---------------------------------------------------------------------------
# Fuentes
# ---------------------------------------------------------------------------

_font_cache: dict = {}


def _resolve(candidates: list[str]) -> tuple[str, int]:
    """Devuelve (ruta, índice) de la primera fuente que exista. '#2' = índice en .ttc"""
    for c in candidates:
        path, _, idx = c.partition("#")
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        if p.exists():
            return str(p), int(idx or 0)
    raise FileNotFoundError(f"Ninguna fuente encontrada en: {candidates}")


def load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    path, idx = _resolve(candidates)
    key = (path, idx, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size, index=idx)
    return _font_cache[key]


def check_glyphs(text: str, candidates: list[str]) -> str:
    """Devuelve los caracteres que la fuente NO puede dibujar (para avisar a tiempo)."""
    if TTFont is None:
        return ""
    try:
        path, idx = _resolve(candidates)
        f = TTCollection(path).fonts[idx] if path.endswith(".ttc") else TTFont(path)
        cmap = f.getBestCmap()
        return "".join(dict.fromkeys(c for c in text if c.strip() and ord(c) not in cmap))
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Utilidades de dibujo
# ---------------------------------------------------------------------------

def wrap(draw, text: str, font, max_w: int) -> list[str]:
    """Ajuste de línea por palabras (respeta saltos manuales con \\n)."""
    lines = []
    for paragraph in text.split("\n"):
        words, cur = paragraph.split(), ""
        for w in words:
            probe = f"{cur} {w}".strip()
            if draw.textlength(probe, font=font) <= max_w or not cur:
                cur = probe
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def fit_text(draw, text, candidates, start_size, max_w, max_h=None, min_size=28):
    """Baja el tamaño de fuente hasta que el texto quepa en la caja."""
    size = start_size
    while size > min_size:
        font = load_font(candidates, size)
        lines = wrap(draw, text, font, max_w)
        line_h = int(size * 1.22)
        if (max_h is None or len(lines) * line_h <= max_h) and \
           all(draw.textlength(l, font=font) <= max_w for l in lines):
            return font, lines, line_h
        size -= 3
    font = load_font(candidates, min_size)
    return font, wrap(draw, text, font, max_w), int(min_size * 1.22)


def draw_block(draw, lines, font, line_h, center_y, canvas_w, **kw):
    """Dibuja varias líneas centradas horizontalmente, con el bloque centrado en center_y."""
    total = len(lines) * line_h
    y = center_y - total / 2
    for line in lines:
        draw.text((canvas_w / 2, y + line_h / 2), line,
                  font=font, anchor="mm", **kw)
        y += line_h


def band_alpha(img: Image.Image, y0: int, y1: int, t: Theme) -> float:
    """
    Cuánto hay que oscurecer la banda [y0,y1] para que el texto blanco se lea.

    Dos factores: lo clara que es (una playa o un cielo se comen el texto blanco)
    y lo movida que es (un fondo con mucho detalle rompe la silueta de las letras
    aunque sea oscuro de media). Se miden por separado y se suman.
    """
    y0, y1 = max(0, y0), min(img.height, y1)
    if y1 <= y0:
        return 0.0
    band = img.convert("L").crop((int(img.width * 0.06), y0,
                                  int(img.width * 0.94), y1))
    stat = ImageStat.Stat(band)
    mean, std = stat.mean[0], stat.stddev[0]

    a = max(0.0, 1.0 - t.target_luma / max(mean, 1.0))   # por brillo
    a += min(0.30, (std / 255.0) * t.busy_bonus)          # por detalle
    return min(a, t.scrim_max)


def apply_scrim(img: Image.Image, bands: list[tuple[int, int]], t: Theme) -> Image.Image:
    """Superpone negro con degradado suave sólo donde hay texto."""
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    applied = []
    for y0, y1 in bands:
        a = band_alpha(img, y0, y1, t)
        applied.append(a)
        if a > 0.02:
            draw.rectangle([0, y0, img.width, y1], fill=int(a * 255))
    if not any(a > 0.02 for a in applied):
        return img
    mask = mask.filter(ImageFilter.GaussianBlur(t.scrim_feather))
    black = Image.new("RGB", img.size, (0, 0, 0))
    print("     scrim: " + "  ".join(f"{a:.2f}" for a in applied))
    return Image.composite(black, img, mask)


def cover_crop(path: Path, size: int) -> Image.Image:
    """Recorta la foto a cuadrado centrado, tipo object-fit: cover."""
    im = Image.open(path).convert("RGB")
    scale = size / min(im.width, im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - size) // 2, (im.height - size) // 2
    return im.crop((left, top, left + size, top + size))


# ---------------------------------------------------------------------------
# Renderizado de cada tipo de slide
# ---------------------------------------------------------------------------

def render_cover(cover: dict, out: Path, t: Theme = THEME) -> Path:
    bg_path = ROOT / cover["background"]
    if not bg_path.exists():
        raise FileNotFoundError(f"No encuentro la foto de portada: {bg_path}")

    img = cover_crop(bg_path, SIZE)

    darken = cover.get("darken", t.cover_darken)
    if darken:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * darken)))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Auto-contraste: se mide DESPUÉS del recorte, porque lo que importa es
    # el trozo de foto que queda visible, no la foto entera.
    if cover.get("auto_contrast", t.auto_contrast):
        img = apply_scrim(img, [
            (int(SIZE * (t.cover_title_y - 0.17)), int(SIZE * (t.cover_title_y + 0.17))),
            (int(SIZE * (t.cover_sub_y - 0.075)), int(SIZE * (t.cover_sub_y + 0.075))),
            (int(SIZE * (t.cover_logo_y - 0.055)), int(SIZE * (t.cover_domain_y + 0.04))),
        ], t)

    draw = ImageDraw.Draw(img)
    stroke = dict(stroke_width=t.cover_stroke_w, stroke_fill=t.cover_stroke)

    title = cover["title"]
    missing = check_glyphs(title, t.font_cover)
    fonts = t.font_latin if missing else t.font_cover
    if missing:
        print(f"  ⚠  la fuente de portada no tiene {missing!r} — uso la fuente de respaldo")

    font, lines, lh = fit_text(draw, title, fonts, t.cover_title_size,
                               int(SIZE * t.cover_title_max_w), int(SIZE * 0.34))
    draw_block(draw, lines, font, lh, SIZE * t.cover_title_y, SIZE,
               fill=t.cover_fill, **stroke)

    if cover.get("subtitle"):
        font, lines, lh = fit_text(draw, cover["subtitle"], fonts, t.cover_sub_size,
                                   int(SIZE * t.cover_sub_max_w), int(SIZE * 0.18))
        draw_block(draw, lines, font, lh, SIZE * t.cover_sub_y, SIZE,
                   fill=t.cover_fill, stroke_width=t.cover_stroke_w - 2,
                   stroke_fill=t.cover_stroke)

    # logo + dominio
    logo_path = ROOT / "assets" / "logo.png"
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        w = int(SIZE * t.cover_logo_w)
        logo = logo.resize((w, round(w * logo.height / logo.width)), Image.LANCZOS)
        img.paste(logo, (SIZE // 2 - logo.width // 2,
                         int(SIZE * t.cover_logo_y) - logo.height // 2), logo)

    dfont = load_font(t.font_cover, t.cover_domain_size)
    draw.text((SIZE / 2, SIZE * t.cover_domain_y), t.domain_text, font=dfont,
              anchor="mm", fill=t.red_dark, stroke_width=3, stroke_fill="#FFFFFF")

    img.save(out, quality=95)
    return out


def render_content(slide: dict, out: Path, t: Theme = THEME) -> Path:
    bg_path = ROOT / "assets" / "content_bg.png"
    if not bg_path.exists():
        raise FileNotFoundError(f"Falta el fondo de contenido: {bg_path}")

    img = Image.open(bg_path).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    hanzi = slide["hanzi"]
    size = t.hanzi_size
    if len(hanzi) > 1:                       # palabras/frases: encoger para que quepan
        size = int(size * min(1.0, 2.6 / len(hanzi)) ** 0.55)
    draw.text((SIZE / 2, SIZE * t.hanzi_y), hanzi,
              font=load_font(t.font_hanzi, size), anchor="mm", fill=t.red)

    pinyin = slide.get("pinyin", "")
    if pinyin:
        missing = check_glyphs(pinyin, t.font_latin)
        if missing:
            print(f"  ⚠  faltan glifos {missing!r} para el pinyin — revisa la fuente")
        font, lines, lh = fit_text(draw, pinyin, t.font_latin, t.pinyin_size,
                                   int(SIZE * 0.78))
        draw_block(draw, lines, font, lh, SIZE * t.pinyin_y, SIZE, fill=t.red)

    meaning = slide.get("meaning", "")
    if meaning:
        font, lines, lh = fit_text(draw, meaning, t.font_latin, t.meaning_size,
                                   int(SIZE * t.meaning_max_w), int(SIZE * 0.20))
        draw_block(draw, lines, font, lh, SIZE * t.meaning_y, SIZE, fill=t.red)

    draw.text((SIZE / 2, SIZE * t.handle_y), t.handle_text,
              font=load_font(t.font_latin, t.handle_size), anchor="mm", fill=t.ink)

    img.save(out, quality=95)
    return out


def render_final(out: Path) -> Path | None:
    src = ROOT / "assets" / "final_slide.png"
    if not src.exists():
        print("  ⚠  no hay assets/final_slide.png — me salto la slide de promoción")
        return None
    Image.open(src).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS).save(out, quality=95)
    return out


# ---------------------------------------------------------------------------
# Orquestación
# ---------------------------------------------------------------------------

def build(post: dict, outdir: Path, fmt: str = "png") -> list[Path]:
    slug = post.get("slug", "post")
    dest = outdir / slug
    dest.mkdir(parents=True, exist_ok=True)

    paths, n = [], 1
    print(f"→ {slug}")

    paths.append(render_cover(post["cover"], dest / f"{n:02d}_portada.{fmt}"))
    print(f"  ✓ 01 portada")

    for slide in post["slides"]:
        n += 1
        render_content(slide, dest / f"{n:02d}_{slide['hanzi']}.{fmt}")
        paths.append(dest / f"{n:02d}_{slide['hanzi']}.{fmt}")
        print(f"  ✓ {n:02d} {slide['hanzi']}  {slide.get('pinyin','')}")

    if post.get("include_final", True):
        n += 1
        f = render_final(dest / f"{n:02d}_promo.{fmt}")
        if f:
            paths.append(f)
            print(f"  ✓ {n:02d} promo")

    caption = build_caption(post)
    (dest / "caption.txt").write_text(caption, encoding="utf-8")
    print(f"  ✓ caption.txt ({len(caption)} caracteres)")

    return paths


def build_caption(post: dict) -> str:
    parts = []
    if post.get("caption"):
        parts.append(post["caption"].strip())
    vocab = " · ".join(
        f"{s['hanzi']} ({s['pinyin']}) {s.get('meaning','')}".strip()
        for s in post["slides"]
    )
    if vocab:
        parts.append(vocab)
    parts.append(post.get("cta", "Read real Chinese texts for free at chinesereads.com 📖"))
    tags = post.get("hashtags") or ["#learnchinese", "#chinesetexts", "#chinesereads",
                                    "#mandarin", "#hsk", "#chinesevocabulary"]
    parts.append(" ".join(tags))
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Genera un carrusel de Chinese Reads")
    ap.add_argument("post", help="ruta al JSON del post (o carpeta con varios)")
    ap.add_argument("-o", "--outdir", default="output", help="carpeta de salida")
    ap.add_argument("--format", default="png", choices=["png", "jpg"])
    args = ap.parse_args()

    src = Path(args.post)
    if not src.is_absolute():
        src = ROOT / src
    files = sorted(src.glob("*.json")) if src.is_dir() else [src]
    if not files:
        sys.exit(f"No hay JSONs en {src}")

    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = ROOT / outdir

    for f in files:
        post = json.loads(f.read_text(encoding="utf-8"))
        build(post, outdir, args.format)

    print(f"\nListo → {outdir}")


if __name__ == "__main__":
    main()
