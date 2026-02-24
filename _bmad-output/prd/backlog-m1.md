# Backlog M1 — Basis-Pipeline

**Meilenstein:** M1 — Basis-Pipeline lauffähig
**Release:** MVP
**Datum:** 2026-02-24
**Ziel:** End-to-End-Lauf: PDF rein → valides JSON raus. Kein LLM im kritischen Pfad. CLI-basiert.

---

## Definition of Done (M1)

- [ ] Ein einzelnes PDF aus `/eingang/2026/elektrotechnik/` wird zu `/ausgabe/elektrotechnik.json` verarbeitet
- [ ] V1 (Schema-Gate) und V2 (Numerische Konsistenz) blockieren fehlerhafte Extraktionen
- [ ] Fehlerhafte PDFs landen mit Fehlerlog in `/fehler/`, Originale nie verloren
- [ ] Erfolgreiche PDFs landen unverändert in `/archiv/`
- [ ] CLI-Ausgabe zeigt Status pro PDF

---

## Epics

| Epic | Beschreibung | Stories |
|------|-------------|---------|
| E1 | Ordner & Konfiguration | M1-01 bis M1-03 |
| E2 | PDF-Parsing & Extraktion | M1-04 bis M1-07 |
| E3 | JSON-Erzeugung & Schema | M1-08 bis M1-09 |
| E4 | Validierungs-Gates | M1-10 bis M1-11 |
| E5 | Datei-Routing & Audit | M1-12 bis M1-14 |

---

## E1 — Ordner & Konfiguration

---

### M1-01 · Ordnerstruktur automatisch anlegen

**Als** Datenkoordinator
**möchte ich**, dass die Anwendung beim ersten Start alle benötigten Ordner anlegt,
**damit** ich sofort mit dem Ablegen von PDFs beginnen kann ohne manuelle Vorbereitung.

**Akzeptanzkriterien:**
- [ ] Beim Start prüft die Anwendung, ob `/eingang`, `/archiv`, `/fehler`, `/ausgabe`, `/konfig`, `/reports` existieren
- [ ] Fehlende Ordner werden automatisch angelegt
- [ ] Bereits vorhandene Ordner bleiben unverändert (kein Überschreiben)
- [ ] Erfolgsmeldung im CLI: "Ordnerstruktur bereit ✓"

**Technische Notizen:**
```
data/
  eingang/     # Eingangs-PDFs
  archiv/      # Verarbeitete Originale (read-only by convention)
  fehler/      # Fehlerhafte PDFs + Fehlerlogs
  ausgabe/     # Extrahierte JSON-Dateien
  konfig/      # Konfig-Bibliothek (YAML pro Beruf)
  reports/     # Validierungs-Reports
```

**Priorität:** Must Have | **Aufwand:** XS

---

### M1-02 · Eingangsordner-Pfad konfigurieren

**Als** Datenkoordinator
**möchte ich** den Basispfad der Ordnerstruktur in einer Konfigurationsdatei festlegen können,
**damit** die Pipeline auf verschiedenen Rechnern ohne Code-Änderungen portabel bleibt.

**Akzeptanzkriterien:**
- [ ] Basispfad ist in `.env` oder `config.yaml` konfigurierbar (Standard: `./data`)
- [ ] CLI-Parameter `--data-dir /pfad/zum/ordner` überschreibt die Konfiguration
- [ ] Ungültiger Pfad → klare Fehlermeldung: "Verzeichnis nicht gefunden: /pfad"
- [ ] Relativer und absoluter Pfad werden beide akzeptiert

**Technische Notizen:**
```python
# config.py
DATA_DIR = os.getenv("DATA_DIR", "./data")
INPUT_DIR = Path(DATA_DIR) / "eingang"
ARCHIVE_DIR = Path(DATA_DIR) / "archiv"
ERROR_DIR = Path(DATA_DIR) / "fehler"
OUTPUT_DIR = Path(DATA_DIR) / "ausgabe"
```

**Priorität:** Must Have | **Aufwand:** XS

---

### M1-03 · Metadaten aus Unterordnerpfad ableiten

**Als** Datenkoordinator
**möchte ich**, dass Beruf und Jahr automatisch aus dem Ordnerpfad abgeleitet werden,
**damit** ich keine separaten Metadaten-Dateien pflegen muss.

