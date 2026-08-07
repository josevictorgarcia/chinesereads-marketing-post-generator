# Chinese Reads — carruseles automatizados

Cinco herramientas independientes que van desde "tengo un tema" hasta "está publicado".

```
   fondo                texto              carrusel            publicación
   ─────                ─────              ────────            ───────────
make_background.py  ┐                  ┌─ generate_       ┌─ publish.py
                    ├─  write_post.py ─┤   carousel.py ───┤
ai_background.py    ┘                  └─ (a mano)        └─ o a mano
```

**Cada pieza es independiente.** Se comunican por ficheros, no por código:

| Herramienta | Entrada | Salida |
|---|---|---|
| `make_background.py` | nada | JPG en `assets/backgrounds/` |
| `ai_background.py` | un prompt | PNG en `assets/backgrounds/` |
| `write_post.py` | un tema | JSON en `posts/` |
| `generate_carousel.py` | JSON de `posts/` | imágenes + caption en `output/` |
| `publish.py` | carpeta de `output/` | post publicado |

Puedes entrar y salir del pipeline donde quieras. Escribir el JSON a mano y saltarte `write_post.py`. Usar tus propias fotos y saltarte los dos generadores de fondo. **Y desde luego saltarte `publish.py`:** la carpeta de salida es autosuficiente, y arrastrar siete imágenes a Metricool funciona perfectamente.

La única obligatoria es `generate_carousel.py`.

---

## Inicio rápido

```bash
./carrusel barrio-chino
```

El script se encarga del entorno virtual: si no existe lo crea e instala las dependencias, así no hay que acordarse de activarlo cada vez que se abre una terminal. Al terminar abre la carpeta con las siete imágenes y el `caption.txt`.

```bash
./carrusel                 # todos los posts de posts/
./carrusel qing            # solo uno, por su nombre
./carrusel --no-abrir      # sin abrir la carpeta al terminar
```

Sin claves de API, sin cuentas, sin internet.

A mano, si lo prefieres:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows:  .venv\Scripts\activate
pip install -r requirements.txt

python generate_carousel.py posts/barrio-chino.json
```

---

## Sobre el entorno virtual

**Créalo. No es una recomendación de estilo, es que en muchos sistemas no funciona sin él.**

Desde Python 3.11, las instalaciones de Python que vienen con el sistema (Ubuntu, Debian, macOS con Homebrew) rechazan `pip install` con un error así:

```
error: externally-managed-environment
× This environment is externally managed
```

Es una protección para que no rompas paquetes de los que depende tu sistema operativo. Un entorno virtual es una carpeta aparte con su propio Python y sus propias librerías, y ahí pip funciona con normalidad.

```bash
python3 -m venv .venv              # crear (una sola vez)
source .venv/bin/activate          # activar (cada vez que abras terminal)
deactivate                         # salir
```

Sabrás que está activo porque el prompt cambia a `(.venv)`. La carpeta `.venv/` está en `.gitignore`.

**Si te sale `externally-managed-environment` es que no lo activaste.** Verás la tentación de usar `pip install --break-system-packages`, que es lo que hace saltar el aviso. Funciona, pero instala en el Python del sistema y es exactamente lo que la protección intenta evitar. Crea el venv.

### Cuidado con cron y los scripts programados

`cron` no hereda el entorno que activaste en tu terminal. Si programas la publicación, usa la ruta completa al Python del venv:

```cron
# mal — usa el Python del sistema y no encuentra las librerías
0 10 * * 2,5  cd ~/chinesereads-carousel && python publish.py output/qing

# bien
0 10 * * 2,5  cd ~/chinesereads-carousel && .venv/bin/python publish.py output/qing
```

Lo mismo para cualquier tarea programada. En GitHub Actions no aplica: cada ejecución arranca en una máquina limpia y aislada.

### Reinstalar desde cero

Si algo se lía, borra y empieza otra vez. No pierdes nada: tus posts, assets y salidas están fuera del venv.

```bash
rm -rf .venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

En cualquier momento:

```bash
python doctor.py
```

Te dice qué herramientas están listas y qué le falta a cada una.

---

## Documentación

| | |
|---|---|
| [docs/generate_carousel.md](docs/generate_carousel.md) | **el núcleo** — formato del JSON, diseño, fuentes, contraste |
| [docs/write_post.md](docs/write_post.md) | textos con Claude |
| [docs/make_background.md](docs/make_background.md) | fondos dibujados por código |
| [docs/ai_background.md](docs/ai_background.md) | fondos fotorrealistas por IA |
| [docs/publish.md](docs/publish.md) | publicar por API |
| [SETUP.md](SETUP.md) | **montaje de la publicación**, paso a paso |

---

## Estructura

