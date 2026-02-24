"""M3-07 + M3-08: Endpunkte für verarbeitete Berufe."""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.config import OUTPUT_DIR

router = APIRouter(prefix="/berufe", tags=["Berufe"])


@router.get("")
async def liste_berufe():
    """Liste aller erfolgreich verarbeiteten Berufe."""
    if not OUTPUT_DIR.exists():
        return []

    berufe = []
    for pfad in sorted(OUTPUT_DIR.glob("*.json")):
        try:
            data = json.loads(pfad.read_text(encoding="utf-8"))
            meta = data.get("metadaten", {})
            berufe.append({
                "beruf":           pfad.stem,
                "beschreibung":    data.get("beschreibung", ""),
                "prüfungsTyp":     data.get("prüfungsTyp", ""),
                "berufNr":         data.get("berufNr", []),
                "anzahlBereiche":  len(data.get("prüfungsbereiche", [])),
                "jahr":            meta.get("jahr"),
                "verarbeitetAm":   meta.get("verarbeitetAm"),
                "konfigVersion":   meta.get("konfigVersion"),
            })
        except Exception:
            continue
    return berufe


@router.get("/{beruf}")
async def get_beruf(beruf: str):
    """JSON-Daten eines einzelnen Berufs."""
    pfad = OUTPUT_DIR / f"{beruf}.json"
    if not pfad.exists():
        raise HTTPException(status_code=404, detail=f"Beruf '{beruf}' nicht gefunden.")
    data = json.loads(pfad.read_text(encoding="utf-8"))
    return JSONResponse(content=data)
