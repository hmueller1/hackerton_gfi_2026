"""Kern-Pipeline: orchestriert alle Schritte für eine einzelne PDF-Datei."""
import json
import logging
import time
from pathlib import Path

from api.config import INPUT_DIR, OUTPUT_DIR
from api.services.config_generator import KiKonfigFehler, generiere_konfig
from api.services.config_manager import KonfigFehltError, load_config
from api.services.file_router import archive_pdf, route_to_error
from api.services.path_parser import extract_metadata
from api.services.pdf_extractor import PdfExtractionError, extract_pdf
from api.services.schema_mapper import map_to_schema
from api.services.validation import validate_consistency, validate_schema

logger = logging.getLogger(__name__)


class PipelineErgebnis:
    """Ergebnis der Verarbeitung einer einzelnen PDF-Datei."""

    def __init__(self, pdf_path: Path):
        self.pdf_path        = pdf_path
        self.status: str     = "AUSSTEHEND"   # ERFOLG | FEHLER | UEBERSPRUNGEN | ZUR_REVIEW
        self.fehler_typ: str | None  = None
        self.meldung: str | None     = None
        self.ausgabe_pfad: Path | None = None
        self.dauer_ms: int           = 0
        self.konfidenz_score: int | None = None
        self.ki_begruendung: str | None  = None

    @property
    def emoji(self) -> str:
        return {
            "ERFOLG":       "✓",
            "FEHLER":       "✗",
            "UEBERSPRUNGEN": "⚠",
            "ZUR_REVIEW":   "~",
        }.get(self.status, "?")


def process_pdf(
    pdf_path: Path,
    dry_run: bool = False,
    no_ai:   bool = False,
) -> PipelineErgebnis:
    """
    Verarbeitet eine einzelne PDF-Datei vollständig:
    1. Metadaten aus Pfad
    2. PDF extrahieren
    3. Konfig laden — bei KONFIG_FEHLT: KI-Generierung (außer --no-ai)
    4. JSON-Schema mapping
    5. V1 + V2 validieren
    6. Ausgabe schreiben / Archivieren oder Fehler-Routing
    """
    ergebnis = PipelineErgebnis(pdf_path)
    start    = time.monotonic()

    meta  = extract_metadata(pdf_path, INPUT_DIR)
    beruf = meta.get("beruf")
    jahr  = meta.get("jahr")

    try:
        # ── Schritt 1: PDF extrahieren (vor Konfig-Lookup, da für KI-Schritt nötig) ──
        seiten = extract_pdf(pdf_path)

        # ── Schritt 2: Konfig laden ───────────────────────────────────
        try:
            konfig = load_config(beruf)

        except KonfigFehltError:
            # Kein vorhandener Konfig-Eintrag → KI-Generierung
            if no_ai:
                ergebnis.status    = "UEBERSPRUNGEN"
                ergebnis.fehler_typ = "KONFIG_FEHLT"
                ergebnis.meldung   = f"Keine Konfig für '{beruf}' — KI-Schritt deaktiviert (--no-ai)"
                route_to_error(
                    pdf_path, beruf, jahr,
                    "KONFIG_FEHLT", ergebnis.meldung,
                    dry_run=dry_run,
                )
                return ergebnis

            try:
                routing, konfig = generiere_konfig(beruf, seiten)
            except KiKonfigFehler as exc:
                ergebnis.status    = "FEHLER"
                ergebnis.fehler_typ = exc.fehler_typ
                ergebnis.meldung   = exc.meldung
                route_to_error(pdf_path, beruf, jahr, exc.fehler_typ, exc.meldung, dry_run=dry_run)
                return ergebnis

            if routing == "ZUR_REVIEW":
                ergebnis.status    = "ZUR_REVIEW"
                ergebnis.meldung   = "Konfidenz unter Schwellwert — manuelle Review erforderlich"
                ki_block = konfig.get("konfidenz")
                if isinstance(ki_block, dict):
                    ergebnis.konfidenz_score = ki_block.get("score")
                    ergebnis.ki_begruendung  = ki_block.get("begruendung")
                # PDF bleibt im Eingangsordner (kein Archivieren bei ZUR_REVIEW)
                return ergebnis

        # ── Schritt 3: JSON-Schema erzeugen ─────────────────────────
        result_json = map_to_schema(seiten, konfig, meta)

        # ── Schritt 4: V1 Schema-Gate ────────────────────────────────
        v1_ok, v1_msg = validate_schema(result_json)
        if not v1_ok:
            ergebnis.status    = "FEHLER"
            ergebnis.fehler_typ = "V1_SCHEMA_FEHLER"
            ergebnis.meldung   = v1_msg
            route_to_error(
                pdf_path, beruf, jahr, "V1_SCHEMA_FEHLER", v1_msg,
                details={"json_ausschnitt": str(result_json)[:500]},
                dry_run=dry_run,
            )
            return ergebnis

        # ── Schritt 5: V2 Konsistenz-Check ──────────────────────────
        v2_ok, v2_msg = validate_consistency(result_json)
        if not v2_ok:
            ergebnis.status    = "FEHLER"
            ergebnis.fehler_typ = "V2_KONSISTENZ_FEHLER"
            ergebnis.meldung   = v2_msg
            route_to_error(pdf_path, beruf, jahr, "V2_KONSISTENZ_FEHLER", v2_msg, dry_run=dry_run)
            return ergebnis

        # ── Schritt 6: JSON speichern + PDF archivieren ──────────────
        ausgabe_pfad = OUTPUT_DIR / f"{beruf}.json"
        if not dry_run:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            with open(ausgabe_pfad, "w", encoding="utf-8") as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            archive_pdf(pdf_path, beruf, jahr, dry_run=False)
        else:
            logger.info("[DRY-RUN] würde speichern: %s", ausgabe_pfad)

        ergebnis.status      = "ERFOLG"
        ergebnis.ausgabe_pfad = ausgabe_pfad

    except PdfExtractionError as exc:
        ergebnis.status    = "FEHLER"
        ergebnis.fehler_typ = exc.typ
        ergebnis.meldung   = exc.meldung
        route_to_error(pdf_path, beruf, jahr, exc.typ, exc.meldung, dry_run=dry_run)

    except Exception as exc:  # noqa: BLE001
        ergebnis.status    = "FEHLER"
        ergebnis.fehler_typ = "UNBEKANNTER_FEHLER"
        ergebnis.meldung   = str(exc)
        logger.exception("Unerwarteter Fehler bei %s", pdf_path.name)
        route_to_error(pdf_path, beruf, jahr, "UNBEKANNTER_FEHLER", str(exc), dry_run=dry_run)

    finally:
        ergebnis.dauer_ms = int((time.monotonic() - start) * 1000)

    return ergebnis


def find_all_pdfs(input_dir: Path) -> list[Path]:
    """Findet alle PDF-Dateien rekursiv im Eingangsordner."""
    return sorted(input_dir.rglob("*.pdf"))