```
chinesereads-carousel/
├── generate_carousel.py        ← obligatorio
├── write_post.py               opcional (Claude)
├── make_background.py          opcional
├── ai_background.py            opcional (API de imagen)
├── publish.py                  opcional (redes)
├── doctor.py                   diagnóstico
│
├── requirements.txt            núcleo: Pillow, fontTools
├── requirements-ai.txt         anthropic, requests
├── requirements-publish.txt    boto3, requests, python-dotenv
│
├── .env.example                copia a .env y rellena lo que uses
├── .gitignore
├── .venv/                      entorno virtual (lo creas tú, no se versiona)
│
├── assets/
│   ├── content_bg.png          fondo de las slides de contenido
│   ├── final_slide.png         tu slide de promoción, fija
│   ├── logo.png                logo con transparencia
│   ├── backgrounds/            fotos de portada
│   └── fonts/                  (opcional) Cover.ttf, Hanzi.ttf, Latin.ttf
│
├── posts/                      un JSON por post
├── output/                     carruseles generados
├── docs/
└── .github/workflows/          publicación programada
```

`assets/`, `posts/` y `output/` son las únicas carpetas que se tocan en el día a día.

---

## Instalación según lo que quieras hacer

Las dependencias están separadas para que no instales boto3 si nunca vas a publicar por API.

Con el entorno virtual activado (`source .venv/bin/activate`):

**Sólo generar carruseles** (empieza aquí):

```bash
pip install -r requirements.txt
```

**Añadir generación de contenido:**

```bash
pip install -r requirements-ai.txt
cp .env.example .env        # rellena ANTHROPIC_API_KEY y/o OPENAI_API_KEY
```

**Añadir publicación automática:**

```bash
pip install -r requirements-publish.txt
# y sigue SETUP.md — bucket, Instagram, TikTok
```

---

## El fichero `.env`

Sólo lo necesitas si usas Claude, la API de imágenes o la publicación. Copia `.env.example` a `.env` y rellena **únicamente** las secciones que vayas a usar; el resto se puede quedar vacío.

```bash
cp .env.example .env
```

| Bloque | Para qué | Herramienta |
|---|---|---|
| `ANTHROPIC_API_KEY` | escribir los posts | `write_post.py` |
| `OPENAI_API_KEY`, `IMAGE_MODEL` | fondos por IA | `ai_background.py` |
| `R2_*`, `CDN_BASE_URL` | alojar las imágenes | `publish.py` |
| `GRAPH_BASE`, `IG_*` | Instagram | `publish.py` |
| `TIKTOK_*` | TikTok | `publish.py` |

`.env` está en `.gitignore`. No lo subas a ningún sitio.

---

## Publicar un post, de principio a fin

### Camino mínimo — sin claves ni cuentas

```bash
# 1. Escribe posts/mi-post.json a mano (copia posts/qing.json de plantilla)
# 2. Genera
python generate_carousel.py posts/mi-post.json
# 3. Abre output/mi-post/, arrastra las imágenes a Metricool o a la app,
#    y pega el contenido de caption.txt
```

Truco: apunta `-o` a una carpeta sincronizada de Google Drive y en Metricool las importas desde Drive sin andar moviendo ficheros.

### Camino completo — todo automático

```bash
python make_background.py --count 3                    # fondos nuevos
python write_post.py "characters sharing 青"           # Claude escribe el JSON
# revisa posts/<slug>.json — 30 segundos, y merece la pena
python generate_carousel.py posts/<slug>.json
python publish.py output/<slug> --dry-run              # ensayo
python publish.py output/<slug>                        # publica
```

### Por lotes

Genera ocho carruseles un domingo y programa el mes entero:

```bash
python generate_carousel.py posts/          # renderiza toda la carpeta
```

---

## Lo que sigue siendo manual, y por qué

| | Trabajo tuyo |
|---|---|
| Instagram por API | cero |
| TikTok en `draft` | un toque en el móvil |
| TikTok en `direct` | cero, tras la auditoría |
| Revisar el JSON | ~30 segundos por post |

Ese último lo dejo a propósito. Puedes encadenar `write_post.py --build` con `publish.py` en un cron y no volver a mirarlo nunca. Pero un tono mal puesto en una cuenta que enseña chino no lo vas a ver hasta que te lo digan en comentarios, y corregir una línea de JSON son diez segundos.

---

## Sobre los assets incluidos

`content_bg.png` y `logo.png` salen de tus imágenes de ejemplo: al primero le borré el texto por inpainting, del segundo recorté el logo y le puse canal alfa.

**`assets/backgrounds/tea_fields.jpg` lleva el texto antiguo incrustado**, porque es tu portada de ejemplo tal cual. Sustitúyela por la foto original limpia antes de usarla de verdad.
