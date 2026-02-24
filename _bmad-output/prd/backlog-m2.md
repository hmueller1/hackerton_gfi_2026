# Backlog M2 — KI-Konfig-Generierung

**Meilenstein:** M2 — KI-gestützte Konfig-Generierung mit Konfidenz-Scoring
**Release:** Vollständig
**Datum:** 2026-02-24
**Voraussetzung:** M1 abgeschlossen (Basis-Pipeline lauffähig)
**Ziel:** Unbekannte Layout-Typen werden automatisch via Claude API analysiert und als YAML-Konfig gespeichert. Konfidenz-Score steuert das Routing zur manuellen Review.

---

## Definition of Done (M2)

- [ ] Bekannte Berufe (Konfig vorhanden) laufen ohne LLM-Aufruf durch
- [ ] Unbekannte Berufe triggern automatisch den KI-Konfigurationsschritt
- [ ] Claude API generiert eine syntaktisch valide YAML-Konfig
- [ ] Jede generierte Konfig enthält Konfidenz-Score (0–100) + Begründung
- [ ] Berufe mit Score < 85% werden als `ZUR_REVIEW` markiert und nicht automatisch gespeichert
- [ ] Generierte Konfigs werden in der Konfig-Bibliothek (`/konfig/`) versioniert gespeichert
- [ ] Claude API nicht verfügbar → sauberer Fallback ohne Pipeline-Absturz

---

## Epics

| Epic | Beschreibung | Stories |
|------|-------------|---------|
| E6 | Layout-Typ-Erkennung & Routing | M2-01 bis M2-02 |
| E7 | Claude API Integration | M2-03 bis M2-04 |
| E8 | KI-Konfig-Generierung | M2-05 bis M2-07 |
| E9 | Konfidenz-Scoring & Review-Routing | M2-08 bis M2-09 |
| E10 | Konfig-Bibliothek & Versionierung | M2-10 bis M2-12 |

---

## E6 — Layout-Typ-Erkennung & Routing

---

### M2-01 · Konfig-Lookup: bekannte Berufe ohne LLM verarbeiten

**Als** Datenkoordinator
**möchte ich**, dass die Pipeline für Berufe mit vorhandener Konfig-Datei direkt die gespeicherte Konfig lädt,
**damit** der Jahres-Lauf für bekannte Berufe schnell, deterministisch und kostenfrei bleibt.

**Akzeptanzkriterien:**
- [ ] Lookup-Logik prüft `/konfig/{beruf}.yaml` bevor ein LLM-Aufruf initiiert wird
- [ ] Konfig gefunden → direkte Verarbeitung, kein API-Call, Log-Eintrag: "Konfig geladen: konfig/elektrotechnik.yaml (v1.2)"
- [ ] Konfig nicht gefunden → Routing zu E8 (KI-Konfig-Generierung)
- [ ] Konfig vorhanden aber ungültige YAML-Syntax → Fehlertyp `KONFIG_SYNTAX_FEHLER`, Beruf → `/fehler/`
- [ ] Konfig-Version wird in `metadaten.konfigVersion` des Output-JSONs gespeichert

**Technische Notizen:**
```python
# config_manager.py
def lookup_config(beruf: str, konfig_dir: Path) -> dict | None:
    konfig_path = konfig_dir / f"{beruf}.yaml"
    if not konfig_path.exists():
        return None
    with open(konfig_path) as f:
        return yaml.safe_load(f)  # Wirft yaml.YAMLError bei Syntaxfehler
```

**Priorität:** Must Have | **Aufwand:** XS

---

### M2-02 · Unbekannte Layouts erkennen und KI-Schritt triggern

**Als** Datenkoordinator
**möchte ich**, dass die Pipeline bei fehlendem Konfig-Eintrag automatisch den KI-Konfigurationsschritt startet,
**damit** neue Berufe ohne manuelle Intervention verarbeitet werden können.

**Akzeptanzkriterien:**
- [ ] Kein Konfig-Treffer → Status `KONFIG_UNBEKANNT`, Routing zu KI-Schritt
- [ ] CLI-Ausgabe zeigt den Schritt: "⚙ Neuer Beruf erkannt — starte KI-Konfig-Generierung..."
- [ ] KI-Schritt-Ergebnis (Konfig + Score) wird als Zwischenergebnis persistiert (auch bei Abbruch abrufbar)
- [ ] Im `--no-ai`-Modus: Routing zu `/fehler/` mit Typ `KONFIG_FEHLT` statt KI-Aufruf (für Offline-Tests)