**Akzeptanzkriterien:**
- [ ] Pfad `/eingang/2026/elektrotechnik/pruefung.pdf` → `beruf="elektrotechnik"`, `jahr=2026`
- [ ] Pfad ohne Jahres-Ebene `/eingang/elektrotechnik/pruefung.pdf` → `jahr=null`, Warnung im Log
- [ ] Berufname wird aus dem Ordnernamen normalisiert: Leerzeichen → Bindestrich, Kleinbuchstaben
- [ ] Ungültige Pfadstruktur → Datei in `/fehler/` mit Hinweis auf erwartete Struktur

**Technische Notizen:**
```python
# path_parser.py
def extract_metadata(pdf_path: Path, base_input_dir: Path) -> dict:
    rel = pdf_path.relative_to(base_input_dir)
    parts = rel.parts  # ["2026", "elektrotechnik", "pruefung.pdf"]
    return {
        "jahr": int(parts[0]) if parts[0].isdigit() else None,
        "beruf": parts[1].lower().replace(" ", "-") if len(parts) >= 3 else None,
        "dateiname": parts[-1]
    }
```

**Priorität:** Must Have | **Aufwand:** S

---

## E2 — PDF-Parsing & Extraktion

---

### M1-04 · Pipeline-Lauf per CLI starten

**Als** Datenkoordinator
**möchte ich** den Verarbeitungslauf per CLI-Befehl starten können,
**damit** ich den Verarbeitungszeitpunkt manuell kontrolliere und den Prozess als Batch ausführe.

**Akzeptanzkriterien:**
- [ ] `python run_pipeline.py` verarbeitet alle PDFs im konfigurierten Eingangsordner
- [ ] `python run_pipeline.py --input ./data/eingang/2026/elektrotechnik/pruefung.pdf` verarbeitet nur diese eine Datei
- [ ] `python run_pipeline.py --dry-run` simuliert den Lauf ohne Dateien zu verschieben oder zu schreiben
- [ ] Fortschrittsanzeige: pro PDF eine Zeile (Dateiname, Status, Dauer in ms)
- [ ] Exit-Code 0 bei vollständigem Erfolg, Exit-Code 1 wenn mindestens eine Datei fehlschlug

**Technische Notizen:**
```bash
python run_pipeline.py [--input PATH] [--data-dir PATH] [--dry-run] [--verbose]
```

**Priorität:** Must Have | **Aufwand:** S

---

### M1-05 · PDFs mit pdfplumber extrahieren

**Als** Datenkoordinator
**möchte ich**, dass Tabellendaten aus PDFs deterministisch mit pdfplumber extrahiert werden,
**damit** die Rohextraktion reproduzierbar ist und keine KI-Nondeterminismus in den Basislauf einbringt.

**Akzeptanzkriterien:**
- [ ] Gleiches PDF + gleiche pdfplumber-Version → identische Rohextraktion
- [ ] Pro Seite werden alle gefundenen Tabellen als separate Objekte extrahiert
- [ ] Nicht-Tabellen-Inhalt (Fließtext, Kopfzeilen) wird separat als `raw_text` gespeichert
- [ ] PDFs ohne erkannte Tabellen → Fehler mit Typ "NO_TABLES_FOUND"
- [ ] Passwortgeschützte oder beschädigte PDFs → Fehler mit Typ "PDF_UNREADABLE"

**Technische Notizen:**
```python
import pdfplumber

def extract_tables(pdf_path: Path) -> list[dict]:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            raw_text = page.extract_text()
            results.append({
                "seite": page_num,
                "tabellen": tables,      # list of list[list[str]]
                "raw_text": raw_text,
                "bbox_info": [t.bbox for t in page.find_tables()]
            })
    return results
```

**Priorität:** Must Have | **Aufwand:** S

---

### M1-06 · Mehrtabellen-Erkennung via Bounding-Box

**Als** Datenkoordinator
**möchte ich**, dass auf Seiten mit mehreren Tabellen jede Tabelle korrekt als eigenständiges Objekt erkannt wird,
**damit** 1-Tabellen- und 2-Tabellen-Seiten unterschiedlich verarbeitet werden können.

**Akzeptanzkriterien:**
- [ ] Seite mit 1 Tabelle → 1 Extraktionsobjekt
- [ ] Seite mit 2 Tabellen → 2 Extraktionsobjekte mit je eigenem Bounding-Box (Y-Koordinate)
- [ ] Tabellen werden nach ihrer vertikalen Position sortiert (obere Tabelle zuerst)
- [ ] Minimale Tabellengröße: mindestens 2 Zeilen und 2 Spalten (sonst ignoriert)
- [ ] Testfall: Seite mit Tabelle 1 (Y: 100–400) + Tabelle 2 (Y: 450–700) → korrekt getrennt

