"""M3-05 + M3-06: Pipeline-Steuerung über die API."""
import asyncio
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.config import INPUT_DIR
from api.pipeline import PipelineErgebnis, find_all_pdfs, process_pdf

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# In-Memory Job-Store (für Hackathon ausreichend)
_jobs: dict[str, dict[str, Any]] = {}


def _serialisiere(e: PipelineErgebnis) -> dict:
    return {
        "datei":       str(e.pdf_path.name),
        "status":      e.status,
        "fehlerTyp":   e.fehler_typ,
        "meldung":     e.meldung,
        "dauerMs":     e.dauer_ms,
        "ausgabePfad": str(e.ausgabe_pfad) if e.ausgabe_pfad else None,
        "konfidenzScore": e.konfidenz_score,
    }


def _run_pipeline_job(job_id: str, no_ai: bool = False) -> None:
    """Läuft in einem BackgroundTask (synchron, da process_pdf synchron ist)."""
    job = _jobs[job_id]
    pdfs = find_all_pdfs(INPUT_DIR)
    job["gesamt"] = len(pdfs)
    job["status"] = "läuft"

    for pdf in pdfs:
        ergebnis = process_pdf(pdf, dry_run=False, no_ai=no_ai)
        job["ergebnisse"].append(_serialisiere(ergebnis))
        job["verarbeitet"] += 1

    job["status"] = "abgeschlossen"


@router.post("/start")
async def start_pipeline(background_tasks: BackgroundTasks, no_ai: bool = False):
    """Startet einen asynchronen Batch-Pipeline-Lauf."""
    # Prüfen ob bereits ein Job läuft
    for j in _jobs.values():
        if j["status"] == "läuft":
            raise HTTPException(status_code=409, detail="Pipeline läuft bereits.")

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "jobId":       job_id,
        "status":      "gestartet",
        "gesamt":      0,
        "verarbeitet": 0,
        "ergebnisse":  [],
    }
    background_tasks.add_task(_run_pipeline_job, job_id, no_ai)
    return {"jobId": job_id, "status": "gestartet"}


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    """Status eines laufenden oder abgeschlossenen Jobs."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nicht gefunden.")
    return job


@router.get("/aktiv")
async def aktiver_job():
    """Gibt den aktuell laufenden Job zurück (oder null)."""
    for j in _jobs.values():
        if j["status"] == "läuft":
            return j
    return None


@router.post("/run-single")
async def run_single(background_tasks: BackgroundTasks, beruf: str, jahr: int, no_ai: bool = False):
    """Einzellauf für einen bestimmten Beruf."""
    from api.config import INPUT_DIR, ERROR_DIR
    from pathlib import Path

    # PDF in eingang/ oder fehler/ suchen
    kandidaten = list((INPUT_DIR / str(jahr) / beruf).glob("*.pdf"))
    if not kandidaten:
        kandidaten = list((ERROR_DIR / str(jahr) / beruf).glob("*.pdf"))
    if not kandidaten:
        raise HTTPException(status_code=404, detail=f"Kein PDF für '{beruf}/{jahr}' gefunden.")

    # PDF zurück in eingang/ verschieben falls aus fehler/
    pdf = kandidaten[0]
    if ERROR_DIR in pdf.parents:
        ziel = INPUT_DIR / str(jahr) / beruf / pdf.name
        ziel.parent.mkdir(parents=True, exist_ok=True)
        pdf.rename(ziel)
        pdf = ziel
        # Fehler-JSON löschen
        fehler_json = pdf.with_suffix(".fehler.json")
        if fehler_json.exists():
            fehler_json.unlink()

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "jobId":       job_id,
        "status":      "gestartet",
        "gesamt":      1,
        "verarbeitet": 0,
        "ergebnisse":  [],
    }

    def _run():
        ergebnis = process_pdf(pdf, dry_run=False, no_ai=no_ai)
        _jobs[job_id]["ergebnisse"].append(_serialisiere(ergebnis))
        _jobs[job_id]["verarbeitet"] = 1
        _jobs[job_id]["status"] = "abgeschlossen"

    background_tasks.add_task(_run)
    return {"jobId": job_id, "status": "gestartet"}
