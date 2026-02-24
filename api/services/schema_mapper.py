"""
M1-08: Rohextraktion → einheitliches JSON-Schema.

Echte BPÜ-PDF-Struktur (aus Analyse von gesamt-bpue-w25-data_1.pdf):
  - 1 Tabelle pro Seite (nicht 2!)
  - Zeilen 1-N: Schriftliche Prüfung
  - Trennzeile: erste Spalte beginnt mit "Praktische Prüfung"
  - Danach: Praktische Prüfung mit optionalem ODER-Trenner
"""
import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Öffentliche API
# ─────────────────────────────────────────────────────────────────────

def map_to_schema(seiten: list[dict], konfig: dict, metadaten: dict) -> dict:
    seite_nr = konfig.get("seite", 1)
    seite = _get_seite(seiten, seite_nr)

    header = _parse_header(seite["raw_text"], konfig)

    tm = konfig.get("tabellenMapping", {})
    sk = tm.get("schriftlich", {})
    pk = tm.get("praktisch",   {})

    if "tabelleIndex" in tm:
        # ── Layout A: 1 kombinierte Tabelle, Split am "Praktische Prüfung"-Subheader ──
        tabelle = _get_tabelle(seite["tabellen"], int(tm["tabelleIndex"]))
        if not tabelle or len(tabelle) < 2:
            raise ValueError("Tabelle leer oder keine Datenzeilen vorhanden.")
        schr_zeilen, prakt_zeilen = _split_table(tabelle)
    else:
        # ── Layout B: separate Tabellen für schriftlich und praktisch ──
        schr_idx  = sk.get("tabelleIndex", 0)
        prakt_idx = pk.get("tabelleIndex", 1)
        schr_tab  = _get_tabelle(seite["tabellen"], schr_idx)
        prakt_tab = _get_tabelle(seite["tabellen"], prakt_idx)
        # Erste Zeile (Header) überspringen
        schr_zeilen  = schr_tab[1:]  if schr_tab  else []
        prakt_zeilen = prakt_tab[1:] if prakt_tab else []

    schriftliche_bereiche = _map_schriftlich(schr_zeilen, sk)
    praktische_bereiche   = _map_praktisch(prakt_zeilen,  pk)

    return {
        "berufNr":          header["berufNr"],
        "beschreibung":     header["beschreibung"],
        "prüfungsTyp":      header["prüfungsTyp"],
        "prüfungsbereiche": schriftliche_bereiche + praktische_bereiche,
        "metadaten": {
            "beruf":        metadaten.get("beruf"),
            "jahr":         metadaten.get("jahr"),
            "quelldatei":   metadaten.get("dateiname"),
            "verarbeitetAm": datetime.now(timezone.utc).isoformat(),
            "konfigVersion": konfig.get("version", "1.0"),
        },
    }


# ─────────────────────────────────────────────────────────────────────
# Header-Parsing
# ─────────────────────────────────────────────────────────────────────

def _parse_header(raw_text: str, konfig: dict) -> dict:
    beruf_nr_match = re.search(r'\((\d{4}(?:[,\s]+\d{4})*)\)', raw_text)
    beruf_nrs = (
        [n.strip() for n in beruf_nr_match.group(1).split(",")]
        if beruf_nr_match else []
    )

    beschreibung = ""
    if beruf_nr_match:
        vor_klammer = raw_text[:beruf_nr_match.start()].strip()
        zeilen = [z.strip() for z in vor_klammer.splitlines() if z.strip()]
        if zeilen:
            beschreibung = zeilen[-1]

    pruefungs_typ = konfig.get("prüfungsTyp") or _detect_pruefungstyp(raw_text)

    return {"berufNr": beruf_nrs, "beschreibung": beschreibung, "prüfungsTyp": pruefungs_typ}


def _detect_pruefungstyp(raw_text: str) -> str:
    t = raw_text.lower()
    if "abschlussprüfung teil 2" in t or "abschlusspruefung teil2" in t:
        return "abschlusspruefung-teil2"
    if "zwischenprüfung" in t:
        return "zwischenpruefung"
    if "abschlussprüfung" in t:
        return "abschlusspruefung"
    return "unbekannt"


# ─────────────────────────────────────────────────────────────────────
# Tabellen-Split
# ─────────────────────────────────────────────────────────────────────

