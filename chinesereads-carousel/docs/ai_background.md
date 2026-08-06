# `ai_background.py` — fondos fotorrealistas por IA

Llama a una API de generación de imágenes y deja el resultado en `assets/backgrounds/`.

- **Necesita:** `pip install -r requirements-ai.txt` con el [entorno virtual activo](../README.md#sobre-el-entorno-virtual) + `OPENAI_API_KEY`
- **Coste:** menos de un céntimo por imagen con `gpt-image-1-mini`

---

## Uso

```bash
export OPENAI_API_KEY=sk-...                 # o ponlo en .env

python ai_background.py --list                            # ver presets
python ai_background.py --preset chinatown_night
python ai_background.py --preset tea_hills --count 3
python ai_background.py "a red temple gate in the rain"
python ai_background.py --preset old_town --quality high
```

| Opción | Qué hace |
|---|---|
| `--preset NOMBRE` | escena predefinida |
| `--count N` | cuántas generar |
| `--quality` | `low`, `medium` (por defecto), `high` |
| `--list` | lista los presets |

Presets incluidos: `chinatown_night`, `chinatown_day`, `tea_hills`, `old_town`, `night_market`, `calligraphy`.

---

## El sufijo de estilo importa

Todos los prompts llevan pegada la constante `STYLE`:

```
photorealistic, shot on a 35mm lens, natural available light,
shallow depth of field, uncluttered composition with open space in
the upper middle of the frame, no text, no watermark, no people
facing the camera
```

Lo importante es **"open space in the upper middle of the frame"**. Sin eso, los modelos devuelven composiciones centradas y simétricas que pelean con el título. La parte de `no text` es igual de necesaria: si no, muchos modelos incrustan pseudo-caracteres chinos inventados que se ven mal y que además quedan debajo de tu texto.

---

## Cambiar de proveedor

La función `generate()` es lo único atado a OpenAI. Sólo tiene que devolver bytes de una imagen cuadrada. Para usar Flux, Ideogram, Replicate o fal, reescribe esa función y no toques nada más.

El modelo se cambia con la variable de entorno `IMAGE_MODEL`.

---

## Revisa lo que sale

Los modelos siguen incrustando texto inventado de vez en cuando, sobre todo si el prompt menciona carteles o letreros. En una cuenta que enseña chino, un cartel con caracteres sin sentido es peor que no poner foto.

Míralas antes de meterlas en `assets/backgrounds/` para uso real.