**Technische Notizen:**
```python
def detect_tables_with_bbox(page) -> list[dict]:
    table_objects = page.find_tables()
    return sorted(
        [{"bbox": t.bbox, "data": t.extract()} for t in table_objects
         if len(t.extract()) >= 2 and len(t.extract()[0]) >= 2],
        key=lambda x: x["bbox"][1]  # sortiert nach Y-Top
    )
```

**Priorität:** Must Have | **Aufwand:** M

---

### M1-07 · Camelot als Fallback bei pdfplumber-Fehlschlag

**Als** Datenkoordinator
**möchte ich**, dass bei schlechter pdfplumber-Extraktion automatisch Camelot als Fallback versucht wird,
**damit** möglichst viele PDFs ohne manuelle Eingriffe verarbeitet werden.

**Akzeptanzkriterien:**
- [ ] pdfplumber scheitert (0 Tabellen gefunden) → automatisch Camelot-Versuch
- [ ] Camelot-Versuch ist im Log als "FALLBACK_CAMELOT" markiert
- [ ] Camelot scheitert ebenfalls → Fehler mit Typ "PARSING_FAILED", PDF → /fehler/
- [ ] Camelot-Abhängigkeit (inkl. Ghostscript) ist im README dokumentiert und optional

**Priorität:** Should Have | **Aufwand:** M

---

## E3 — JSON-Erzeugung & Schema

---

### M1-08 · Rohextraktion in einheitliches JSON-Schema überführen

**Als** Datenkoordinator
**möchte ich**, dass die extrahierten Tabellendaten in das definierte JSON-Schema transformiert werden,
**damit** alle Berufe ein konsistentes, weiterverarbeitbares Format haben.

**Akzeptanzkriterien:**
- [ ] Output-JSON enthält immer: `berufNr` (Array), `beschreibung`, `prüfungsTyp`, `prüfungsbereiche`
- [ ] Nicht vorhandene optionale Felder werden als `null` gespeichert, nicht weggelassen
- [ ] `berufNr` ist immer ein Array, auch bei einer einzelnen Nummer
- [ ] `prüfungsbereiche` enthält min. 1 schriftlichen und min. 1 praktischen Bereich (sonst V1-Fehler)
- [ ] Ausgabedatei: `/ausgabe/{beruf}.json`

**Ziel-Schema (Referenz):**
```json
{
  "berufNr": ["4010", "4011", "4012"],
  "beschreibung": "Anlagenmechaniker/-in",
  "prüfungsTyp": "abschlusspruefung-teil2",
  "prüfungsbereiche": [
    {
      "name": "Arbeitsauftrag",
      "typ": "praktisch",
      "varianten": [
        {
          "bezeichnung": "Praktische Aufgabe",
          "aufgaben": [
            { "bezeichnung": "Planung", "zeitMinuten": 30, "punkte": null }
          ],
          "gewichtung": {
            "imPrüfungsbereich": 50,
            "schriftlichePrüfung": null,
            "teil2": 50,
            "gesamtergebnis": null
          }
        }
      ]
    },
    {
      "name": "Schriftliche Prüfung",
      "typ": "schriftlich",
      "varianten": null,
      "aufgaben": [
        { "bezeichnung": "Aufgabe 1", "zeitMinuten": 90, "punkte": 100 }
      ],
      "gewichtung": {
        "imPrüfungsbereich": null,
        "schriftlichePrüfung": 40,
        "teil2": 25,
        "gesamtergebnis": null
      }
    }
  ],
  "metadaten": {
    "beruf": "anlagenmechaniker",
    "jahr": 2026,
    "quelldatei": "pruefung.pdf",
    "verarbeitetAm": "2026-02-24T14:30:00Z",
    "konfigVersion": "1.0"
  }
}
```

**Priorität:** Must Have | **Aufwand:** L

---

### M1-09 · Konfig-basiertes Mapping (Hardcoded für MVP)

**Als** Datenkoordinator
**möchte ich** für den MVP eine hardcodierte Mapping-Konfig für bekannte Test-PDFs verwenden,
**damit** die Pipeline ohne KI-Schritt testbar und demonstrierbar ist.

**Akzeptanzkriterien:**
- [ ] Konfig-Datei `konfig/anlagenmechaniker.yaml` steuert das Spalten-Mapping
- [ ] Pipeline liest Konfig beim Start für bekannte Berufe
- [ ] Unbekannter Beruf ohne Konfig → Status "KONFIG_FEHLT", Beruf übersprungen (kein Absturz)
- [ ] Konfig-Format ist dokumentiert (Kommentare in der YAML)