def _split_table(tabelle: list[list]) -> tuple[list[list], list[list]]:
    """
    Teilt die Tabelle bei der "Praktische Prüfung"-Subheader-Zeile auf.
    Gibt (schriftliche_zeilen, praktische_zeilen) zurück.
    Zeile 0 (Haupt-Header) wird immer übersprungen.
    """
    split_idx = None
    for i, zeile in enumerate(tabelle[1:], start=1):
        cell = str(zeile[0] or "").strip()
        if re.search(r'praktische\s+pr[üu]', cell, re.IGNORECASE):
            split_idx = i
            break

    if split_idx is None:
        logger.warning("Kein 'Praktische Prüfung'-Subheader gefunden — alles als schriftlich behandelt.")
        return tabelle[1:], []

    return tabelle[1:split_idx], tabelle[split_idx + 1:]   # Subheader-Zeile selbst weglassen


# ─────────────────────────────────────────────────────────────────────
# Schriftliche Prüfung
# ─────────────────────────────────────────────────────────────────────

def _map_schriftlich(zeilen: list[list], sp: dict) -> list[dict]:
    """
    Verarbeitet die schriftlichen Prüfungszeilen.
    Jede Zeile mit nicht-leerem col0 = neuer Prüfungsbereich.
    Sub-Zeilen (col0=None) = zusätzliche Aufgabe im selben Bereich.
    """
    spalten = sp.get("spalten", {})
    c_name  = _col(spalten, "prüfungsbereich",       0)
    c_aufg  = _col(spalten, "aufgaben",              1)
    c_zeit  = _col(spalten, "vorgabezeit",           4)
    c_gib   = _col(spalten, "gewichtungImBereich",   5)
    c_gschr = _col(spalten, "gewichtungSchriftlich", 6)
    c_gt2   = _col(spalten, "gewichtungTeil2",       7)
    c_gges  = _col(spalten, "gewichtungGesamt",      8)

    bereiche: list[dict] = []
    aktuell: dict | None = None

    def _flush():
        if aktuell:
            bereiche.append(aktuell)

    for zeile in zeilen:
        if _is_empty_row(zeile):
            continue

        name_cell = _cell(zeile, c_name)

        if name_cell:
            # Neuer Prüfungsbereich
            _flush()
            aktuell = {
                "name":     _clean(name_cell),
                "typ":      "schriftlich",
                "varianten": None,
                "aufgaben": [],
                "gewichtung": {
                    "imPrüfungsbereich":  None,
                    "schriftlichePrüfung": _parse_pct(_cell(zeile, c_gschr)),
                    "teil2":              _parse_pct(_cell(zeile, c_gt2)),
                    "gesamtergebnis":     _parse_pct(_cell(zeile, c_gges)),
                },
            }

        # Aufgabe aus dieser Zeile
        if aktuell is not None:
            aufg = _make_aufgabe(
                aufg_text  = _cell(zeile, c_aufg),
                zeit_text  = _cell(zeile, c_zeit),
                gib        = _parse_pct(_cell(zeile, c_gib)),
            )
            if aufg:
                aktuell["aufgaben"].append(aufg)

    _flush()
    return bereiche


# ─────────────────────────────────────────────────────────────────────
# Praktische Prüfung
# ─────────────────────────────────────────────────────────────────────

