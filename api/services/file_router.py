"""M1-12 + M1-13: Datei-Routing — Archivieren und Fehler ablegen."""
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from api.config import ARCHIVE_DIR, ERROR_DIR

logger = logging.getLogger(__name__)


def archive_pdf(pdf_path: Path, beruf: str, jahr: int | None, dry_run: bool = False) -> Path:
    """
    M1-12: Verschiebt ein erfolgreich verarbeitetes PDF ins Archiv.
    Zielstruktur: archiv/{jahr}/{beruf}/{dateiname}
    Bei Namenskonflikt wird _1, _2 etc. angehängt.
    """
    ziel_ordner = ARCHIVE_DIR / (str(jahr) if jahr else "unbekannt") / beruf
    ziel_pfad = _unique_path(ziel_ordner, pdf_path.name)

    if dry_run:
        logger.info("[DRY-RUN] würde archiviert: %s → %s", pdf_path.name, ziel_pfad)
        return ziel_pfad

    ziel_ordner.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pdf_path), str(ziel_pfad))
    logger.debug("Archiviert: %s", ziel_pfad)
    return ziel_pfad


def route_to_error(
    pdf_path: Path,
    beruf: str | None,
    jahr: int | None,
    fehler_typ: str,
    meldung: str,
    details: dict | None = None,
    dry_run: bool = False,
) -> Path:
    """
    M1-13: Verschiebt ein fehlerhaftes PDF in /fehler/ und schreibt Fehlerlog.
    Zielstruktur: fehler/{jahr}/{beruf}/{dateiname} + .fehler.json
    """
    ordner_name = str(jahr) if jahr else "unbekannt"
    beruf_name = beruf or "unbekannt"
    ziel_ordner = ERROR_DIR / ordner_name / beruf_name

    ziel_pdf = _unique_path(ziel_ordner, pdf_path.name)
    fehler_log = ziel_pdf.with_suffix("").with_suffix(".fehler.json")

    fehler_eintrag = {
        "datei": pdf_path.name,
        "beruf": beruf_name,
        "jahr": jahr,
        "zeitstempel": datetime.now(timezone.utc).isoformat(),
        "fehlerTyp": fehler_typ,
        "meldung": meldung,
        "details": details or {},
    }

    if dry_run:
        logger.info(
            "[DRY-RUN] würde in /fehler/ verschoben: %s [%s]",
            pdf_path.name, fehler_typ,
        )
        return ziel_pdf

    ziel_ordner.mkdir(parents=True, exist_ok=True)

    if pdf_path.exists():
        shutil.move(str(pdf_path), str(ziel_pdf))

    with open(fehler_log, "w", encoding="utf-8") as f:
        json.dump(fehler_eintrag, f, ensure_ascii=False, indent=2)

    logger.warning("Fehler [%s]: %s → %s", fehler_typ, pdf_path.name, ziel_pdf)
    return ziel_pdf


def _unique_path(ordner: Path, dateiname: str) -> Path:
    """Gibt einen eindeutigen Zielpfad zurück — hängt _1, _2 etc. an falls nötig."""
    ziel = ordner / dateiname
    if not ziel.exists():
        return ziel

    stem = Path(dateiname).stem
    suffix = Path(dateiname).suffix
    counter = 1
    while True:
        kandidat = ordner / f"{stem}_{counter}{suffix}"
        if not kandidat.exists():
            return kandidat
        counter += 1
