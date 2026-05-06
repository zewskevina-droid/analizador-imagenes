# Analizador de imagenes con chat

Proyecto Python normal basado en el notebook `2_lab2_autogen_agentchat.ipynb`.

La app permite seleccionar una imagen en un chat, escribir una instruccion y recibir un analisis visual usando la API de OpenAI.

## Importante sobre GitHub Pages

GitHub Pages solo publica archivos estaticos: HTML, CSS y JavaScript. No ejecuta Python.

Por eso este repo queda dividido asi:

- `src/analyzer_app/`: backend Python con FastAPI. Hace el analisis real de la imagen.
- `docs/`: frontend estatico listo para publicar en GitHub Pages.

En local, FastAPI sirve tambien el frontend. En GitHub Pages, el frontend debe apuntar a la URL donde tengas desplegado el backend Python.

## Requisitos

- Python 3.10 o superior.
- Una API key de OpenAI.

## Instalacion local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edita `.env` y agrega tu `OPENAI_API_KEY`.

## Ejecutar local

```bash
uvicorn analyzer_app.main:app --app-dir src --reload
```

Abre:

```text
http://127.0.0.1:8000
```

## Publicar frontend en GitHub Pages

1. Sube el repo a GitHub.
2. En GitHub, entra a `Settings > Pages`.
3. En `Build and deployment`, selecciona `GitHub Actions`.
4. Haz push a `main`.

Pagina publicada:

```text
https://zewskevina-droid.github.io/analizador-imagenes/
```

## Desplegar backend en Render

La pagina publicada en GitHub Pages necesita una URL de backend. El archivo `render.yaml` ya deja configurado un servicio web para Render.

Pasos:

1. Entra a Render.
2. Crea un `New > Blueprint`.
3. Selecciona este repositorio de GitHub.
4. Render detectara `render.yaml`.
5. Agrega la variable secreta `OPENAI_API_KEY`.
6. Crea el servicio.
7. Copia la URL publica del servicio, por ejemplo:

```text
https://analizador-imagenes-api.onrender.com
```

8. Abre la pagina de GitHub Pages.
9. Haz clic en el boton de configuracion, pega la URL de Render en `Backend` y guarda.

Tambien puedes desplegar el backend en Railway, Fly.io, Azure App Service, Google Cloud Run o un VPS.

Variables necesarias:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
ALLOWED_ORIGINS=https://zewskevina-droid.github.io
```

`ALLOWED_ORIGINS` debe incluir la URL real de GitHub Pages para que el navegador pueda llamar al backend.

## Estructura

```text
.
+-- docs/
|   +-- app.js
|   +-- index.html
|   +-- styles.css
+-- src/
|   +-- analyzer_app/
|       +-- __init__.py
|       +-- main.py
+-- .env.example
+-- render.yaml
+-- requirements.txt
+-- README.md
```
