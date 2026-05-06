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

## Ejecutar

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
3. En `Build and deployment`, selecciona:
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/docs`
4. Guarda.

Cuando el sitio este publicado, abre la configuracion de la pagina y escribe la URL de tu backend Python en el campo `Backend`.

## Desplegar backend

Puedes desplegar el backend en servicios que ejecuten Python, por ejemplo Render, Railway, Fly.io, Azure App Service, Google Cloud Run o un VPS.

Variables necesarias:

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
ALLOWED_ORIGINS=https://tu-usuario.github.io
```

`ALLOWED_ORIGINS` debe incluir la URL real de GitHub Pages para que el navegador pueda llamar al backend.

## Estructura

```text
.
├── docs/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── src/
│   └── analyzer_app/
│       ├── __init__.py
│       └── main.py
├── .env.example
├── requirements.txt
└── README.md
```

