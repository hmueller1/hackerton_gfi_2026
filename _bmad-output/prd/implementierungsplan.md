# Implementierungsplan — BPÜ Datenextraktions-Pipeline

**Datum:** 2026-02-24
**Basis:** Backlogs M1–M5 (58 Stories)
**Kontext:** Hackathon — Pragmatismus vor Perfektion; Demo-Readiness hat Priorität

---

## Ausgangssituation

| Fakt | Bedeutung |
|------|-----------|
| **Kein Code vorhanden** | Greenfield — Repository-Struktur muss erst angelegt werden |
| **115 echte Test-PDFs verfügbar** | `doc/berufe/pages/` — sofort nutzbar, kein Warten auf Testdaten |
| **Klare Architektur** | Python FastAPI (Backend) + Next.js (Frontend) — Entscheidung gefallen |
| **Vollständige Backlogs** | M1–M5 mit 58 Stories, Akzeptanzkriterien und Code-Referenzen |
| **Claude Code verfügbar** | Direkte Implementierungsunterstützung Story für Story |

---

## Schritt 1 — Repository-Struktur anlegen (sofort, ~30 Min.)

Bevor Entwicklung beginnt, muss die Ordnerstruktur stehen. Diese Struktur muss **einmalig, gemeinsam, manuell** angelegt werden:

```
hackerton_gfi_2026/          ← vorhandenes Git-Root
  api/                       ← Python FastAPI Service (NEU)
    routers/
    services/
    models/
    prompts/
    tests/
    Dockerfile
    requirements.txt
    main.py
  frontend/                  ← Next.js App (NEU)
    src/
      app/
      components/
      lib/
      types/
    Dockerfile
    package.json
  data/                      ← Laufzeit-Daten (NEU, in .gitignore)
    eingang/
    archiv/
    fehler/
    ausgabe/
    konfig/
      pending/
      archiv/
      clustering/
    reports/
  demo/                      ← Demo-Skripte (NEU)
    README.md
    reset.sh
  docker-compose.yml         ← NEU
  .env.example               ← NEU (ohne echte Keys)
  doc/                       ← vorhanden (PDFs)
  _bmad-output/              ← vorhanden (Backlogs, PRD)
```

**Wichtig:** `data/` in `.gitignore` eintragen — keine Berufsdaten ins Repository.

---

## Schritt 2 — Entwicklungsumgebung einrichten (~45 Min.)

### Python-Backend (api/)

```bash
# Virtuelle Umgebung
python -m venv .venv
.venv\Scripts\activate          # Windows

# Abhängigkeiten
pip install fastapi uvicorn pdfplumber anthropic pyyaml jsonschema tenacity pytest httpx

# requirements.txt generieren
pip freeze > api/requirements.txt

# Server starten (Entwicklung)
uvicorn api.main:app --reload --port 8000
```

### Next.js-Frontend (frontend/)

```bash
npx create-next-app@latest frontend \
  --typescript --tailwind --app --src-dir --no-git

cd frontend
npm install        # Basis-Pakete
npm install @codemirror/state @codemirror/view    # YAML-Editor (M4)
npm run dev        # startet auf Port 3000
```

### Umgebungsvariablen (.env)

```bash
# .env (lokal, nie committen)
ANTHROPIC_API_KEY=sk-ant-...
DATA_DIR=./data
KONFIDENZ_SCHWELLWERT=85
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Schritt 3 — Meilenstein-Reihenfolge

### Übersicht

```
Woche/Tag  Backend-Strang (api/)          Frontend-Strang (frontend/)
───────────────────────────────────────────────────────────────────────
Phase A    M1: Basis-Pipeline             [wartet auf M1-Endpoints]
           (Stories M1-01 bis M1-14)

Phase B    M2: KI-Konfig                  M3: Next.js-Frontend
           (Stories M2-01 bis M2-12)      (Stories M3-01 bis M3-12)
           [PARALLEL möglich]             [PARALLEL möglich]

