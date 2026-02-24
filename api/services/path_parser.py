"""M1-03: Metadaten (Beruf, Jahr) aus dem Unterordnerpfad ableiten."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_metadata(pdf_path: Path, base_input_dir: Path) -> dict:
    """
    Leitet Beruf und Jahr aus dem Ordnerpfad ab.

    Erwartet: base_input_dir/{jahr}/{beruf}/datei.pdf
    Fallback:  base_input_dir/{beruf}/datei.pdf  → jahr=None, Warnung

    Gibt dict zurück: {"beruf": str|None, "jahr": int|None, "dateiname": str}
    """
    try:
        rel = pdf_path.relative_to(base_input_dir)
    except ValueError:
        logger.error("PDF liegt nicht unter INPUT_DIR: %s", pdf_path)
        return {"beruf": None, "jahr": None, "dateiname": pdf_path.name}

    parts = rel.parts  # z.B. ("2026", "anlagenmechaniker", "pruefung.pdf")

    if len(parts) == 3 and parts[0].isdigit():
        # Normalfall: Jahr/Beruf/Datei
        return {
            "jahr": int(parts[0]),
            "beruf": _normalize_beruf(parts[1]),
            "dateiname": parts[2],
        }
    elif len(parts) == 2:
        # Fallback: Beruf/Datei — kein Jahr
        logger.warning(
            "Kein Jahresordner erkannt für %s — 'jahr' wird null gesetzt.", pdf_path.name
        )
        return {
            "jahr": None,
            "beruf": _normalize_beruf(parts[0]),
            "dateiname": parts[1],
        }
    else:
        logger.error(
            "Unerwartete Pfadstruktur: %s — erwartet: eingang/{jahr}/{beruf}/datei.pdf", rel
        )
        return {"beruf": None, "jahr": None, "dateiname": pdf_path.name}


def _normalize_beruf(name: str) -> str:
    """Normalisiert den Berufsordnernamen: Kleinbuchstaben, Leerzeichen → Bindestrich."""
    return name.lower().strip().replace(" ", "-")
