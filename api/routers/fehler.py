"""M3-09 + M3-10: Endpunkte für Fehler-Management."""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.config import ERROR_DIR

router = APIRouter(prefix="/fehler", tags=["Fehler"])


@router.get("")
async def liste_fehler():
    """Liste aller Fehler-Einträge aus den .fehler.json-Dateien."""
    if not ERROR_DIR.exists():
        return []

    eintraege = []
    for pfad in sorted(ERROR_DIR.rglob("*.fehler.json")):
        try:
            data = json.loads(pfad.read_text(encoding="utf-8"))
            # PDF-Pfad ermitteln
            pdf_pfad = pfad.with_suffix("").with_suffix(".pdf")  # .fehler.json → .pdf
            eintraege.append({
                **data,
                "hatPdf": pdf_pfad.exists(),
                "pfadKey": str(pfad.relative_to(ERROR_DIR)),
            })
        except Exception:
            continue
    return eintraege


@router.get("/download")
async def download_fehler_pdf(pfad_key: str):
    """Lädt das fehlerhafte PDF herunter. pfad_key = relativer Pfad unter ERROR_DIR."""
    pdf_pfad = ERROR_DIR / pfad_key.replace(".fehler.json", ".pdf")
    if not pdf_pfad.exists():
        raise HTTPException(status_code=404, detail="PDF nicht gefunden.")
    return FileResponse(
        path=str(pdf_pfad),
        media_type="application/pdf",
        filename=pdf_pfad.name,
    )
