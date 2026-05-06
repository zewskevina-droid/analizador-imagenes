from __future__ import annotations

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, OpenAIError

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT_DIR / "docs"

DEFAULT_PROMPT = (
    "Describe el contenido de esta imagen con detalle. Incluye objetos, colores, "
    "personas, emociones, texto visible, estilo, mensaje probable y cualquier "
    "incertidumbre relevante."
)

SUPPORTED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
}

MAX_IMAGE_SIZE = 20 * 1024 * 1024


def _allowed_origins() -> list[str]:
    raw_value = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000",
    )
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


app = FastAPI(
    title="Analizador de imagenes",
    description="Backend Python para analizar imagenes desde un chat.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

if DOCS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DOCS_DIR), name="assets")


@app.get("/")
def index() -> FileResponse:
    index_file = DOCS_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend no encontrado.")
    return FileResponse(index_file)


@app.get("/styles.css")
def styles() -> FileResponse:
    styles_file = DOCS_DIR / "styles.css"
    if not styles_file.exists():
        raise HTTPException(status_code=404, detail="CSS no encontrado.")
    return FileResponse(styles_file)


@app.get("/app.js")
def app_js() -> FileResponse:
    script_file = DOCS_DIR / "app.js"
    if not script_file.exists():
        raise HTTPException(status_code=404, detail="JavaScript no encontrado.")
    return FileResponse(script_file)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: str = Form(DEFAULT_PROMPT),
) -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar OPENAI_API_KEY en el entorno del backend.",
        )

    if image.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Usa PNG, JPG, WEBP o GIF no animado.",
        )

    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="La imagen es demasiado grande. Usa una imagen menor a 20 MB.",
        )

    clean_prompt = prompt.strip() or DEFAULT_PROMPT
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{image.content_type};base64,{encoded_image}"

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": clean_prompt},
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo analizar la imagen con OpenAI: {exc}",
        ) from exc

    return {
        "analysis": response.output_text,
        "model": model,
        "filename": image.filename or "imagen",
    }
