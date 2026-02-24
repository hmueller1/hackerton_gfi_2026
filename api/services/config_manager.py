"""M1-09 + M2-01 + M2-12: Konfig-Bibliothek laden, speichern, versionieren, freigeben."""
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml

from api.config import CONFIG_DIR, PENDING_DIR

logger = logging.getLogger(__name__)


class KonfigFehltError(Exception):
    """Wird geworfen wenn keine Konfig für einen Beruf gefunden wird."""


def load_config(beruf: str) -> dict:
    """
    Lädt die Konfig-Datei für einen Beruf.
    Sucht zuerst in CONFIG_DIR/{beruf}.yaml, dann in PENDING_DIR/{beruf}.review.yaml.

    Raises:
        KonfigFehltError: Wenn keine Konfig gefunden wird.
    """
    pfad = CONFIG_DIR / f"{beruf}.yaml"
    if pfad.exists():
        return _load_yaml(pfad)

    # Auch im pending-Ordner suchen (für Dry-Run in M4)
    pending_pfad = PENDING_DIR / f"{beruf}.review.yaml"
    if pending_pfad.exists():
        logger.warning("Konfig für '%s' nur im Pending-Ordner — noch nicht freigegeben.", beruf)
        return _load_yaml(pending_pfad)

    raise KonfigFehltError(
        f"Keine Konfig gefunden für Beruf '{beruf}'. "
        f"Erwartet: {pfad}"
    )


def config_exists(beruf: str) -> bool:
    """Prüft ob eine freigegebene Konfig für den Beruf existiert."""
    return (CONFIG_DIR / f"{beruf}.yaml").exists()


def save_config(beruf: str, konfig: dict, pending: bool = False) -> Path:
    """
    Speichert eine Konfig-Datei.
    pending=True → PENDING_DIR/{beruf}.review.yaml
    pending=False → CONFIG_DIR/{beruf}.yaml
    """
    if pending:
        ziel = PENDING_DIR / f"{beruf}.review.yaml"
    else:
        ziel = CONFIG_DIR / f"{beruf}.yaml"

    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        yaml.dump(konfig, f, allow_unicode=True, default_flow_style=False)

    logger.info("Konfig gespeichert: %s", ziel)
    return ziel


def approve_config(beruf: str) -> Path:
    """
    M2-12: Verschiebt eine Pending-Konfig in die aktive Konfig-Bibliothek.
    Führt einen Major-Version-Bump durch und markiert als 'manuell'.

    Returns:
        Zielpfad der freigegebenen Konfig.

    Raises:
        FileNotFoundError: Wenn keine Pending-Konfig existiert.
    """
    pending_pfad = PENDING_DIR / f"{beruf}.review.yaml"
    if not pending_pfad.exists():
        raise FileNotFoundError(f"Keine Pending-Konfig für '{beruf}': {pending_pfad}")

    konfig = _load_yaml(pending_pfad)
    konfig["erstelltDurch"] = "manuell"
    konfig["erstelltAm"]    = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Major-Bump bei manueller Freigabe
    version_str = str(konfig.get("version", "0.1"))
    try:
        teile   = version_str.split(".")
        major_v = int(teile[0]) + 1
        konfig["version"] = f"{major_v}.0"
    except (ValueError, IndexError):
        konfig["version"] = "1.0"

    ziel = CONFIG_DIR / f"{beruf}.yaml"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        yaml.dump(konfig, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    pending_pfad.unlink()
    logger.info("Konfig freigegeben: %s → %s", pending_pfad.name, ziel)
    return ziel


def reject_config(beruf: str) -> None:
    """
    M2-12: Löscht eine Pending-Konfig (Ablehnung durch Reviewer).

    Raises:
        FileNotFoundError: Wenn keine Pending-Konfig existiert.
    """
    pending_pfad = PENDING_DIR / f"{beruf}.review.yaml"
    if not pending_pfad.exists():
        raise FileNotFoundError(f"Keine Pending-Konfig für '{beruf}': {pending_pfad}")
    pending_pfad.unlink()
    logger.info("Pending-Konfig abgelehnt und gelöscht: %s", pending_pfad)


def list_pending_configs() -> list[dict]:
    """Gibt alle Pending-Konfigs als Liste von Dicts zurück."""
    ergebnis = []
    for pfad in sorted(PENDING_DIR.glob("*.yaml")):
        try:
            k     = _load_yaml(pfad)
            ki    = k.get("konfidenz") or {}
            score = ki.get("score", "?") if isinstance(ki, dict) else "?"
        except Exception:
            score = "?"
        ergebnis.append({
            "beruf":   pfad.stem.replace(".review", ""),
            "pfad":    pfad,
            "score":   score,
            "version": "?"  # pending configs haben kein stabiles version-Feld
        })
    return ergebnis


def _load_yaml(pfad: Path) -> dict:
    try:
        with open(pfad, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Ungültiges YAML-Format in {pfad}")
        return data
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML-Syntaxfehler in {pfad}: {exc}") from exc