def _map_praktisch(zeilen: list[list], pk: dict) -> list[dict]:
    """
    Verarbeitet die praktischen Prüfungszeilen.
    Spalten-Offset: col6=GewichtungPraktisch, col7=GewichtungTeil2
    ODER-Varianten werden durch Zeilen erkannt, in denen col0=='oder'.
    """
    if not zeilen:
        return []

    spalten = pk.get("spalten", {})
    c_name  = _col(spalten, "prüfungsbereich",    0)
    c_zeit  = _col(spalten, "vorgabezeit",        4)
    c_gprk  = _col(spalten, "gewichtungPraktisch",6)
    c_gt2   = _col(spalten, "gewichtungTeil2",    7)

    # t2 für den gesamten praktischen Block aus erster Datenzeile lesen
    t2_block: float | None = None
    for z in zeilen:
        val = _parse_pct(_cell(z, c_gt2))
        if val is not None:
            t2_block = val
            break

    # Varianten-Gruppen aufteilen
    varianten_gruppen = _split_by_oder(zeilen)

    if len(varianten_gruppen) == 1:
        # Keine ODER-Varianten
        name = _first_name(varianten_gruppen[0], c_name) or "Praktische Prüfung"
        gprk = _first_value(varianten_gruppen[0], c_gprk)
        return [{
            "name":     name,
            "typ":      "praktisch",
            "varianten": None,
            "aufgaben": [],
            "gewichtung": {
                "imPrüfungsbereich":  gprk,
                "schriftlichePrüfung": None,
                "teil2":              t2_block,
                "gesamtergebnis":     None,
            },
        }]

    # Mit ODER-Varianten → 1 Prüfungsbereich mit varianten[]
    varianten = []
    for gruppe in varianten_gruppen:
        if not gruppe:
            continue
        vname = _first_name(gruppe, c_name) or "Variante"
        gprk  = _first_value(gruppe, c_gprk)
        varianten.append({
            "bezeichnung": vname,
            "aufgaben":    [],
            "gewichtung": {
                "imPrüfungsbereich":  gprk,
                "schriftlichePrüfung": None,
                "teil2":              None,   # t2 liegt am Bereich, nicht an der Variante
                "gesamtergebnis":     None,
            },
        })

    return [{
        "name":     "Praktische Prüfung",
        "typ":      "praktisch",
        "varianten": varianten,
        "aufgaben": [],
        "gewichtung": {
            "imPrüfungsbereich":  None,
            "schriftlichePrüfung": None,
            "teil2":              t2_block,
            "gesamtergebnis":     None,
        },
    }]


def _split_by_oder(zeilen: list[list]) -> list[list]:
    gruppen, aktuell = [], []
    for z in zeilen:
        if z and any(isinstance(c, str) and c.strip().lower() == "oder" for c in z):
            if aktuell:
                gruppen.append(aktuell)
            aktuell = []
        else:
            aktuell.append(z)
    if aktuell:
        gruppen.append(aktuell)
    return gruppen or [zeilen]


def _first_name(zeilen: list[list], col: int) -> str | None:
    for z in zeilen:
        v = _cell(z, col)
        if v:
            return _clean(v)
    return None


def _first_value(zeilen: list[list], col: int) -> float | None:
    for z in zeilen:
        v = _parse_pct(_cell(z, col))
        if v is not None:
            return v
    return None


# ─────────────────────────────────────────────────────────────────────
# Hilfs-Funktionen
# ─────────────────────────────────────────────────────────────────────

def _get_seite(seiten: list[dict], nr: int) -> dict:
    for s in seiten:
        if s["seite"] == nr:
            return s
    return seiten[0]


def _get_tabelle(tabellen: list[dict], idx: int) -> list[list]:
    for t in tabellen:
        if t["index"] == idx:
            return t["daten"]
    if tabellen:
        return tabellen[0]["daten"]
    return []


def _col(spalten: dict, key: str, default: int) -> int:
    """Liest einen Spalten-Index aus dem Konfig-Dict.
    Gibt default zurück wenn der Key fehlt ODER explizit auf null gesetzt ist."""
    val = spalten.get(key)
    return val if isinstance(val, int) else default


def _cell(zeile: list, idx: int | None) -> str | None:
    if idx is None or idx >= len(zeile):
        return None
    val = zeile[idx]
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() != "none" else None


def _clean(text: str) -> str:
    return " ".join(text.split())


def _is_empty_row(zeile: list) -> bool:
    return all(z is None or str(z).strip() in ("", "None") for z in zeile)


def _parse_pct(text: str | None) -> float | None:
    if not text:
        return None
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*%', text.replace(",", "."))
    if m:
        try:
            v = float(m.group(1))
            return v if 0 <= v <= 100 else None
        except ValueError:
            return None
    return None


def _make_aufgabe(aufg_text: str | None, zeit_text: str | None, gib: float | None) -> dict | None:
    if not aufg_text:
        return None
    zeilen = aufg_text.strip().splitlines()
    bezeichnung = _clean(zeilen[0]) if zeilen else aufg_text[:80]
    return {
        "bezeichnung":       bezeichnung,
        "zeitMinuten":       _parse_zeit(zeit_text),
        "gewichtungImBereich": gib,
        "punkte":            None,
    }


def _parse_zeit(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*Std', text, re.IGNORECASE)
    if m:
        return int(float(m.group(1).replace(",", ".")) * 60)
    m = re.search(r'(\d+)\s*Min', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