**Priorität:** Must Have | **Aufwand:** XS

---

## E7 — Claude API Integration

---

### M2-03 · Claude API Anbindung & Konfiguration

**Als** Entwickler
**möchte ich** eine saubere, konfigurierbare Abstraktion zur Claude API,
**damit** API-Key, Modell und Timeouts zentral gesteuert werden und ein Wechsel des Modells keine Code-Änderungen erfordert.

**Akzeptanzkriterien:**
- [ ] `ANTHROPIC_API_KEY` wird aus `.env` geladen — nie hardcodiert
- [ ] Modell konfigurierbar in `config.yaml` (Standard: `claude-sonnet-4-6`)
- [ ] Timeout konfigurierbar (Standard: 60 Sekunden)
- [ ] API-Key fehlt → klare Fehlermeldung beim Start: "ANTHROPIC_API_KEY nicht gesetzt. KI-Konfig-Schritt deaktiviert."
- [ ] API-Fehler (HTTP 429, 500, Timeout) → Retry mit Exponential Backoff (max. 3 Versuche), danach Fallback
- [ ] Alle API-Aufrufe werden mit Dauer und Token-Verbrauch geloggt (INFO-Level)

**Technische Notizen:**
```python
# ai_client.py
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_claude(system_prompt: str, user_prompt: str, model: str = "claude-sonnet-4-6") -> str:
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text
```

**Priorität:** Must Have | **Aufwand:** S

---

### M2-04 · Fallback bei Claude API Nicht-Verfügbarkeit

**Als** Datenkoordinator
**möchte ich**, dass die Pipeline bei API-Ausfällen nicht abstürzt,
**damit** der Rest des Batch-Laufs für bekannte Berufe unbeeinträchtigt weiterläuft.

**Akzeptanzkriterien:**
- [ ] Nach 3 fehlgeschlagenen Versuchen: Beruf → `/fehler/` mit Typ `KI_NICHT_VERFUEGBAR`
- [ ] Alle anderen Berufe im Batch werden weiter verarbeitet
- [ ] Fehler-JSON enthält HTTP-Status und letzte Fehlermeldung der API
- [ ] CLI-Ausgabe: "⚠ Claude API nicht erreichbar für {beruf} — Beruf übersprungen"

**Priorität:** Must Have | **Aufwand:** XS

---

## E8 — KI-Konfig-Generierung

---

### M2-05 · System-Prompt & Konfig-Generierungs-Prompt

**Als** Entwickler
**möchte ich** einen präzisen, getesteten Prompt für die Konfig-Generierung,
**damit** Claude konsistent valide YAML-Konfigs im definierten Format erzeugt.

**Akzeptanzkriterien:**
- [ ] System-Prompt definiert die Rolle und das Ausgabeformat (YAML-Schema)
- [ ] User-Prompt enthält: Roh-Tabelleninhalt (als Text), erkannte Seitenstruktur, JSON-Ziel-Schema-Referenz
- [ ] Claude antwortet mit genau einem YAML-Block (kein Freitext davor/danach, oder zuverlässig parsebar)
- [ ] Prompt enthält Beispiel-Input/Output (One-Shot) für den Anlagenmechaniker-Layout-Typ
- [ ] Prompt-Dateien liegen unter `/prompts/` und sind ohne Code-Änderung editierbar

**System-Prompt (Referenz):**
```
Du bist ein Experte für Datenextraktions-Pipelines und Berufsprüfungs-Dokumente.
Deine Aufgabe: Analysiere Tabellendaten aus einem PDF und generiere eine YAML-Konfig,
die das Spalten-Mapping für eine automatische Extraktion beschreibt.

Ausgabeformat: Genau ein YAML-Block, kein weiterer Text außerhalb des Blocks.
Halte dich strikt an das vorgegebene Konfig-Schema.
```