**Konfig-Referenzformat:**
```yaml
# konfig/anlagenmechaniker.yaml
version: "1.0"
beruf: "anlagenmechaniker"
prüfungsTyp: "abschlusspruefung-teil2"
tabellenMapping:
  - seite: 1
    tabelleIndex: 0          # Erste Tabelle auf der Seite
    layout: "schriftlich"
    spalten:
      bezeichnung: 0         # Spaltenindex
      zeitMinuten: 1
      gewichtungImBereich: 2
      gewichtungTeil2: 3
  - seite: 1
    tabelleIndex: 1
    layout: "praktisch"
    transponiert: false
    spalten:
      bezeichnung: 0
      variante: 1
      zeitMinuten: 2
```

**Priorität:** Must Have | **Aufwand:** M

---

## E4 — Validierungs-Gates

---

### M1-10 · V1 — JSON-Schema-Gate (Pflicht)

**Als** Datenkoordinator
**möchte ich**, dass jedes erzeugte JSON vor dem Speichern gegen das Pflicht-Schema validiert wird,
**damit** strukturell ungültige Daten niemals im `/ausgabe/`-Ordner landen.

**Akzeptanzkriterien:**
- [ ] Pflichtfelder vorhanden: `berufNr` (nicht-leeres Array), `beschreibung`, `prüfungsTyp`, `prüfungsbereiche` (min. 1 Eintrag)
- [ ] Min. 1 `prüfungsbereich` mit `typ: "schriftlich"` und min. 1 mit `typ: "praktisch"`
- [ ] Alle Felder haben korrekte Datentypen (Array ist Array, String ist String, Zahl ist Zahl)
- [ ] V1-Fehler → kein JSON in `/ausgabe/`, PDF → `/fehler/`, Fehlertyp: `V1_SCHEMA_FEHLER`
- [ ] V1-Fehler-Meldung benennt das konkrete fehlende/falsche Feld

**Technische Notizen:**
```python
# validation.py
from jsonschema import validate, ValidationError

PFLICHT_SCHEMA = {
    "type": "object",
    "required": ["berufNr", "beschreibung", "prüfungsTyp", "prüfungsbereiche"],
    "properties": {
        "berufNr": {"type": "array", "minItems": 1},
        "beschreibung": {"type": "string", "minLength": 1},
        "prüfungsTyp": {"type": "string"},
        "prüfungsbereiche": {"type": "array", "minItems": 1}
    }
}

def validate_schema(data: dict) -> tuple[bool, str | None]:
    try:
        validate(instance=data, schema=PFLICHT_SCHEMA)
        # Prüfe min. 1 schriftlich + 1 praktisch
        typen = [b["typ"] for b in data.get("prüfungsbereiche", [])]
        if "schriftlich" not in typen:
            return False, "Kein schriftlicher Prüfungsbereich gefunden"
        if "praktisch" not in typen:
            return False, "Kein praktischer Prüfungsbereich gefunden"
        return True, None
    except ValidationError as e:
        return False, e.message
```

**Priorität:** Must Have | **Aufwand:** S

---

### M1-11 · V2 — Numerische Konsistenz-Check (Pflicht)

**Als** Datenkoordinator
**möchte ich**, dass Gewichtungssummen und Zeitangaben automatisch auf Plausibilität geprüft werden,
**damit** mathematische Extraktionsfehler deterministisch abgefangen werden — unabhängig davon, wie überzeugend der Text klingt.

**Akzeptanzkriterien:**
- [ ] Alle Gewichtungen pro Gewichtungsebene summieren auf 100% (Toleranz: ±1% für Rundungsfehler)
- [ ] Keine Zeitangabe < 1 Minute oder > 1440 Minuten (24h)
- [ ] Alle `berufNr`-Einträge sind numerisch und positiv
- [ ] Gewichtung muss zwischen 0 und 100 liegen (kein Wert > 100 erlaubt)
- [ ] V2-Fehler → kein JSON in `/ausgabe/`, PDF → `/fehler/`, Fehlertyp: `V2_KONSISTENZ_FEHLER`
- [ ] V2-Fehler-Meldung nennt konkrete Prüfregel und tatsächlichen Wert: "Gewichtung schriftlichePrüfung: 40+25+40=105% (>101%)"

