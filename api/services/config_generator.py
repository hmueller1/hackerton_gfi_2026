"""
M2-05 bis M2-10: KI-gestützte Konfig-Generierung via Claude API.

Ablauf:
  1. Prompts laden (M2-05)
  2. Tabelleninhalt für Prompt aufbereiten
  3. Claude aufrufen (M2-03)
  4. YAML aus Antwort parsen (M2-06)
  5. Konfig-Struktur prüfen (M2-06)
  6. Dry-Run gegen echte PDF-Daten (M2-07)
  7. Konfidenz-Score lesen (M2-08)
  8. Routing: auto speichern oder pending (M2-09)
  9. Report schreiben (M2-08)
 10. Versionierung beim Speichern (M2-10)
"""
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from api.config import CONFIG_DIR, KONFIDENZ_SCHWELLWERT, PENDING_DIR, REPORTS_DIR
from api.services.ai_client import KiNichtVerfuegbarError, call_claude
from api.services.schema_mapper import map_to_schema
from api.services.validation import validate_consistency, validate_schema

logger = logging.getLogger(__name__)

PROMPTS_DIR   = Path(__file__).parent.parent / "prompts"
PFLICHT_FELDER = {"version", "beruf", "prüfungsTyp", "tabellenMapping"}


# ─────────────────────────────────────────────────────────────────────
# Öffentliche Ausnahme
# ─────────────────────────────────────────────────────────────────────

class KiKonfigFehler(Exception):
    """Fehler bei der KI-Konfig-Generierung mit Typ und Meldung."""

    def __init__(self, fehler_typ: str, meldung: str):
        self.fehler_typ = fehler_typ
        self.meldung    = meldung
        super().__init__(meldung)


# ─────────────────────────────────────────────────────────────────────
# Öffentliche API
# ─────────────────────────────────────────────────────────────────────

def generiere_konfig(beruf: str, seiten: list[dict]) -> tuple[str, dict]:
    """
    Orchestriert den kompletten KI-Konfig-Generierungsprozess.

    Returns:
        (routing, konfig_dict)
        routing: "AUTO_GESPEICHERT" | "ZUR_REVIEW"

    Raises:
        KiKonfigFehler: Bei API-Fehler, ungültigem YAML oder fehlenden Pflichtfeldern.
    """
    print("  Neuer Beruf erkannt — starte KI-Konfig-Generierung...")

    # ── Prompts laden (M2-05) ────────────────────────────────────────
    system_prompt = _lade_prompt("system_prompt.txt")
    user_template = _lade_prompt("user_prompt_template.txt")

    tabellen_text   = _formatiere_tabellen(seiten)
    anzahl_tabellen = sum(len(s.get("tabellen", [])) for s in seiten)
    layout_hinweis  = (
        "Layout A — tabelleIndex: 0 auf Top-Level (1 kombinierte Tabelle)"
        if anzahl_tabellen == 1 else
        f"Layout B — schriftlich.tabelleIndex: 0 + praktisch.tabelleIndex: 1 ({anzahl_tabellen} separate Tabellen)"
    )
    user_prompt = user_template.format(
        beruf              = beruf,
        seitenanzahl       = len(seiten),
        anzahl_tabellen    = anzahl_tabellen,
        layout_hinweis     = layout_hinweis,
        tabellen_rohinhalt = tabellen_text,
    )

    # ── Claude aufrufen (M2-03) ──────────────────────────────────────
    try:
        antwort = call_claude(system_prompt, user_prompt)
    except KiNichtVerfuegbarError as exc:
        raise KiKonfigFehler("KI_NICHT_VERFUEGBAR", str(exc)) from exc

    # ── YAML aus Antwort extrahieren (M2-06) ─────────────────────────
    konfig = _parse_yaml_aus_antwort(antwort)

    # ── Konfig-Struktur prüfen (M2-06) ───────────────────────────────
    ok, msg = _prüfe_konfig_struktur(konfig)
    if not ok:
        raise KiKonfigFehler("KI_KONFIG_UNVOLLSTAENDIG", msg)

    # ── Konfig mit Metadaten anreichern ──────────────────────────────
    heute = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    konfig.setdefault("beruf",        beruf)
    konfig.setdefault("erstelltAm",   heute)
    konfig["erstelltDurch"] = "ki"

    # ── Konfidenz auslesen (M2-08) ───────────────────────────────────
    score, begruendung, unsichere_felder = _lese_konfidenz(konfig)
    print(f"  Konfidenz: {score}/100 — '{begruendung}'")
    if unsichere_felder:
        print(f"  Unsichere Felder: {', '.join(unsichere_felder)}")

    # ── Dry-Run gegen echte Daten (M2-07) ────────────────────────────
    dry_run_ok, dry_run_status = _dry_run(konfig, seiten, beruf)
    symbol = "OK" if dry_run_ok else "FEHLER"
    print(f"  Dry-Run: {symbol} — {dry_run_status}")

    # ── Routing nach Schwellwert (M2-09) ─────────────────────────────
    if score >= KONFIDENZ_SCHWELLWERT and dry_run_ok:
        routing = "AUTO_GESPEICHERT"
        _speichere_konfig(beruf, konfig, pending=False)
        logger.info("Konfig fuer '%s' automatisch gespeichert (Score %d)", beruf, score)
    else:
        routing = "ZUR_REVIEW"
        grund = "score_unter_schwellwert" if score < KONFIDENZ_SCHWELLWERT else "dry_run_fehler"
        logger.info(
            "Konfig fuer '%s' → pending [%s, Score %d]", beruf, grund, score
        )
        _speichere_konfig(beruf, konfig, pending=True)

    # ── Report persistieren (M2-08) ──────────────────────────────────
    _speichere_report(beruf, score, begruendung, unsichere_felder, dry_run_status, routing)

    return routing, konfig