Phase C    M4: Integration & Dual-View
           (Stories M4-01 bis M4-10)
           [Braucht M2 + M3 fertig]

Phase D    M5: Clustering, Export, Audit
           (Stories M5-01 bis M5-10)
```

---

### Phase A — M1: Basis-Pipeline

**Ziel:** `python run_pipeline.py` verarbeitet ein PDF zu validem JSON.

**Reihenfolge der Stories (Implementierungssequenz):**

```
1. M1-01  Ordnerstruktur anlegen
   └─ Einstiegspunkt: api/services/folder_manager.py

2. M1-02  Pfad-Konfiguration
   └─ api/config.py mit dotenv

3. M1-03  Metadaten aus Pfad lesen
   └─ api/services/path_parser.py

4. M1-04  CLI-Einstiegspunkt
   └─ api/run_pipeline.py (argparse)

5. M1-05  pdfplumber-Extraktion
   └─ api/services/pdf_extractor.py

6. M1-06  Mehrtabellen-Erkennung (Bounding-Box)
   └─ Erweiterung von pdf_extractor.py

7. M1-09  Konfig-Format definieren (YAML-Schema)
   └─ api/services/config_manager.py  ← VOR JSON-Mapping!

8. M1-08  JSON-Schema-Transformation
   └─ api/services/schema_mapper.py

9. M1-10  V1 Schema-Gate
   └─ api/services/validation.py

10. M1-11  V2 Numerische Konsistenz
    └─ Erweiterung von validation.py

11. M1-12  Archiv-Routing
    └─ api/services/file_router.py

12. M1-13  Fehler-Routing + Fehlerlog
    └─ Erweiterung von file_router.py

13. M1-14  CLI-Zusammenfassung
    └─ Erweiterung von run_pipeline.py

14. M1-07  Camelot-Fallback [optional, zuletzt]
```

**Erster Meilenstein-Test:**
```bash
# 1 echtes PDF aus doc/berufe/pages/ in den Eingangsordner
cp "doc/berufe/pages/gesamt-bpue-w25-data_1.pdf" "data/eingang/2026/anlagenmechaniker/"
python api/run_pipeline.py
# Erwartung: ausgabe/anlagenmechaniker.json erzeugt, V1+V2 bestanden
```

---

### Phase B — M2 + M3 parallel

**M2 (Backend): KI-Konfig-Generierung**

```
1. M2-01  Konfig-Lookup (bekannt → direkt)
2. M2-02  Unbekannt → KI-Trigger
3. M2-03  Claude API Client (api/services/ai_client.py)
4. M2-04  API-Fallback
5. M2-05  Prompts schreiben (api/prompts/generate_config.txt)
6. M2-06  Antwort-Parser (YAML extrahieren)
7. M2-07  Interner Dry-Run nach Generierung
8. M2-08  Score auslesen + persistieren
9. M2-09  Schwellwert-Routing (auto vs. pending/)
10. M2-10  Konfig-Versionierung [should have]
11. M2-11  CLI: --list-configs [should have]
12. M2-12  CLI: --approve/--reject [could have]
```

**M3 (Frontend): Next.js aufbauen**

```
1. M3-01  Next.js-Projekt initialisieren
2. M3-02  Docker Compose anlegen
3. M3-03  API-Client (src/lib/api.ts)
4. M3-12  Navigation + globales Layout
5. M3-04  Dashboard (Status-Karten + Tabelle)
6. M3-07  Berufe-Übersicht
7. M3-08  Beruf-Einzelansicht (JSON strukturiert)
8. M3-09  Fehler-Liste
9. M3-05  Pipeline-Button + Job-Start
10. M3-11  Konfig-Bibliothek UI
11. M3-06  Echtzeit-Fortschritt [should have]
12. M3-10  PDF-Download + Einzellauf [should have]
```

**Wichtig für M3:** FastAPI muss für M3-Entwicklung zumindest mit Mock-Daten antworten. Entweder M2-Backend-Team liefert echte Endpoints, oder kurze Mock-Endpoints als Platzhalter.

---

### Phase C — M4: Integration

**Voraussetzung:** M2 (Backend läuft durch) + M3 (Frontend-Seiten existieren)

```
1. M4-09  FastAPI-Endpoints für Dual-View
   └─ api/routers/konfig.py: /pending, /dry-run, /approve, /reject

