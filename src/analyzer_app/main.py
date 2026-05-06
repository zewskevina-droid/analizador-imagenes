from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Literal

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage
from autogen_core import Image as AGImage
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

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


class ImageDescription(BaseModel):
    scene: str = Field(description="En resumen, la escena general de la imagen")
    message: str = Field(description="El mensaje que la imagen intenta transmitir")
    style: str = Field(description="El estilo artistico de la imagen")
    orientation: Literal["retrato", "paisaje", "cuadrado"] = Field(
        description="La orientacion de la imagen"
    )


def parse_image_description(raw_content: object) -> ImageDescription | None:
    if isinstance(raw_content, ImageDescription):
        return raw_content

    text = str(raw_content).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return ImageDescription.model_validate_json(text)
    except ValueError:
        try:
            return ImageDescription.model_validate(json.loads(text))
        except (ValueError, json.JSONDecodeError, TypeError):
            return None


def build_image_metadata_tool(
    image: Image.Image,
    filename: str,
    content_type: str,
    size_bytes: int,
) -> FunctionTool:
    def inspect_image_metadata() -> dict[str, str | int | None]:
        """Obtiene datos tecnicos de la imagen cuando ayudan al analisis visual."""
        width, height = image.size
        if width > height:
            orientation = "paisaje"
        elif height > width:
            orientation = "retrato"
        else:
            orientation = "cuadrado"

        return {
            "filename": filename,
            "content_type": content_type,
            "width": width,
            "height": height,
            "orientation": orientation,
            "mode": image.mode,
            "format": image.format,
            "size_bytes": size_bytes,
        }

    return FunctionTool(
        inspect_image_metadata,
        name="inspect_image_metadata",
        description=(
            "Obtiene metadatos tecnicos de la imagen cargada: nombre, tipo, "
            "dimensiones, orientacion, modo, formato y peso en bytes."
        ),
        strict=True,
    )


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
) -> dict[str, object]:
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
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    try:
        pil_image = Image.open(BytesIO(image_bytes))
        pil_image.load()
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer la imagen. Sube un archivo de imagen valido.",
        ) from exc

    ag_image = AGImage(pil_image)
    multi_modal_message = MultiModalMessage(
        content=[clean_prompt, ag_image],
        source="User",
    )

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )
    describer = AssistantAgent(
        name="description_agent",
        model_client=model_client,
        tools=[
            build_image_metadata_tool(
                image=pil_image,
                filename=image.filename or "imagen",
                content_type=image.content_type or "unknown",
                size_bytes=len(image_bytes),
            )
        ],
        reflect_on_tool_use=True,
        max_tool_iterations=2,
        system_message=(
            "Se te da bien describir imagenes con detalle y tambien estructurar "
            "esa descripcion de forma clara. Describe la imagen que recibes con "
            "mucho detalle, incluyendo objetos, colores, personas, emociones, "
            "texto visible, estilo y mensaje probable. Si no puedes describir "
            "algo con certeza, dilo claramente. Puedes usar la herramienta "
            "inspect_image_metadata cuando necesites datos tecnicos como ancho, "
            "alto, formato u orientacion. No la uses si no aporta valor. "
            "Responde solamente con JSON valido, sin Markdown, con esta forma: "
            '{"scene": "...", "message": "...", "style": "...", '
            '"orientation": "retrato|paisaje|cuadrado"}.'
        ),
    )

    try:
        response = await describer.run(task=multi_modal_message)
        reply = response.messages[-1].content
        parsed_reply = parse_image_description(reply)
        if parsed_reply is not None:
            structured = parsed_reply.model_dump()
            analysis = (
                f"Escena:\n{parsed_reply.scene}\n\n"
                f"Mensaje:\n{parsed_reply.message}\n\n"
                f"Estilo:\n{parsed_reply.style}\n\n"
                f"Orientacion:\n{parsed_reply.orientation}"
            )
        else:
            structured = None
            analysis = str(reply)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo analizar la imagen con AutoGen/OpenAI: {exc}",
        ) from exc
    finally:
        await model_client.close()

    return {
        "analysis": analysis,
        "structured": structured,
        "model": model,
        "filename": image.filename or "imagen",
    }