**Technische Notizen:**
```python
def validate_consistency(data: dict) -> tuple[bool, str | None]:
    TOLERANZ = 1.0  # ±1%

    for bereich in data.get("prüfungsbereiche", []):
        for ebene in ["imPrüfungsbereich", "schriftlichePrüfung", "teil2", "gesamtergebnis"]:
            gewichtungen = [
                b.get("gewichtung", {}).get(ebene)
                for b in data["prüfungsbereiche"]
                if b.get("gewichtung", {}).get(ebene) is not None
            ]
            if gewichtungen:
                summe = sum(gewichtungen)
                if not (100 - TOLERANZ <= summe <= 100 + TOLERANZ):
                    return False, f"Gewichtungsebene '{ebene}': Summe={summe}% (erwartet: 100±{TOLERANZ}%)"

        # Zeitangaben prüfen
        for aufgabe in bereich.get("aufgaben", []):
            zeit = aufgabe.get("zeitMinuten")
            if zeit is not None and not (1 <= zeit <= 1440):
                return False, f"Zeitangabe '{aufgabe.get('bezeichnung')}': {zeit} Minuten (erwartet: 1–1440)"

    return True, None
```

**Priorität:** Must Have | **Aufwand:** M

---

## E5 — Datei-Routing & Audit

---

### M1-12 · Erfolgreich verarbeitete PDFs archivieren

**Als** Datenkoordinator
**möchte ich**, dass erfolgreich verarbeitete PDFs in den `/archiv/`-Ordner verschoben werden,
**damit** der Eingangsordner sauber bleibt und die Originaldaten unveränderlich erhalten bleiben.

**Akzeptanzkriterien:**
- [ ] Nach erfolgreichem V1+V2-Gate: PDF wird von `/eingang/` nach `/archiv/` verschoben (nicht kopiert)
- [ ] Zielstruktur im Archiv spiegelt Quellstruktur: `/archiv/2026/elektrotechnik/pruefung.pdf`
- [ ] Bereits vorhandene Datei im Archiv → nicht überschreiben, Suffix `_1`, `_2` etc. anhängen
- [ ] Im `--dry-run`-Modus: kein Verschieben, nur Logging "würde archiviert: ..."

**Priorität:** Must Have | **Aufwand:** S

---

### M1-13 · Fehlerhafte PDFs mit Fehlerlog in /fehler/ ablegen

**Als** Datenkoordinator
**möchte ich**, dass fehlerhafte PDFs mit einem begleitenden Fehlerlog in `/fehler/` landen,
**damit** ich den Fehlergrund ohne Debugging nachvollziehen kann und keine Datei verloren geht.

**Akzeptanzkriterien:**
- [ ] Bei Fehler (jeder Art): Original-PDF → `/fehler/2026/elektrotechnik/pruefung.pdf`
- [ ] Begleitdatei: `/fehler/2026/elektrotechnik/pruefung.fehler.json`
- [ ] Fehler-JSON enthält: `datei`, `zeitstempel`, `fehlerTyp` (V1_SCHEMA_FEHLER / V2_KONSISTENZ_FEHLER / PARSING_FAILED / NO_TABLES_FOUND / KONFIG_FEHLT), `meldung`, `details`
- [ ] Pipeline läuft nach einem Fehler weiter (kein Absturz für andere PDFs)

**Fehler-JSON Beispiel:**
```json
{
  "datei": "pruefung.pdf",
  "beruf": "elektrotechnik",
  "jahr": 2026,
  "zeitstempel": "2026-02-24T15:00:00Z",
  "fehlerTyp": "V2_KONSISTENZ_FEHLER",
  "meldung": "Gewichtungsebene 'schriftlichePrüfung': Summe=105% (erwartet: 100±1%)",
  "details": {
    "ebene": "schriftlichePrüfung",
    "werte": [40, 25, 40],
    "summe": 105
  }
}
```

**Priorität:** Must Have | **Aufwand:** S

---

### M1-14 · CLI-Zusammenfassung nach Pipeline-Lauf

**Als** Datenkoordinator
**möchte ich** nach dem Lauf eine kompakte Zusammenfassung im Terminal sehen,
**damit** ich auf einen Blick weiß, was erfolgreich war und was Aufmerksamkeit braucht.

**Akzeptanzkriterien:**
- [ ] Pro PDF: eine Zeile mit Status-Emoji, Dateiname, Fehlertyp (falls vorhanden), Dauer
- [ ] Abschluss-Zusammenfassung: Gesamt / Erfolgreich / Fehlerhaft / Übersprungen
- [ ] Exit-Code 0 wenn alle erfolgreich, Exit-Code 1 wenn min. 1 fehlerhaft