2. M4-01  Pending-Konfig im Dashboard hervorheben
3. M4-02  Dual-View Grundlayout (/konfig/{beruf}/verify)
4. M4-04  Dry-Run beim Öffnen der Dual-View
5. M4-03  Unsichere Felder hervorheben
6. M4-05  YAML-Editor (CodeMirror/Monaco)
7. M4-06  Dry-Run-Retry bei YAML-Änderung
8. M4-07  Bestätigen-Gate
9. M4-08  Ablehnen mit Pflicht-Begründung
10. M4-10  End-to-End-Smoke-Test
```

---

### Phase D — M5: Polish & Demo

```
1. M5-09  Demo-Datensatz vorbereiten (sofort anfangen, parallel zu Phase C!)
2. M5-01  Feature-Extraktion pro PDF
3. M5-02  Format-Clustering
4. M5-03  Sample-Validation + Cluster-Erbschaft
5. M5-04  Unbekannte Layout-Typen isolieren
6. M5-05  HTML-Export einzelner Beruf
7. M5-07  Validation-Report im Browser
8. M5-10  Performance-Test 50 PDFs [should have]
9. M5-06  Batch-HTML-Export als ZIP [could have]
10. M5-08  V3 LLM-Rückverifikation [could have]
```

---

## Schritt 4 — Arbeitsmodus mit Claude Code

### Wie jede Story umgesetzt wird

Für jede Story gibt es eine optimale Vorgehensweise:

**1. Neue Story starten:**
> "Implementiere M1-05: pdfplumber-Extraktion. Die Akzeptanzkriterien sind im Backlog unter `_bmad-output/prd/backlog-m1.md` unter M1-05 beschrieben."

Claude Code liest das Backlog, implementiert die Story und schreibt die Datei.

**2. Nach der Implementierung testen:**
> "Führe den Smoke-Test für M1-05 aus: Extrahiere Tabellen aus `doc/berufe/pages/gesamt-bpue-w25-data_1.pdf` und zeige das Ergebnis."

**3. Nächste Story:**
> "M1-05 ist fertig. Weiter mit M1-06: Mehrtabellen-Erkennung via Bounding-Box."

### Empfohlene Kontextverwaltung

- **Pro Story ein frisches Kontextfenster** — verhindert Kontext-Drift bei langen Sessions
- **Backlog als Referenz mitgeben** — "Lies `backlog-m1.md`, Story M1-06"
- **Nach je 3–4 Stories committen** — kleiner, nachvollziehbarer Commits

---

## Schritt 5 — Erste Aktion: Konfig-Vorlage aus echten PDFs ableiten

**Vor der Implementierung von M1-08 (JSON-Mapping)** muss bekannt sein, wie die echten PDFs aussehen. Das ist der wichtigste Vorbereitungsschritt:

```
Aufgabe (jetzt, vor der Implementierung):

1. 3 verschiedene PDFs aus doc/berufe/pages/ öffnen
   (z.B. Seite 1, 15, 50 — für Stichprobe verschiedener Berufe)

2. Folgende Fragen klären:
   - Wie viele Tabellen pro Seite? (1 oder 2?)
   - Welche Spalten gibt es? (Name, Zeit, Gewichtung?)
   - Sind Tabellen transponiert? (Kopfzeile links statt oben?)
   - Wie sind Prüfungsbereiche aufgeteilt? (schriftlich/praktisch)

3. Erste handcodierte Konfig für 1 Beruf erstellen
   → data/konfig/beispiel-beruf.yaml