**User-Prompt-Template (Referenz):**
```
## Tabellendaten aus dem PDF

Beruf: {beruf}
Seiten: {seitenanzahl}

{tabellen_rohinhalt}

## Ziel-JSON-Schema

{json_schema_referenz}

## Konfig-Schema (YAML)

{konfig_schema_mit_kommentaren}

## Beispiel-Konfig (Anlagenmechaniker / Layout-Typ A)

{beispiel_konfig}

## Aufgabe

Generiere die YAML-Konfig für den Beruf "{beruf}".
Füge am Ende einen Konfidenz-Score (0–100) und eine Begründung hinzu.
Format:
  konfidenz:
    score: 87
    begruendung: "Spalte 3 ist eindeutig Gewichtung. Unsicher bei Transponierung Seite 2."
    unsichereFelder: ["tabellenMapping[1].transponiert"]
```

**Priorität:** Must Have | **Aufwand:** L

---

### M2-06 · Claude-Antwort parsen und YAML extrahieren

**Als** Entwickler
**möchte ich** die Claude-Antwort robust parsen und die generierte YAML-Konfig extrahieren,
**damit** Freitext-Anteile in der Antwort die Verarbeitung nicht brechen.

**Akzeptanzkriterien:**
- [ ] YAML-Block wird aus Markdown-Codeblock (` ```yaml ... ``` `) extrahiert, falls vorhanden
- [ ] Fallback: gesamte Antwort wird als YAML geparst, wenn kein Codeblock vorhanden
- [ ] Nicht-parsebares YAML → Fehlertyp `KI_ANTWORT_UNGUELTIG`, Beruf → `/fehler/`
- [ ] Geparste Konfig wird auf Pflichtfelder geprüft: `version`, `beruf`, `prüfungsTyp`, `tabellenMapping`
- [ ] Fehlende Pflichtfelder → Fehlertyp `KI_KONFIG_UNVOLLSTAENDIG`

**Technische Notizen:**
```python
import re, yaml

def extract_yaml_from_response(response: str) -> dict:
    # Versuche Markdown-Codeblock zu extrahieren
    match = re.search(r"```(?:yaml)?\n(.*?)```", response, re.DOTALL)
    raw_yaml = match.group(1) if match else response.strip()
    return yaml.safe_load(raw_yaml)  # Wirft yaml.YAMLError bei Syntaxfehler

PFLICHT_FELDER_KONFIG = {"version", "beruf", "prüfungsTyp", "tabellenMapping", "konfidenz"}

def validate_generated_config(config: dict) -> tuple[bool, str | None]:
    fehlend = PFLICHT_FELDER_KONFIG - set(config.keys())
    if fehlend:
        return False, f"Pflichtfelder fehlen: {', '.join(fehlend)}"
    if not isinstance(config.get("tabellenMapping"), list) or len(config["tabellenMapping"]) == 0:
        return False, "tabellenMapping muss eine nicht-leere Liste sein"
    return True, None
```

**Priorität:** Must Have | **Aufwand:** M

---

### M2-07 · Generierte Konfig gegen echte PDF-Daten testen (Dry-Run)

**Als** Datenkoordinator
**möchte ich**, dass die generierte Konfig sofort gegen die echten Tabellendaten des PDFs angewendet wird,
**damit** Fehler in der Konfig bereits vor der Speicherung sichtbar werden.

**Akzeptanzkriterien:**
- [ ] Nach erfolgreicher Konfig-Generierung: Konfig wird direkt für einen internen Extraktions-Test genutzt
- [ ] Extraktion liefert kein valides JSON (V1/V2-Fehler) → Konfig wird als `DRAFT` markiert, nicht automatisch gespeichert
- [ ] Dry-Run-Ergebnis (JSON + Fehler falls vorhanden) wird als `{beruf}.draft.json` in `/konfig/` gespeichert
- [ ] CLI-Ausgabe: "⚙ Dry-Run: Konfig angewendet → [✓ V1 bestanden | ✗ V2 fehlgeschlagen: ...]"

**Priorität:** Must Have | **Aufwand:** M

---

## E9 — Konfidenz-Scoring & Review-Routing

---

### M2-08 · Konfidenz-Score auslesen und interpretieren

**Als** Datenkoordinator
**möchte ich** den Konfidenz-Score und die Begründung aus der KI-Antwort lesen können,
**damit** ich gezielt weiß, welche Felder einer Konfig besondere Prüfaufmerksamkeit benötigen.

