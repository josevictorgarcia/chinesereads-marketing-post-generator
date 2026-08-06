# SETUP — de cero a publicar solo

Coste total: **0 €/mes**. Tiempo: una tarde para Instagram, más la auditoría de TikTok si la quieres.

Lo importante que descubrí antes de escribir esto:

- **Instagram no necesita App Review en tu caso.** Meta lo dice explícitamente: <cite index="54-1">si tu app solo da servicio a tu propia cuenta profesional de Instagram o a una que gestionas, el Standard Access es todo lo que necesitas.</cite> Las 2-4 semanas de revisión son para apps que sirven a cuentas de terceros. La tuya no. Te ahorras el trámite entero.
- **TikTok sí tiene un muro.** <cite index="31-1">Todo el contenido publicado por clientes sin auditar queda restringido a modo privado.</cite> Por eso el script trae `TIKTOK_MODE=draft` por defecto: la publicación va a tus borradores y la sacas con un toque. Es lo que se puede hacer sin auditoría.

---

## Paso 0 — El dominio (hazlo primero)

Las dos APIs descargan las imágenes desde una URL pública, y TikTok además exige que el dominio sea verificadamente tuyo. <cite index="65-1">La URL tiene que estar en un dominio verificado en el portal de TikTok con una meta etiqueta o un registro DNS. Si tus ficheros están en un CDN como S3 o Cloudflare R2, tienes que verificar ese host exacto. Las URLs firmadas de un bucket sin verificar se rechazan con `url_ownership_unverified`.</cite>

Como ya tienes `chinesereads.com`, esto es trivial: **usa un subdominio tuyo**.

1. Cloudflare → R2 → crea un bucket (`chinesereads-media`).
2. Settings → Public access → **Connect a custom domain** → `cdn.chinesereads.com`.
3. R2 → Manage API tokens → crea uno con permiso de escritura sobre ese bucket. Apunta *Access Key ID*, *Secret* y el endpoint `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.

El plan gratuito de R2 sobra: tus carruseles pesan unos 5 MB.

> **No uses la URL `*.r2.dev`** que Cloudflare da por defecto. No la puedes verificar en TikTok porque no es tuya, y te vas a comer el `url_ownership_unverified` sin entender por qué.

---

## Paso 1 — Instagram (~1 hora, sin revisión)

1. Tu cuenta de Instagram tiene que ser **Profesional** (Empresa o Creador). Ajustes → Tipo de cuenta.
2. developers.facebook.com → **My Apps → Create App**. Caso de uso: *Other*. Tipo: *Business*.
3. En la app, añade el producto **Instagram** → *API setup with Instagram login*.
4. Añade los permisos `instagram_business_basic` e `instagram_business_content_publish`.
5. En esa misma pantalla, **Generate token** con tu cuenta de Instagram. Sale un token de larga duración y tu *Instagram user ID*.
6. Al `.env`: `IG_USER_ID` e `IG_ACCESS_TOKEN`.

**Deja la app en modo Development.** No la pases a Live y no la mandes a revisión: solo va a tocar tu cuenta, y en Development eso funciona.

El token dura 60 días. Refréscalo con:

```bash
python publish.py --refresh-ig-token
```

Ponlo en el calendario cada mes. Si caduca, el pipeline se para en silencio y no te enteras hasta que echas de menos un post.

**Límites:** <cite index="44-1">100 publicaciones por API cada 24 horas; un carrusel cuenta como una.</cite> No es tu problema.

---

## Paso 2 — TikTok (~1 hora, y luego decides)

1. developers.tiktok.com → Manage apps → crea la app.
2. Añade el producto **Content Posting API**.
3. **URL properties** → añade `cdn.chinesereads.com` y verifícalo (meta etiqueta o DNS). <cite index="58-1">Verificado un prefijo, todas las URLs con ese prefijo exacto se consideran tuyas.</cite>
4. Scopes: `video.upload` para borradores, `video.publish` si vas a por el directo.
5. Haz el OAuth una vez (redirect URI **https**, TikTok rechaza localhost) y guarda el `refresh_token`.
6. Al `.env`: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`.

Ahora eliges:

| | `TIKTOK_MODE=draft` | `TIKTOK_MODE=direct` |
|---|---|---|
| Auditoría | no | sí |
| Resultado | borrador en tu app, un toque para publicar | publicado solo |
| Cuándo | ya, hoy | cuando pases la auditoría |

<cite index="66-1">La auditoría convierte una tarea de programación en un proyecto de cumplimiento</cite> y tarda de días a semanas. Empieza en `draft`, y si el toque diario te molesta, la solicitas. Puedes cambiar la variable sin tocar código.

---

## Paso 3 — Publicar

```bash
cp .env.example .env      # y rellénalo
pip install -r requirements.txt

python write_post.py "characters sharing the 青 phonetic" --build
python publish.py output/qing --dry-run     # sube y enseña el payload
python publish.py output/qing               # va de verdad
```

`--dry-run` sube las imágenes y te muestra exactamente lo que se enviaría, sin publicar. Úsalo la primera vez: los errores de configuración salen ahí, no en producción.

Cada carpeta guarda un `.published.json` cuando se publica, así que no hay duplicados aunque ejecutes dos veces.

---

## Paso 4 — Que corra solo

`.github/workflows/publish.yml` publica el carrusel que toque cada martes y viernes. Sube los secretos a **Settings → Secrets and variables → Actions**.

O en tu propia máquina:

```cron
0 10 * * 2,5  cd ~/chinesereads-carousel && .venv/bin/python publish.py $(ls -d output/*/ | head -1)
```

Ojo con la ruta: `cron` **no hereda** el entorno virtual que activas en tu terminal. Si pones `python` a secas usará el del sistema y no encontrará las librerías. Siempre `.venv/bin/python`.

---

## Qué es "sin hacer nada" de verdad

Siendo honesto contigo, porque es lo que preguntabas:

| | Trabajo tuyo |
|---|---|
| Instagram | **cero**, una vez configurado |
| TikTok en `draft` | un toque en el móvil por post |
| TikTok en `direct` | cero, tras la auditoría |
| Revisar el JSON | ~30 segundos por post |

Ese último lo pongo a propósito. Puedes saltártelo encadenando `write_post.py --build` con `publish.py` en el mismo cron y no volver a mirarlo. Pero un tono mal puesto en una cuenta que enseña chino se nota, y no lo vas a ver hasta que te lo diga alguien en comentarios. Treinta segundos de revisión es el mejor negocio de todo este pipeline.

---

## Cuando algo falle

| Síntoma | Causa casi segura |
|---|---|
| `url_ownership_unverified` | el prefijo de URL no coincide con el verificado en TikTok |
| Instagram devuelve error de permisos | falta `instagram_business_content_publish` o el token caducó |
| El carrusel sale recortado raro | <cite index="40-1">Instagram recorta todas las imágenes a la proporción de la primera</cite> |
| TikTok se queda en `PROCESSING_UPLOAD` | tus URLs no son accesibles públicamente, o redirigen |
| TikTok publica pero solo lo ves tú | app sin auditar: `SELF_ONLY` forzado |

<cite index="58-1">Las URLs deben usar https y no redirigir a otra URL.</cite> Si pones un redirect delante del CDN, falla.