# ─────────────────────────────────────────────────────────────────────
# Prompt-Laden
# ─────────────────────────────────────────────────────────────────────

def _lade_prompt(dateiname: str) -> str:
    pfad = PROMPTS_DIR / dateiname
    if not pfad.exists():
        raise FileNotFoundError(f"Prompt-Datei nicht gefunden: {pfad}")
    return pfad.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────
# Tabelleninhalt für Prompt aufbereiten
# ─────────────────────────────────────────────────────────────────────

def _formatiere_tabellen(seiten: list[dict]) -> str:
    zeilen = []
    for seite in seiten:
        zeilen.append(f"=== Seite {seite['seite']} ===")
        raw = seite.get("raw_text", "")
        if raw:
            zeilen.append("Freitext der Seite (erste 500 Zeichen):")
            zeilen.append(raw[:500])
            zeilen.append("")
        for tabelle in seite.get("tabellen", []):
            zeilen.append(f"--- Tabelle Index {tabelle['index']} (BBox: {tabelle.get('bbox', '?')}) ---")
            for i, zeile in enumerate(tabelle["daten"]):
                zeilen.append(f"  Z{i:02d}: {zeile}")
            zeilen.append("")
    return "\n".join(zeilen)


# ─────────────────────────────────────────────────────────────────────
# YAML aus Claude-Antwort extrahieren (M2-06)
# ─────────────────────────────────────────────────────────────────────

def _parse_yaml_aus_antwort(antwort: str) -> dict:
    # Versuch 1: vollständiger ```yaml ... ``` Block
    match = re.search(r"```(?:yaml)?\n(.*?)```", antwort, re.DOTALL)
    if match:
        roh = match.group(1)
    else:
        # Versuch 2: öffnenden Codeblock-Header entfernen, Rest nehmen
        # (passiert wenn Antwort abgeschnitten wurde und ``` fehlt)
        roh = re.sub(r"^```(?:yaml)?\s*\n?", "", antwort.strip())
        roh = re.sub(r"```\s*$", "", roh.strip())

    try:
        result = yaml.safe_load(roh)
        if not isinstance(result, dict):
            raise ValueError("Kein gültiges YAML-Objekt (kein dict)")
        return result
    except yaml.YAMLError as exc:
        raise KiKonfigFehler(
            "KI_ANTWORT_UNGUELTIG",
            f"YAML der KI-Antwort nicht parsebar: {exc}"
        ) from exc


# ─────────────────────────────────────────────────────────────────────
# Konfig-Struktur prüfen (M2-06)
# ─────────────────────────────────────────────────────────────────────

def _prüfe_konfig_struktur(konfig: dict) -> tuple[bool, str | None]:
    fehlend = PFLICHT_FELDER - set(konfig.keys())
    if fehlend:
        return False, f"Pflichtfelder fehlen: {', '.join(sorted(fehlend))}"
    if not isinstance(konfig.get("tabellenMapping"), dict):
        return False, "tabellenMapping muss ein YAML-Objekt (dict) sein"
    return True, None


# ─────────────────────────────────────────────────────────────────────
# Konfidenz auslesen (M2-08)
# ─────────────────────────────────────────────────────────────────────