**Beispiel-Output:**
```
BPÜ Pipeline — Lauf 2026-02-24 15:00:00
─────────────────────────────────────────────────────
✓  anlagenmechaniker/pruefung.pdf          → ausgabe/anlagenmechaniker.json       (1.2s)
✓  industriemechaniker/pruefung.pdf        → ausgabe/industriemechaniker.json     (0.9s)
✗  elektrotechnik/pruefung.pdf             → fehler/ [V2_KONSISTENZ_FEHLER]       (0.7s)
⚠  kaufmann-bueromanagement/pruefung.pdf   → fehler/ [KONFIG_FEHLT]               (0.1s)
─────────────────────────────────────────────────────
Gesamt: 4 | Erfolgreich: 2 | Fehlerhaft: 1 | Übersprungen: 1
```

**Priorität:** Must Have | **Aufwand:** XS

---

## Story-Übersicht M1

| ID | Titel | Epic | Priorität | Aufwand | PRD-Ref |
|----|-------|------|-----------|---------|---------|
| M1-01 | Ordnerstruktur automatisch anlegen | E1 | Must Have | XS | F-01 |
| M1-02 | Eingangsordner-Pfad konfigurieren | E1 | Must Have | XS | F-01 |
| M1-03 | Metadaten aus Unterordnerpfad ableiten | E1 | Must Have | S | F-03 |
| M1-04 | Pipeline-Lauf per CLI starten | E2 | Must Have | S | F-02 |
| M1-05 | PDFs mit pdfplumber extrahieren | E2 | Must Have | S | F-06 |
| M1-06 | Mehrtabellen-Erkennung via Bounding-Box | E2 | Must Have | M | F-07 |
| M1-07 | Camelot als Fallback | E2 | Should Have | M | F-06 |
| M1-08 | Rohextraktion in JSON-Schema überführen | E3 | Must Have | L | F-20–F-25 |
| M1-09 | Konfig-basiertes Mapping (Hardcoded MVP) | E3 | Must Have | M | F-10, F-12 |
| M1-10 | V1 — JSON-Schema-Gate | E4 | Must Have | S | F-26 |
| M1-11 | V2 — Numerische Konsistenz-Check | E4 | Must Have | M | F-27 |
| M1-12 | Erfolgreich verarbeitete PDFs archivieren | E5 | Must Have | S | F-04 |
| M1-13 | Fehlerhafte PDFs mit Fehlerlog ablegen | E5 | Must Have | S | F-05 |
| M1-14 | CLI-Zusammenfassung nach Pipeline-Lauf | E5 | Must Have | XS | F-02 |

**Gesamtaufwand M1:** 13 Must Have + 1 Should Have Stories

---

## Empfohlene Implementierungsreihenfolge

```
Phase 1 — Fundament (E1 + E5-Grundstruktur)
  M1-01 → M1-02 → M1-03

Phase 2 — Parsing-Kern (E2)
  M1-04 → M1-05 → M1-06 → [M1-07 optional]

Phase 3 — Schema & Mapping (E3)
  M1-09 → M1-08   ← Konfig-Format zuerst definieren, dann Mapping implementieren

Phase 4 — Validierung (E4)
  M1-10 → M1-11   ← Gates blockieren, daher früh testen

Phase 5 — Routing & Ausgabe (E5)
  M1-12 → M1-13 → M1-14
```

---

## Test-Szenarien M1 (Smoke Tests)

| Szenario | Erwartetes Ergebnis |
|----------|---------------------|
| PDF mit bekannter Konfig, korrekte Daten | JSON in `/ausgabe/`, PDF in `/archiv/` |
| PDF mit bekannter Konfig, Gewichtung 105% | V2-Fehler, PDF in `/fehler/` mit Fehler-JSON |
| PDF mit bekannter Konfig, Pflichtfeld fehlt | V1-Fehler, PDF in `/fehler/` mit Fehler-JSON |
| PDF ohne passende Konfig | KONFIG_FEHLT-Warnung, PDF in `/fehler/` |
| PDF mit 2 Tabellen pro Seite | Beide Tabellen korrekt getrennt extrahiert |
| `--dry-run` | Kein Schreiben, nur Logging |
| Beschädigte PDF-Datei | PDF_UNREADABLE-Fehler, kein Absturz der Pipeline |
