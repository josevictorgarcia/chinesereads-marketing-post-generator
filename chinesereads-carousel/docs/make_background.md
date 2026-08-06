# `make_background.py` — fondos dibujados por código

Genera escenas de callejón con farolillos usando geometría. **Es ilustración, no fotografía.**

- **Necesita:** `pip install -r requirements.txt` con el [entorno virtual activo](../README.md#sobre-el-entorno-virtual) (sólo Pillow)
- **No necesita:** claves, internet, ni coste alguno

---

## Uso

```bash
python make_background.py                        # una aleatoria
python make_background.py --seed 42              # reproducible
python make_background.py --count 6              # una tanda
python make_background.py --palette dusk         # night | dusk | festival
python make_background.py --outdir /tmp/pruebas
```

Salen en `assets/backgrounds/` como `lanterns_<paleta>_<semilla>.jpg`, listas para poner en el JSON del post.

Con `--seed` el resultado es idéntico siempre. Si una te gusta, apunta el número y la puedes reproducir.

---

## Cómo está construida la escena

Un callejón en perspectiva con punto de fuga cerca del centro:

1. **Cielo** con degradado y un resplandor cálido al fondo del callejón, que es la fuente de luz de toda la escena.
2. **Dos muros laterales** en perspectiva, casi negros, con ventanas y carteles verticales que se encogen hacia la fuga.
3. **Tres guirnaldas de farolillos** cruzando, cada una más grande y más nítida que la anterior. Las lejanas van desenfocadas: es lo que da profundidad.
4. **Suelo** que refleja algo de luz, para que no sea negro plano.
5. **Viñeteado** que empuja la mirada al centro.

**Los muros van a los lados a propósito.** Una foto de barrio chino normal tiene el motivo justo en el centro, peleando con el título. Aquí el centro queda despejado.

---

## Ajustar

Las paletas están arriba del script, como tuplas `(cielo, resplandor, farolillo, brillo, edificios)`:

```python
PALETTES = {
    "night":    ((10, 14, 34), (158, 82, 62), (206, 38, 32), (255, 150, 70), (7, 7, 15)),
    ...
}
```

El resplandor va **abajo** a propósito: los edificios sólo se leen como silueta si tienen un fondo más claro detrás. Si lo inviertes, el skyline desaparece.

Para añadir una paleta, mete una entrada más en el diccionario y ya aparece en `--palette`.

---

## Limitación honesta

Todas las variantes comparten la misma estructura de callejón. Cambian la paleta, la posición de la fuga, el número y tamaño de farolillos, las ventanas y los carteles — pero la composición es la misma.

Sirve para probar el pipeline y para tapar huecos. Si publicas tres veces por semana, **se va a notar la repetición en tu feed**. Para producción, mézclalo con tus fotos reales o con `ai_background.py`.
