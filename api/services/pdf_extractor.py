"""
M1-05 + M1-06: PDF-Extraktion mit pdfplumber.
Deterministisch, reproduzierbar — kein LLM im Parsing-Schritt.
"""
import logging
from pathlib import Path

import pdfplumber

logger = logging.getLogger(__name__)


class PdfExtractionError(Exception):
    """Wird geworfen wenn das PDF nicht verarbeitet werden kann."""
    def __init__(self, typ: str, meldung: str):
        self.typ = typ        # z.B. "NO_TABLES_FOUND", "PDF_UNREADABLE"
        self.meldung = meldung
        super().__init__(meldung)


def extract_pdf(pdf_path: Path) -> list[dict]:
    """
    Extrahiert alle Seiten eines PDFs mit Tabellen und Rohtext.

    Gibt eine Liste von Seiten-Dicts zurück:
    [
      {
        "seite": 1,
        "raw_text": "...",
        "tabellen": [
          {
            "index": 0,
            "bbox": (x0, y0, x1, y1),
            "daten": [["Spalte1", "Spalte2", ...], [...], ...]
          },
          ...
        ]
      },
      ...
    ]

    Raises:
        PdfExtractionError: Bei unlesbaren PDFs oder fehlenden Tabellen.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) == 0:
                raise PdfExtractionError("PDF_UNREADABLE", "PDF enthält keine Seiten.")

            seiten = []
            gesamt_tabellen = 0

            for page_num, page in enumerate(pdf.pages, start=1):
                raw_text = page.extract_text() or ""
                tabellen = _extract_tables_with_bbox(page)
                gesamt_tabellen += len(tabellen)

                seiten.append({
                    "seite": page_num,
                    "raw_text": raw_text,
                    "tabellen": tabellen,
                })

            if gesamt_tabellen == 0:
                raise PdfExtractionError(
                    "NO_TABLES_FOUND",
                    f"Keine Tabellen in '{pdf_path.name}' gefunden.",
                )

            logger.debug(
                "PDF extrahiert: %s — %d Seite(n), %d Tabelle(n)",
                pdf_path.name, len(seiten), gesamt_tabellen,
            )
            return seiten

    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError(
            "PDF_UNREADABLE",
            f"PDF konnte nicht geöffnet werden: {exc}",
        ) from exc


def _extract_tables_with_bbox(page) -> list[dict]:
    """
    M1-06: Erkennt alle Tabellen auf einer Seite via Bounding-Box-Analyse.
    Sortiert Tabellen nach vertikaler Position (obere zuerst).
    Ignoriert Tabellen mit < 2 Zeilen oder < 2 Spalten.
    """
    table_objects = page.find_tables()

    result = []
    for tbl in table_objects:
        daten = tbl.extract()

        # Mindestgröße: 2 Zeilen, 2 Spalten
        if not daten or len(daten) < 2:
            continue
        if not daten[0] or len(daten[0]) < 2:
            continue

        result.append({
            "bbox": tbl.bbox,   # (x0, top, x1, bottom)
            "daten": daten,
        })

    # Nach Y-Position sortieren (obere Tabelle zuerst)
    result.sort(key=lambda t: t["bbox"][1])

    # Index vergeben
    for i, t in enumerate(result):
        t["index"] = i

    return result