def _lese_konfidenz(konfig: dict) -> tuple[int, str, list]:
    ki = konfig.get("konfidenz")
    if not isinstance(ki, dict):
        logger.warning("Kein 'konfidenz'-Block in KI-Antwort — Score wird als 0 gewertet.")
        return 0, "Kein Konfidenz-Block vorhanden", []
    score       = max(0, min(100, int(ki.get("score", 0))))
    begruendung = str(ki.get("begruendung", ""))
    unsicher    = list(ki.get("unsichereFelder", []) or [])
    return score, begruendung, unsicher


# ─────────────────────────────────────────────────────────────────────
# Dry-Run: generierte Konfig gegen echte PDF-Daten testen (M2-07)
# ─────────────────────────────────────────────────────────────────────

def _dry_run(konfig: dict, seiten: list[dict], beruf: str) -> tuple[bool, str]:
    try:
        meta       = {"beruf": beruf, "jahr": 0, "dateiname": "dry-run"}
        result_json = map_to_schema(seiten, konfig, meta)

        v1_ok, v1_msg = validate_schema(result_json)
        if not v1_ok:
            return False, f"V1 fehlgeschlagen: {v1_msg}"

        v2_ok, v2_msg = validate_consistency(result_json)
        if not v2_ok:
            return False, f"V2 fehlgeschlagen: {v2_msg}"

        # Draft-JSON speichern (für manuelle Inspektion)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        draft_pfad = CONFIG_DIR / f"{beruf}.draft.json"
        with open(draft_pfad, "w", encoding="utf-8") as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)

        return True, "V1 OK, V2 OK"

    except Exception as exc:  # noqa: BLE001
        return False, f"Exception: {exc}"


# ─────────────────────────────────────────────────────────────────────
# Konfig speichern mit Versionierung (M2-10)
# ─────────────────────────────────────────────────────────────────────

def _speichere_konfig(beruf: str, konfig: dict, pending: bool) -> None:
    """Speichert die generierte Konfig, archiviert ggf. die Vorgänger-Version."""
    if pending:
        ziel = PENDING_DIR / f"{beruf}.review.yaml"
    else:
        ziel = CONFIG_DIR / f"{beruf}.yaml"

        # Bestehende Version archivieren (M2-10)
        if ziel.exists():
            _archiviere_alte_konfig(beruf, ziel)

        # Minor-Version automatisch erhöhen
        konfig = _bump_version(konfig, major=False)

    ziel.parent.mkdir(parents=True, exist_ok=True)
    with open(ziel, "w", encoding="utf-8") as f:
        yaml.dump(konfig, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    logger.info("Konfig gespeichert: %s", ziel)


def _bump_version(konfig: dict, major: bool) -> dict:
    """Erhöht die Versionsnummer (major: 1.x → 2.0 / minor: 1.0 → 1.1)."""
    verion_str = str(konfig.get("version", "1.0"))
    try:
        teile = verion_str.split(".")
        major_v = int(teile[0])
        minor_v = int(teile[1]) if len(teile) > 1 else 0
        if major:
            major_v += 1
            minor_v  = 0
        else:
            minor_v += 1
        konfig["version"] = f"{major_v}.{minor_v}"
    except (ValueError, IndexError):
        konfig["version"] = "1.0"
    return konfig


def _archiviere_alte_konfig(beruf: str, pfad: Path) -> None:
    """Verschiebt die bestehende Konfig ins Archiv."""
    try:
        with open(pfad, encoding="utf-8") as f:
            alt = yaml.safe_load(f)
        version = str(alt.get("version", "unbekannt"))
    except Exception:
        version = "unbekannt"

    datum  = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archiv = CONFIG_DIR / "archiv" / beruf
    archiv.mkdir(parents=True, exist_ok=True)
    ziel   = archiv / f"v{version}-{datum}.yaml"
    pfad.rename(ziel)
    logger.info("Alte Konfig archiviert: %s", ziel)


# ─────────────────────────────────────────────────────────────────────
# Report persistieren (M2-08)
# ─────────────────────────────────────────────────────────────────────

def _speichere_report(
    beruf: str,
    score: int,
    begruendung: str,
    unsichere_felder: list,
    dry_run_status: str,
    routing: str,
) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    datum  = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    report = {
        "beruf":           beruf,
        "zeitstempel":     datetime.now(timezone.utc).isoformat(),
        "score":           score,
        "begruendung":     begruendung,
        "unsichereFelder": unsichere_felder,
        "dryRunErgebnis":  dry_run_status,
        "routing":         routing,
    }
    pfad = REPORTS_DIR / f"ki-konfig-{beruf}-{datum}.json"
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info("KI-Report gespeichert: %s", pfad)