**Akzeptanzkriterien:**
- [ ] Score wird aus `konfidenz.score` der generierten YAML gelesen (Integer 0–100)
- [ ] Begründung und unsichere Felder werden in den Prozess-Status übernommen
- [ ] Kein Score in der Antwort → Score wird als `0` gewertet (worst case), Warnung im Log
- [ ] Score wird in `/reports/ki-konfig-{beruf}-{datum}.json` persistiert:
  ```json
  {
    "beruf": "elektrotechnik",
    "zeitstempel": "2026-02-24T15:00:00Z",
    "score": 87,
    "begruendung": "Spalte 3 ist eindeutig Gewichtung.",
    "unsichereFelder": ["tabellenMapping[1].transponiert"],
    "dryRunErgebnis": "V1_OK_V2_OK",
    "routing": "AUTO_GESPEICHERT"
  }
  ```
- [ ] CLI-Ausgabe: "Konfidenz: 87/100 — 'Spalte 3 eindeutig Gewichtung. Unsicher: tabellenMapping[1].transponiert'"

**Priorität:** Must Have | **Aufwand:** S

---

### M2-09 · Schwellwert-Routing: hoch vs. niedrig Konfidenz

**Als** Datenkoordinator
**möchte ich**, dass Konfigs mit hohem Konfidenz-Score automatisch gespeichert werden und Konfigs mit niedrigem Score zur manuellen Prüfung markiert werden,
**damit** kein unsicherer Konfig-Vorschlag unbemerkt produktiv geht.

**Akzeptanzkriterien:**
- [ ] Schwellwert konfigurierbar in `config.yaml` (Standard: `konfidenz_schwellwert: 85`)
- [ ] Score ≥ Schwellwert UND Dry-Run OK → Konfig wird automatisch in `/konfig/{beruf}.yaml` gespeichert, Beruf vollständig verarbeitet
- [ ] Score < Schwellwert ODER Dry-Run fehlgeschlagen → Konfig als `{beruf}.review.yaml` in `/konfig/pending/` gespeichert, Status `ZUR_REVIEW`
- [ ] `ZUR_REVIEW`-Berufe erscheinen in der CLI-Zusammenfassung als eigene Kategorie (nicht als Fehler)
- [ ] Beruf bleibt in `/eingang/` solange er `ZUR_REVIEW` ist (kein vorzeitiges Archivieren)

**CLI-Ausgabe (Beispiel):**
```
⚠  kaufmann-bueromanagement/pruefung.pdf  → konfig/pending/ [ZUR_REVIEW | Score: 72/100]  (3.1s)
   Begründung: "Spalte 4 unklar — Gewichtung oder Punktzahl? Bitte manuell prüfen."
```

**Technische Notizen:**
```python
SCHWELLWERT = int(os.getenv("KONFIDENZ_SCHWELLWERT", 85))

def route_by_confidence(beruf: str, score: int, dry_run_ok: bool, konfig: dict) -> str:
    if score >= SCHWELLWERT and dry_run_ok:
        save_config(beruf, konfig, pfad=KONFIG_DIR / f"{beruf}.yaml")
        return "AUTO_GESPEICHERT"
    else:
        save_config(beruf, konfig, pfad=KONFIG_DIR / "pending" / f"{beruf}.review.yaml")
        save_review_status(beruf, score=score, grund="score_unter_schwellwert" if score < SCHWELLWERT else "dry_run_fehler")
        return "ZUR_REVIEW"
```

**Priorität:** Must Have | **Aufwand:** M

---

## E10 — Konfig-Bibliothek & Versionierung

---

### M2-10 · Konfig-Datei speichern und versionieren

**Als** Datenkoordinator
**möchte ich**, dass jede gespeicherte Konfig automatisch versioniert wird,
**damit** ich nachvollziehen kann, welche Konfig-Version für welchen Jahres-Lauf verwendet wurde.

**Akzeptanzkriterien:**
- [ ] Versionsnummer wird beim Speichern automatisch erhöht (`1.0` → `1.1` → `2.0`)
- [ ] Minor-Bump bei KI-generierter Aktualisierung; Major-Bump bei manueller Bearbeitung (via Flag)
- [ ] Alte Konfig-Versionen werden in `/konfig/archiv/{beruf}/v{version}-{datum}.yaml` gespeichert
- [ ] Metadaten in der YAML: `version`, `erstelltAm`, `erstelltDurch` (`ki` oder `manuell`), `konfigScore`
- [ ] Konfig-Datei enthält Header-Kommentar mit Versionshistorie (letzte 3 Einträge)

