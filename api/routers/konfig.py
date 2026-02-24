"""M3-11: Endpunkte für die Konfig-Bibliothek."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

import yaml

from api.config import CONFIG_DIR, PENDING_DIR

router = APIRouter(prefix="/konfig", tags=["Konfig"])


@router.get("")
async def liste_konfigs():
    """Liste aller aktiven und pending Konfigs."""
    aktive = []
    for pfad in sorted(CONFIG_DIR.glob("*.yaml")):
        try:
            k = yaml.safe_load(pfad.read_text(encoding="utf-8"))
            ki = k.get("konfidenz") or {}
            aktive.append({
                "beruf":       pfad.stem,
                "version":     k.get("version", "?"),
                "erstelltDurch": k.get("erstelltDurch", "manuell"),
                "erstelltAm":  k.get("erstelltAm"),
                "score":       ki.get("score") if isinstance(ki, dict) else None,
                "pending":     False,
            })
        except Exception:
            continue

    pending = []
    for pfad in sorted(PENDING_DIR.glob("*.yaml")):
        try:
            k = yaml.safe_load(pfad.read_text(encoding="utf-8"))
            ki = k.get("konfidenz") or {}
            pending.append({
                "beruf":       pfad.stem.replace(".review", ""),
                "version":     k.get("version", "?"),
                "erstelltDurch": k.get("erstelltDurch", "ki"),
                "erstelltAm":  k.get("erstelltAm"),
                "score":       ki.get("score") if isinstance(ki, dict) else None,
                "begruendung": ki.get("begruendung") if isinstance(ki, dict) else None,
                "pending":     True,
            })
        except Exception:
            continue

    return {"aktiv": aktive, "pending": pending}


@router.get("/{beruf}")
async def get_konfig(beruf: str):
    """YAML-Inhalt einer Konfig als Plain-Text."""
    pfad = CONFIG_DIR / f"{beruf}.yaml"
    if not pfad.exists():
        pfad = PENDING_DIR / f"{beruf}.review.yaml"
    if not pfad.exists():
        raise HTTPException(status_code=404, detail=f"Konfig für '{beruf}' nicht gefunden.")
    return PlainTextResponse(pfad.read_text(encoding="utf-8"), media_type="text/yaml")


@router.post("/{beruf}/approve")
async def approve_konfig(beruf: str):
    """Pending-Konfig freigeben (Major-Bump)."""
    from api.services.config_manager import approve_config
    try:
        ziel = approve_config(beruf)
        return {"status": "freigegeben", "pfad": str(ziel)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{beruf}/pending")
async def reject_konfig(beruf: str):
    """Pending-Konfig ablehnen und löschen."""
    from api.services.config_manager import reject_config
    try:
        reject_config(beruf)
        return {"status": "abgelehnt"}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
