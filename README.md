# Chinese Reads — generador de carruseles

Convierte un JSON con palabras en un carrusel de Instagram listo para publicar:
portada, una slide por palabra, slide final de promoción y el texto del pie.

El proyecto vive entero en [`chinesereads-carousel/`](chinesereads-carousel/).
Esta carpeta solo es el contenedor del repositorio.

## Inicio rápido

```bash
cd chinesereads-carousel
python3 -m venv .venv
source .venv/bin/activate          # Windows:  .venv\Scripts\activate
pip install -r requirements.txt

python generate_carousel.py posts/qing.json
```

Salida en `chinesereads-carousel/output/qing/`: siete PNG numerados y
`caption.txt`. Sin claves de API, sin cuentas, sin internet.

> Todos los comandos se ejecutan **desde dentro de `chinesereads-carousel/`**,
> con el entorno virtual activado. Fuera del venv usa `python3`, no `python`.

## Dónde está cada cosa

| | |
|---|---|
| [chinesereads-carousel/README.md](chinesereads-carousel/README.md) | **manual completo** — estructura, instalación por partes, flujo de trabajo |
| [chinesereads-carousel/docs/generate_carousel.md](chinesereads-carousel/docs/generate_carousel.md) | formato del JSON, diseño, fuentes, contraste |
| [chinesereads-carousel/docs/write_post.md](chinesereads-carousel/docs/write_post.md) | escribir los textos con Claude (opcional) |
| [chinesereads-carousel/docs/make_background.md](chinesereads-carousel/docs/make_background.md) | fondos dibujados por código |
| [chinesereads-carousel/docs/ai_background.md](chinesereads-carousel/docs/ai_background.md) | fondos fotorrealistas por IA (opcional) |
| [chinesereads-carousel/docs/publish.md](chinesereads-carousel/docs/publish.md) | publicar por API (opcional) |
| [SETUP.md](SETUP.md) | montaje de la publicación automática, paso a paso |

## Diagnóstico

```bash
cd chinesereads-carousel && python doctor.py
```

Te dice qué herramientas están listas y qué le falta a cada una. Desde la raíz
también funciona (`python3 doctor.py`): se redirige solo al subproyecto.
