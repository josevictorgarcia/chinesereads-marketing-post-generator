# `write_post.py` — escribir el post con Claude

Genera el JSON que consume `generate_carousel.py`, a partir de un tema.

- **Necesita:** `pip install -r requirements-ai.txt` con el [entorno virtual activo](../README.md#sobre-el-entorno-virtual) + `ANTHROPIC_API_KEY`
- **Opcional:** puedes escribir los JSON a mano y no usar esto nunca

---

## Uso

```bash
export ANTHROPIC_API_KEY=sk-ant-...          # o ponlo en .env

python write_post.py "characters that share the 青 phonetic component"
python write_post.py "HSK3 verbs about travelling" --slides 6
python write_post.py "measure words for animals" --bg tea_fields.jpg
python write_post.py "tones that change in pairs" --build
```

| Opción | Qué hace |
|---|---|
| `--slides N` | número de slides de contenido (5 por defecto) |
| `--bg FICHERO` | foto concreta de `assets/backgrounds/`; si no, elige una al azar |
| `--build` | renderiza el carrusel al terminar, sin pasar por revisión |

Escribe `posts/<slug>.json` y te imprime un resumen:

```
✓ posts/qing.json
  portada:  Is "qing" the most mistaken Chinese character?
  青  qīng       blue-green / youth
  晴  qíng       clear / sunny (weather)
  ...
```

---

## Qué le pide a Claude

El system prompt está en la constante `SYSTEM`, arriba del script. Fija:

- Título de portada: gancho, pregunta o afirmación sorprendente, máximo 55 caracteres
- Subtítulo: máximo 40 caracteres
- Una sola cosa por slide
- `meaning` de 32 caracteres como mucho, con `/` para separar acepciones
- Pinyin con marcas tonales correctas, en minúscula
- Caption de 2-3 frases que aporte algo que no esté en un diccionario

Devuelve sólo JSON, sin markdown ni preámbulo. Si algún día responde algo que no parsea, el script te enseña los primeros 600 caracteres para que veas qué pasó.

Ajusta `SYSTEM` hasta que el tono sea el tuyo. Es lo que más rendimiento da de todo el proyecto: el resto es fontanería.

---

## Revisa antes de renderizar

`--build` encadena generación y render sin parar. Cómodo, pero:

**Los tonos y los significados son justo donde un error te cuesta credibilidad.** Tu cuenta enseña chino; un `qíng` donde iba `qǐng` lo va a ver alguien y te lo va a decir en comentarios. Corregir una línea del JSON son diez segundos, y es el mejor negocio de todo el pipeline.

Yo lo usaría sin `--build`, mirando el resumen que imprime, y renderizando después.

---

## Cambiar de modelo

```python
MODEL = "claude-sonnet-4-6"
```

Arriba del script. Cualquier modelo con acceso por API te vale.
