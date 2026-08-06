#!/usr/bin/env python3
"""
make_background.py — fondos de portada generados por código
============================================================

Escenas de callejón de barrio chino con farolillos. Todo es geometría dibujada
al vuelo, así que el resultado es tuyo: sin licencias, sin API, sin coste, y
reproducible a partir de una semilla.

    python make_background.py                      # una imagen aleatoria
    python make_background.py --seed 42            # reproducible
    python make_background.py --count 6            # una tanda
    python make_background.py --palette dusk       # night | dusk | festival

Salen en assets/backgrounds/, listas para usar en el JSON del post.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
SIZE = 1080

PALETTES = {
    # (cielo arriba, resplandor del horizonte, farolillo, brillo, edificios)
    # El resplandor va ABAJO a propósito: los edificios sólo se leen como
    # silueta si tienen un fondo más claro detrás.
    "night":    ((10, 14, 34), (158, 82, 62), (206, 38, 32), (255, 150, 70), (7, 7, 15)),
    "dusk":     ((44, 36, 76), (232, 138, 88), (214, 46, 38), (255, 176, 92), (16, 13, 26)),
    "festival": ((26, 10, 24), (196, 62, 48), (226, 32, 30), (255, 196, 96), (12, 5, 12)),
}


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def sky(top, bottom) -> Image.Image:
    """Degradado vertical, con más resolución tonal en la parte baja."""
    img = Image.new("RGB", (1, SIZE))
    px = img.load()
    for y in range(SIZE):
        px[0, y] = lerp(top, bottom, (y / SIZE) ** 1.35)
    return img.resize((SIZE, SIZE), Image.BILINEAR)


def alley_wall(rng: random.Random, side: int, vx: float, vy: float,
               colour, window) -> Image.Image:
    """
    Un muro de callejón en perspectiva, como capa RGBA.

    Los muros van a los lados y no cruzando la imagen: así el centro queda
    despejado para el texto de la portada, que es lo que tiene que ganar.
    Todo converge en el punto de fuga (vx, vy).
    """
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    edge = 0 if side < 0 else SIZE
    inner = vx + side * SIZE * 0.10          # el hueco central que queda libre

    # Muro casi vertical en el borde y cerrándose hacia la fuga. El techo baja
    # y el suelo sube, que es lo que crea la sensación de profundidad.
    d.polygon([(edge, -60), (inner, vy - SIZE * 0.22),
               (inner, vy + SIZE * 0.10), (edge, SIZE + 60)],
              fill=colour + (255,))

    # ventanas: rejilla en perspectiva, pequeñas y densas
    for t in [0.10, 0.24, 0.38, 0.52, 0.64, 0.75, 0.84]:
        x = edge + (inner - edge) * t
        k = 1 - t * 0.82                       # escala por distancia
        w, h = 26 * k, 34 * k
        top = -60 + (vy - SIZE * 0.22 + 60) * t
        bot = SIZE + 60 + (vy + SIZE * 0.10 - SIZE - 60) * t
        for row in range(4):
            cy = top + (bot - top) * (0.18 + row * 0.17)
            if rng.random() < 0.32:
                continue
            tone = lerp(window, colour, rng.uniform(0.0, 0.5))
            d.rectangle([x - w / 2, cy - h / 2, x + w / 2, cy + h / 2],
                        fill=tone + (255,))

        # cartel vertical hacia el centro: el detalle que sitúa la escena
        if t < 0.7 and rng.random() < 0.55:
            sw, sh = 11 * k, 90 * k
            sx = x - side * 34 * k
            sy = top + (bot - top) * 0.30
            d.rectangle([sx - sw, sy, sx + sw, sy + sh],
                        fill=lerp(window, (206, 34, 30), 0.62) + (255,))
    return layer


def lantern(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float,
            body, cap=(232, 186, 92)):
    """Un farolillo: cuerpo achatado, tapas doradas, nervios verticales y borla."""
    rx, ry = r, r * 0.82
    draw.line([(cx, cy - ry - r * 1.9), (cx, cy - ry)], fill=(60, 40, 30), width=max(1, int(r * 0.07)))
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=body)

    # nervios: sólo se ven de cerca, pero son lo que evita que parezca una pelota
    if r > 22:
        rib = lerp(body, (0, 0, 0), 0.22)
        for i in (-0.55, -0.2, 0.2, 0.55):
            ox = rx * i
            draw.ellipse([cx + ox - rx * 0.1, cy - ry * 0.97,
                          cx + ox + rx * 0.1, cy + ry * 0.97], outline=rib,
                         width=max(1, int(r * 0.05)))

    ch, cw = r * 0.2, rx * 0.52
    draw.rectangle([cx - cw, cy - ry - ch, cx + cw, cy - ry + ch * 0.4], fill=cap)
    draw.rectangle([cx - cw, cy + ry - ch * 0.4, cx + cw, cy + ry + ch], fill=cap)
    draw.line([(cx, cy + ry + ch), (cx, cy + ry + r * 0.75)], fill=cap,
              width=max(1, int(r * 0.12)))


def string_of_lanterns(layer, glow, rng, y0, count, radius, sag, body, halo):
    """Una guirnalda con catenaria. Devuelve dibujado en dos capas: cuerpo y brillo."""
    d, g = ImageDraw.Draw(layer), ImageDraw.Draw(glow)
    xs = [SIZE * (i + 0.5) / count + rng.uniform(-18, 18) for i in range(count)]
    pts = [(x, y0 + sag * math.sin(math.pi * (x / SIZE))) for x in xs]

    d.line([(-40, y0 - 12)] + [(x, y - radius * 1.9) for x, y in pts] + [(SIZE + 40, y0 - 12)],
           fill=(56, 38, 32), width=max(2, int(radius * 0.1)), joint="curve")

    for x, y in pts:
        r = radius * rng.uniform(0.88, 1.12)
        lantern(d, x, y, r, body)
        g.ellipse([x - r * 2.6, y - r * 2.6, x + r * 2.6, y + r * 2.6], fill=halo)


def scene(seed: int, palette: str) -> Image.Image:
    rng = random.Random(seed)
    top, glow_c, body, halo, build = PALETTES[palette]

    vx = SIZE * 0.5 + rng.uniform(-60, 60)
    vy = SIZE * rng.uniform(0.60, 0.68)

    img = sky(top, lerp(glow_c, top, 0.45))

    # resplandor al fondo del callejón: es la fuente de luz de toda la escena
    g = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(g).ellipse([vx - SIZE * 0.42, vy - SIZE * 0.30,
                               vx + SIZE * 0.42, vy + SIZE * 0.30], fill=255)
    img = Image.composite(Image.new("RGB", img.size, glow_c), img,
                          g.filter(ImageFilter.GaussianBlur(150)))

    window = lerp(halo, (255, 240, 200), 0.35)
    for side in (-1, 1):
        wall = alley_wall(rng, side, vx, vy, build, window)
        img.paste(wall, (0, 0), wall)

    # suelo: refleja algo de luz, no es negro plano
    ground = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(ground).polygon([(0, SIZE), (SIZE, SIZE), (vx + 80, vy), (vx - 80, vy)],
                                   fill=255)
    img = Image.composite(
        Image.blend(img, Image.new("RGB", img.size, lerp(glow_c, (0, 0, 0), 0.84)), 0.88),
        img, ground.filter(ImageFilter.GaussianBlur(40)))

    # guirnaldas cruzando el callejón: de lejos a cerca
    for L in (dict(y0=int(SIZE * 0.42), n=9, r=14, sag=22, blur=2.8),
              dict(y0=int(SIZE * 0.27), n=6, r=28, sag=40, blur=1.2),
              dict(y0=int(SIZE * 0.10), n=4, r=50, sag=60, blur=0.0)):
        body_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        glow_layer = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
        string_of_lanterns(body_layer, glow_layer, rng, L["y0"], L["n"],
                           L["r"], L["sag"], body, lerp(halo, (0, 0, 0), 0.62))
        img = ImageChops_screen(img, glow_layer.filter(
            ImageFilter.GaussianBlur(L["r"] * 1.7)))
        if L["blur"]:
            body_layer = body_layer.filter(ImageFilter.GaussianBlur(L["blur"]))
        img.paste(body_layer, (0, 0), body_layer)

    vig = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(vig).ellipse([-SIZE * 0.22, -SIZE * 0.22, SIZE * 1.22, SIZE * 1.22], fill=255)
    img = Image.composite(img, Image.new("RGB", img.size, (0, 0, 0)),
                          vig.filter(ImageFilter.GaussianBlur(170)).point(lambda v: 40 + v * 0.84))
    return img


def ImageChops_screen(a: Image.Image, b: Image.Image) -> Image.Image:
    from PIL import ImageChops
    return ImageChops.screen(a, b)


def main():
    ap = argparse.ArgumentParser(description="Genera fondos de portada")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--palette", choices=list(PALETTES), default="night")
    ap.add_argument("--outdir", default="assets/backgrounds")
    args = ap.parse_args()

    out = ROOT / args.outdir
    out.mkdir(parents=True, exist_ok=True)

    for i in range(args.count):
        seed = args.seed if args.seed is not None else random.randint(1000, 9999)
        seed += i if args.seed is not None else 0
        path = out / f"lanterns_{args.palette}_{seed}.jpg"
        scene(seed, args.palette).save(path, quality=92)
        print(f"✓ {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