**Konfig-Header (Referenz):**
```yaml
# Konfig: elektrotechnik
# Version: 1.2 | Erstellt: 2026-02-24 | Durch: ki | Score: 91
# Historie:
#   1.0 (2026-02-24, ki, Score: 87) — Erstgenerierung
#   1.1 (2026-02-24, manuell) — Spalte 3 korrigiert
#   1.2 (2026-02-24, ki, Score: 91) — Aktualisierung nach neuem PDF

version: "1.2"
beruf: "elektrotechnik"
erstelltAm: "2026-02-24"
erstelltDurch: "ki"
konfigScore: 91
prüfungsTyp: "abschlusspruefung-teil2"
tabellenMapping:
  ...
```

**Priorität:** Should Have | **Aufwand:** M

---

### M2-11 · Konfig-Bibliothek per CLI auflisten

**Als** Datenkoordinator
**möchte ich** alle bekannten Konfigs per CLI auflisten können,
**damit** ich ohne Dateisystem-Navigation einen Überblick über den Stand der Konfig-Bibliothek habe.

**Akzeptanzkriterien:**
- [ ] `python run_pipeline.py --list-configs` zeigt alle gespeicherten Konfigs
- [ ] Ausgabe enthält: Beruf, Version, Erstelldatum, Score, Ersteller (ki/manuell)
- [ ] Konfigs im `/pending/`-Ordner werden separat als `ZUR_REVIEW` gelistet
- [ ] `--list-configs --pending` zeigt nur Review-ausstehende Konfigs

**CLI-Ausgabe (Beispiel):**
```
Konfig-Bibliothek (7 Einträge)
──────────────────────────────────────────────────────────
Beruf                      Version  Score  Erstellt     Durch
anlagenmechaniker          1.0      —      2026-02-24   manuell
elektrotechnik             1.2      91     2026-02-24   ki
industriemechaniker        1.0      —      2026-02-24   manuell

ZUR REVIEW (2 ausstehend)
──────────────────────────────────────────────────────────
kaufmann-bueromanagement   0.1d     72     2026-02-24   ki  ← Score unter Schwellwert
fachinformatiker           0.1d     61     2026-02-24   ki  ← Dry-Run V2-Fehler
```

**Priorität:** Should Have | **Aufwand:** S

---

### M2-12 · Review-Konfig manuell bestätigen per CLI

**Als** Datenkoordinator
**möchte ich** eine im Pending-Status wartende Konfig per CLI-Befehl bestätigen oder ablehnen können,
**damit** ich den manuellen Review-Schritt ohne Webinterface abschließen kann (Vorarbeit für M4).

**Akzeptanzkriterien:**
- [ ] `python run_pipeline.py --approve-config kaufmann-bueromanagement` → verschiebt Konfig von `/pending/` nach `/konfig/`, startet vollständige Verarbeitung des PDFs
- [ ] `python run_pipeline.py --reject-config fachinformatiker` → löscht Pending-Konfig, PDF → `/fehler/` mit Typ `KONFIG_ABGELEHNT`
- [ ] Beide Aktionen fragen zur Sicherheit nach Bestätigung: "Bestätigen? [j/N]"
- [ ] `--approve-config` schreibt Version als `manuell` und setzt Major-Bump

**Priorität:** Could Have | **Aufwand:** S

---

## Story-Übersicht M2