4. Diese Konfig als Vorlage für M1-09 und M2-05 (Prompt) nutzen
```

**Claude Code kann dabei helfen:**
> "Lies `doc/berufe/pages/gesamt-bpue-w25-data_1.pdf` und beschreibe die Tabellenstruktur: Anzahl Tabellen, Spaltenbezeichnungen, ob Transponierung vorliegt."

---

## Schritt 6 — Kritische Entscheidungen vor der Implementierung

Diese Punkte **müssen vor dem Coden** geklärt sein — sie betreffen das gesamte System:

### Entscheidung 1: Gehören mehrere PDF-Seiten zu einem Beruf?

Die vorhandenen PDFs in `doc/berufe/pages/` sind Einzelseiten des Gesamtdokuments. Die Pipeline erwartet ein PDF pro Beruf.

**Frage:** Sind manche Berufe über 2 Seiten verteilt? Falls ja → Pipeline muss Seiten zusammenführen.

**Aktion:** 5 aufeinanderfolgende Seiten prüfen, ob sie zu demselben oder verschiedenen Berufen gehören.

### Entscheidung 2: Eingabe-Format der PDFs

**Option A:** Pipeline verarbeitet Einzelseiten-PDFs direkt (jede Seite = ein Beruf).
**Option B:** Pipeline erwartet mehrseitige PDFs pro Beruf (Seiten müssen vorab zusammengeführt werden).

Diese Entscheidung beeinflusst M1-03 (Metadaten aus Pfad) und M1-05 (pdfplumber-Extraktion).

### Entscheidung 3: JSON-Schema final absegnen

Das JSON-Ziel-Schema aus M1-08 ist die **zentrale Datenstruktur**. Alle anderen Komponenten bauen darauf auf. Es muss vor der Implementierung von M1-08 final bestätigt sein.

Das vorgeschlagene Schema steht in `backlog-m1.md` unter M1-08.

---

## Zusammenfassung: Die nächsten konkreten Schritte

```
JETZT (heute):

□ 1. Repository-Struktur anlegen (api/, frontend/, data/, docker-compose.yml)
□ 2. .env.example mit API-Key-Platzhalter anlegen
□ 3. 3–5 PDFs aus doc/berufe/pages/ öffnen → Tabellenstruktur verstehen
□ 4. Entscheidung: Einzelseite = 1 Beruf? Oder Mehrseiter?
□ 5. JSON-Schema aus M1-08 absegnen

DANACH (M1 starten):

□ 6. Python-Venv anlegen, pdfplumber installieren
□ 7. "Implementiere M1-01 bis M1-04" → Claude Code
□ 8. Ersten CLI-Lauf mit einem echten PDF testen
□ 9. "Implementiere M1-05 bis M1-11" → Claude Code
□ 10. M1 Definition of Done prüfen → alle 7 Smoke-Tests grün

DANACH (M2 + M3 parallel):

□ 11. Claude API Key besorgen / aktivieren
□ 12. M2-03 zuerst (API-Client) → M2-05 (Prompt iterieren mit echten PDFs)
□ 13. Next.js-Projekt anlegen (M3-01) → Dashboard-Grundgerüst (M3-04)
```

---

## Risiken & Gegenmaßnahmen

| Risiko | Wahrscheinlichkeit | Gegenmaßnahme |
|--------|-------------------|---------------|
| PDF-Struktur komplexer als erwartet | Hoch | Früh 10+ echte PDFs analysieren (vor M1-08) |
| KI-Konfig-Qualität unzureichend | Mittel | Prompt-Iteration mit 3 bekannten PDFs, One-Shot-Beispiel |
| M2 + M3 blockieren sich gegenseitig | Mittel | Mock-Endpoints für Frontend; echter Backend parallel |
| Zeitdruck: M5 nicht fertig | Niedrig | M5 ist vollständig optional; Demo funktioniert ab M4 |
| Camelot-Installation (Ghostscript) | Mittel | pdfplumber als primär, Camelot skip bis M1 stabil |
