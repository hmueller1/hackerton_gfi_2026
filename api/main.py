"""FastAPI-App — BPÜ Pipeline API (M3)."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.services.folder_manager import ensure_folder_structure
from api.routers import berufe, fehler, konfig, pipeline

app = FastAPI(
    title="BPÜ Pipeline API",
    description="KI-gestützte Datenextraktions-Pipeline für Berufsprüfungs-PDFs",
    version="1.0.0",
)

# CORS — für Entwicklung alle Origins erlauben; in Produktion FRONTEND_URL setzen
_frontend_url = os.getenv("FRONTEND_URL", "")
_cors_origins = (
    [o.strip() for o in _frontend_url.split(",") if o.strip()]
    if _frontend_url
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(berufe.router)
app.include_router(fehler.router)
app.include_router(konfig.router)
app.include_router(pipeline.router)


@app.on_event("startup")
async def startup():
    ensure_folder_structure()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