| ID | Titel | Epic | Priorität | Aufwand | PRD-Ref |
|----|-------|------|-----------|---------|---------|
| M2-01 | Konfig-Lookup: bekannte Berufe ohne LLM | E6 | Must Have | XS | F-12 |
| M2-02 | Unbekannte Layouts erkennen & KI triggern | E6 | Must Have | XS | F-09 |
| M2-03 | Claude API Anbindung & Konfiguration | E7 | Must Have | S | — |
| M2-04 | Fallback bei API Nicht-Verfügbarkeit | E7 | Must Have | XS | — |
| M2-05 | System-Prompt & Konfig-Generierungs-Prompt | E8 | Must Have | L | F-09, F-10 |
| M2-06 | Claude-Antwort parsen und YAML extrahieren | E8 | Must Have | M | F-10 |
| M2-07 | Generierte Konfig intern testen (Dry-Run) | E8 | Must Have | M | F-10 |
| M2-08 | Konfidenz-Score auslesen und persistieren | E9 | Must Have | S | F-13 |
| M2-09 | Schwellwert-Routing: auto vs. Review | E9 | Must Have | M | F-13 |
| M2-10 | Konfig-Datei speichern und versionieren | E10 | Should Have | M | F-11 |
| M2-11 | Konfig-Bibliothek per CLI auflisten | E10 | Should Have | S | F-31 |
| M2-12 | Review-Konfig manuell bestätigen per CLI | E10 | Could Have | S | F-11 |

**Gesamtaufwand M2:** 9 Must Have + 2 Should Have + 1 Could Have Stories

---

## Abhängigkeiten zu M1

| M2-Story | Benötigt aus M1 |
|----------|-----------------|
| M2-01 | M1-09 (Konfig-Format definiert) |
| M2-05 | M1-08 (JSON-Ziel-Schema als Prompt-Referenz) |
| M2-07 | M1-10, M1-11 (V1+V2 Gates für internen Dry-Run) |
| M2-09 | M1-12, M1-13 (Archiv/Fehler-Routing) |

---

## Empfohlene Implementierungsreihenfolge

```
Phase 1 — Routing-Logik (E6)
  M2-01 → M2-02

Phase 2 — API-Infrastruktur (E7)
  M2-03 → M2-04   ← API zuerst, dann Fallback

Phase 3 — Prompt & Parsing (E8)
  M2-05 → M2-06 → M2-07   ← Prompt zuerst iterieren, dann Parsing, dann Dry-Run

Phase 4 — Scoring & Routing (E9)
  M2-08 → M2-09   ← Score erst lesen, dann Routing-Logik implementieren

Phase 5 — Bibliothek (E10)
  M2-10 → M2-11 → [M2-12 optional]
```

---

## Prompt-Engineering Hinweise

### Wichtigste Designentscheidungen

| Entscheidung | Begründung |
|---|---|
| One-Shot-Beispiel (Anlagenmechaniker) im Prompt | Reduziert Format-Abweichungen drastisch |
| Konfidenz-Score als Teil der YAML (nicht separater JSON-Block) | Verhindert Parsing in zwei Formaten |
| `unsichereFelder[]` als explizite Liste | Gibt dem Prüfer den genauen Fokuspunkt |
| Kein freier Erklärungstext außerhalb der YAML | Vereinfacht robustes Parsing |

### Prompt-Iterationsstrategie für den Hackathon

1. Prompt mit 3 bekannten Test-PDFs (Anlagenmechaniker, Industriemechaniker, Elektroanlagenmonteur) testen
2. Score-Kalibrierung: erwarteter Score für manuelle Referenz-Konfigs ≥ 90
3. Grenzfall testen: 2-Tabellen-Seite mit unklarer Spaltenbezeichnung

---

## Test-Szenarien M2 (Smoke Tests)

| Szenario | Erwartetes Ergebnis |
|----------|---------------------|
| Beruf mit vorhandener Konfig | Kein API-Call, direkte Verarbeitung |
| Neuer Beruf, klares Layout | Konfig generiert, Score ≥ 85, auto gespeichert |
| Neuer Beruf, unklares Layout | Score < 85, Konfig in `/konfig/pending/`, Status `ZUR_REVIEW` |
| API-Key fehlt, bekannte Berufe | Pipeline läuft für bekannte Berufe durch |
| API-Key fehlt, unbekannter Beruf | `KI_NICHT_VERFUEGBAR`, Beruf → `/fehler/` |
| API-Timeout nach 3 Versuchen | Sauberer Fallback, kein Absturz |
| Claude antwortet mit Freitext + YAML | YAML korrekt extrahiert |
| Claude antwortet mit ungültigem YAML | `KI_ANTWORT_UNGUELTIG`, Beruf → `/fehler/` |
| Dry-Run: generierte Konfig schlägt V2 an | Konfig → `/pending/`, nicht auto gespeichert |
| `--list-configs` | Tabelle aller Konfigs inkl. Pending |
