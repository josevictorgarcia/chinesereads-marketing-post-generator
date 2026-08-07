# `generate_carousel.py` — generar el carrusel

**La herramienta central.** Todas las demás son opcionales; ésta no.

Convierte un JSON en las imágenes del carrusel más el texto del pie.

- **Necesita:** `pip install -r requirements.txt` con el [entorno virtual activo](../README.md#sobre-el-entorno-virtual) (Pillow y fontTools)
- **No necesita:** claves de API, internet, ni ninguna otra herramienta

---

## Uso

```bash
python generate_carousel.py posts/qing.json          # un post
python generate_carousel.py posts/                   # toda la carpeta
python generate_carousel.py posts/qing.json -o /tmp  # otra salida
python generate_carousel.py posts/qing.json --format jpg
```

Resultado:

```
output/qing/
├── 01_portada.png      foto + título + subtítulo + logo
├── 02_青.png            \
├── 03_晴.png             |  una por cada entrada de "slides"
├── ...                  /
├── 07_promo.png        tu slide fija de promoción
└── caption.txt         pie de foto con hashtags, listo para copiar
```

Las imágenes van numeradas para que el orden alfabético sea el orden del carrusel. Cualquier programador (Metricool, Buffer) o el propio `publish.py` las lee en ese orden sin configurar nada.

---

## El JSON

```json
{
  "slug": "qing",
  "cover": {
    "background": "assets/backgrounds/tea_fields.jpg",
    "title": "Is \"qing\" the most mistaken Chinese character?",
    "subtitle": "Swipe to see the different types",
    "auto_contrast": true,
    "darken": 0.0
  },
  "slides": [
    { "hanzi": "青", "pinyin": "qīng", "meaning": "blue-green / youth" },
    { "hanzi": "晴", "pinyin": "qíng", "meaning": "clear / sunny (weather)" }
  ],
  "caption": "Texto principal del pie.",
  "cta": "Read real Chinese texts for free at chinesereads.com 📖 (link in bio)",
  "hashtags": ["#learnchinese", "#chinesereads"],
  "include_final": true
}
```

| Campo | Obligatorio | Qué hace |
|---|---|---|
| `slug` | sí | nombre de la carpeta de salida |
| `cover.background` | sí | ruta a la foto, relativa a la raíz del proyecto |
| `cover.title` | sí | se auto-ajusta de tamaño, no cuentes caracteres |
| `cover.subtitle` | no | el "swipe to see…" |
| `cover.auto_contrast` | no | `false` lo desactiva para este post |
| `cover.darken` | no | oscurecimiento global extra, 0–1, además del automático |
| `slides[]` | sí | `hanzi` obligatorio; `pinyin` y `meaning` opcionales |
| `caption` | no | texto del pie |
| `cta` | no | llamada a la acción; hay una por defecto |
| `hashtags` | no | lista; hay unos por defecto |
| `include_final` | no | `false` omite la slide de promoción |

`hanzi` acepta caracteres sueltos, palabras y frases cortas. El tamaño se reduce solo según la longitud.

`caption.txt` se monta así: `caption` + vocabulario de las slides + `cta` + hashtags, separados por líneas en blanco.

---

## Contraste automático de la portada

Aquí es donde esto se rompía: texto blanco sobre una foto cualquiera. Un campo de té va bien; un cielo o una playa se comen las letras.

El script mide la luminancia real **de la banda concreta donde va cada texto**, y sólo de esa banda, después del recorte cuadrado. Luego oscurece ahí con un degradado suave.

Dos factores por separado:

- **Brillo** — cuánto hay que bajar la luminancia media hasta `target_luma` (96).
- **Detalle** — la desviación típica. Un fondo movido rompe la silueta de las letras aunque sea oscuro de media, así que suma un extra vía `busy_bonus`.

El total se limita a `scrim_max` (0.72) para no convertir la foto en un rectángulo negro. En consola sale el valor aplicado a cada una de las tres bandas:

```
     scrim: 0.09  0.11  0.02     <- callejón nocturno: apenas hace nada
     scrim: 0.43  0.32  0.42     <- campo de té
     scrim: 0.65  0.64  0.65     <- fondo casi blanco
```

Si algo queda muy oscuro o muy claro, mueve `target_luma` en la clase `Theme`.

---

## Cambiar el diseño

Todo lo visual está en la clase `Theme`, arriba del script. Las posiciones son fracciones de 1080, así que si cambias `SIZE` el diseño escala solo.

```python
red: str = "#F42C1E"        # rojo de hanzi, pinyin y significado
hanzi_y: float = 0.200      # centro vertical del carácter
hanzi_size: int = 165
cover_stroke_w: int = 9     # grosor del contorno negro del título
target_luma: float = 96.0   # umbral del auto-contraste
```

Para pasar a 4:5 (ocupa más pantalla en Instagram) cambia `SIZE` por una tupla `(1080, 1350)` y reajusta las fracciones. **Cámbialo en todas las slides a la vez:** Instagram recorta todas las imágenes de un carrusel a la proporción de la primera.

---

## Fuentes

El generador prueba, para cada rol, la primera fuente que exista: primero tu
`assets/fonts/`, luego las de Linux, luego las de macOS.

| Rol | Linux | macOS |
|---|---|---|
| portada | Poppins Bold | Helvetica Neue Condensed Black |
| hanzi | Noto Sans CJK SC Black | Songti SC Black |
| pinyin y significado | Noto Sans CJK SC Black | Avenir Next Demi Bold |

**Por qué condensada en la portada:** entra más texto por línea, así el cuerpo
puede ser mayor sin que el título se parta en cuatro. Lo que decide si alguien
se para en el post es si el titular se lee en la miniatura del feed, a unos
160 px de lado.

**Por qué Songti en el hanzi:** es un estilo Ming, con remate en el trazo. Se
lee como caligrafía y acompaña al marco ornamental, en vez de parecer texto de
sistema.

**Cuidado con los tonos:** a la mayoría de fuentes de diseño les faltan los
glifos del tercer tono — `ǎ ǐ ǒ ǔ ǚ`. Un `qǐng` te saldría como un cuadrado
vacío. Todas las de la tabla los cubren. El script comprueba la cobertura antes
de dibujar y avisa por consola si detecta un glifo que falta, en vez de dejarte
publicar el cuadrado.

Para usar tu tipografía, mete los `.ttf` en `assets/fonts/` con estos nombres:

| Fichero | Se usa en |
|---|---|
| `Cover.ttf` | título y subtítulo de la portada |
| `Hanzi.ttf` | el carácter chino grande |
| `Latin.ttf` | pinyin, significado y el handle |

Si añades una fuente sin tonos completos, el aviso de consola te lo dirá en la primera ejecución.

---

## Los assets

| Fichero | Qué es |
|---|---|
| `assets/content_bg.png` | el marco y la textura de papel, sin texto |
| `assets/final_slide.png` | tu slide de promoción, fija |
| `assets/footer.png` | **el lockup de marca** (símbolo + logotipo), va en la portada |
| `assets/logo.png` | el símbolo suelto; lo sustituyó `footer.png` y ya no se usa |
| `assets/backgrounds/` | fotos de portada |

### La marca

`footer.png` es la versión oficial y manda sobre todo lo demás. Va en la
portada como imagen, con un halo blanco difuminado detrás para que el rojo se
lea igual sobre una foto clara que sobre una oscura — así no hay que tocar
nada al cambiar de fondo.

En las slides de contenido el nombre va **escrito**, no como imagen, para no
repetir el lockup entero siete veces. Se compone en la tipografía de marca
(`font_brand`: Charter Bold, la que más se acerca al logotipo) y en el rojo
oscuro de la paleta. Si tienes la tipografía original del logotipo, mete el
`.ttf` en `assets/fonts/Brand.ttf` y pasa a usarse sola.

`content_bg.png` y `logo.png` los saqué de tus imágenes de ejemplo: al primero le borré el texto por inpainting, del segundo recorté el logo y le añadí canal alfa.

**`backgrounds/tea_fields.jpg` lleva el texto antiguo incrustado**, porque es tu portada de ejemplo. Sustitúyela por la foto original limpia o verás el texto viejo por debajo del nuevo.

---

## Publicar lo generado

La carpeta de salida es autosuficiente: imágenes numeradas y `caption.txt`. A partir de ahí, como prefieras.

- **A mano** — arrastra las imágenes a Metricool, Buffer o la propia app, pega el caption. Cero configuración.
- **Con Google Drive** — apunta `-o` a una carpeta sincronizada y en Metricool las importas desde Drive sin tocar ficheros.
- **Por API** — ver [publish.md](publish.md).
