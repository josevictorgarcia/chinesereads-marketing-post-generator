# `publish.py` — publicar por API

Sube el carrusel a un bucket y lo publica en Instagram y TikTok.

- **Necesita:** `pip install -r requirements-publish.txt` con el [entorno virtual activo](../README.md#sobre-el-entorno-virtual) + bucket + credenciales de ambas redes
- **Totalmente opcional:** si no lo usas, sube las imágenes a mano y ya está

**El montaje completo, paso a paso, está en [../SETUP.md](../SETUP.md).** Este documento explica cómo funciona y cómo se usa una vez montado.

---

## Uso

```bash
python publish.py output/qing --dry-run       # sube y enseña el payload, no publica
python publish.py output/qing                 # va de verdad
python publish.py output/qing --only instagram
python publish.py output/qing --force         # republicar
python publish.py --refresh-ig-token          # renovar el token de Instagram
```

**Usa `--dry-run` la primera vez.** Sube las imágenes y te muestra exactamente lo que se enviaría. Los errores de configuración salen ahí, no en producción.

---

## Qué hace por dentro

**1. Subida.** Lee la carpeta, ordena las imágenes por nombre y las sube al bucket bajo `carousels/<slug>/`. Devuelve las URLs públicas.

Esto no es opcional: las dos plataformas **descargan** las imágenes desde una URL pública. No se envían los ficheros.

**2. Instagram** — modelo de contenedores, tres pasos:

- Un contenedor por imagen, con `is_carousel_item=true`
- Un contenedor padre `CAROUSEL` con la lista de hijos y el caption
- Espera a que el padre pase a `FINISHED` y entonces publica

La espera es necesaria: publicar antes de tiempo falla. Máximo 10 imágenes por carrusel; el script lo comprueba antes de empezar a subir.

**3. TikTok** — Content Posting API en modo foto. Renueva el access token con el refresh token (los de TikTok duran 24 h), inicia la publicación y consulta el estado hasta que termina.

**4. Estado.** Escribe `.published.json` en la carpeta. Si vuelves a lanzarlo, se para. `--force` lo salta.

---

## Los dos modos de TikTok

```bash
TIKTOK_MODE=draft     # va a tus borradores, publicas con un toque
TIKTOK_MODE=direct    # publica solo
```

`direct` necesita superar la auditoría de TikTok. Sin auditar, todo lo que publiques queda en modo privado y sólo lo ves tú — por eso `draft` es el valor por defecto.

Es una variable de entorno: puedes cambiarla el día que pases la auditoría sin tocar código.

En modo `direct` el script consulta antes los ajustes permitidos del creador y usa el nivel de privacidad más abierto que TikTok autorice. Enviar uno no permitido es un rechazo.

---

## Mantenimiento

**El token de Instagram caduca a los 60 días.**

```bash
python publish.py --refresh-ig-token
```

Ponlo en el calendario cada mes. Si caduca, el pipeline se para en silencio y no te enteras hasta que echas de menos un post.

**TikTok puede rotar el refresh token.** Si pasa, el script te avisa por consola con el nuevo valor para que lo pongas en `.env`.

---

## Errores frecuentes

| Síntoma | Causa casi segura |
|---|---|
| `url_ownership_unverified` | el prefijo de URL no coincide con el verificado en TikTok |
| Instagram: error de permisos | falta `instagram_business_content_publish` o el token caducó |
| El carrusel sale recortado raro | Instagram recorta todo a la proporción de la primera imagen |
| TikTok se queda en `PROCESSING_UPLOAD` | tus URLs no son accesibles, o redirigen |
| TikTok publica pero sólo lo ves tú | app sin auditar: privacidad forzada |

Las URLs deben ser `https` y **no redirigir**. Si pones un redirect delante del CDN, falla.

---

## Automatizar

`.github/workflows/publish.yml` coge el carrusel más antiguo sin publicar y lo publica martes y viernes. Los secretos van en Settings → Secrets and variables → Actions.

O en tu máquina:

```cron
0 10 * * 2,5  cd ~/chinesereads-carousel && .venv/bin/python publish.py $(ls -d output/*/ | head -1)
```

`cron` no hereda el entorno virtual de tu terminal: usa la ruta completa a `.venv/bin/python` o no encontrará boto3.
