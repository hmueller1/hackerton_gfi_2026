# Backlog M3 — Next.js-Frontend

**Meilenstein:** M3 — Vollständiges Next.js-Frontend (Dashboard, JSON-Browser, Fehler-UI)
**Release:** Vollständig
**Datum:** 2026-02-24
**Voraussetzung:** M1 abgeschlossen; M2 parallel oder abgeschlossen
**Ziel:** Vollwertiges Webinterface für Pipeline-Steuerung, Status-Übersicht, JSON-Anzeige und Fehler-Management. Noch kein Dual-View (→ M4), aber alle übrigen UI-Seiten lauffähig.

---

## Definition of Done (M3)

- [ ] Next.js-App startet lokal (`npm run dev`) und zeigt ein Dashboard
- [ ] Pipeline-Lauf lässt sich per Button starten; Status wird pro Beruf angezeigt
- [ ] Alle verarbeiteten JSONs sind im Browser durchsuchbar und lesbar
- [ ] Fehler-Liste zeigt Fehlertyp und ermöglicht PDF-Download
- [ ] Konfig-Bibliothek listet alle gespeicherten Konfigs inkl. Pending
- [ ] FastAPI-Service ist als Docker-Compose-Service definiert und erreichbar

---

## Epics

| Epic | Beschreibung | Stories |
|------|-------------|---------|
| E11 | Projekt-Setup & Infrastruktur | M3-01 bis M3-03 |
| E12 | Dashboard & Pipeline-Steuerung | M3-04 bis M3-06 |
| E13 | JSON-Browser | M3-07 bis M3-08 |
| E14 | Fehler-Management UI | M3-09 bis M3-10 |
| E15 | Konfig-Bibliothek UI | M3-11 bis M3-12 |

---

## E11 — Projekt-Setup & Infrastruktur

---

### M3-01 · Next.js-Projektstruktur anlegen

**Als** Entwickler
**möchte ich** eine saubere Next.js-Projektstruktur mit TypeScript, Tailwind CSS und App Router,
**damit** alle UI-Komponenten auf einem einheitlichen, wartbaren Fundament aufbauen.

**Akzeptanzkriterien:**
- [ ] `npx create-next-app@latest` mit TypeScript, Tailwind, App Router, src/-Verzeichnis
- [ ] Ordnerstruktur: `src/app/`, `src/components/`, `src/lib/`, `src/types/`
- [ ] Globale TypeScript-Typen für das JSON-Schema (`Beruf`, `Prüfungsbereich`, `Aufgabe`, `Gewichtung`) in `src/types/schema.ts`
- [ ] Tailwind-Konfiguration mit einfachem Design-System (Farben: neutral/slate, Akzent: blue-600)
- [ ] ESLint + Prettier konfiguriert
- [ ] `npm run dev` startet ohne Fehler auf Port 3000

**Projektstruktur (Referenz):**
```
src/
  app/
    layout.tsx          # Root Layout mit Navigation
    page.tsx            # Dashboard (/)
    berufe/
      page.tsx          # JSON-Browser (/berufe)
      [beruf]/
        page.tsx        # Einzelansicht (/berufe/elektrotechnik)
    fehler/
      page.tsx          # Fehler-Liste (/fehler)
    konfig/
      page.tsx          # Konfig-Bibliothek (/konfig)
      [beruf]/
        verify/
          page.tsx      # Dual-View (/konfig/elektrotechnik/verify) → M4
  components/
    ui/                 # Basis-Komponenten (Button, Badge, Card, Table)
    layout/             # Navigation, Sidebar, PageHeader
    beruf/              # Beruf-spezifische Komponenten
  lib/
    api.ts              # API-Client (fetch-Wrapper für FastAPI)
    utils.ts            # Hilfsfunktionen
  types/
    schema.ts           # JSON-Schema-Typen
    api.ts              # API-Response-Typen
```

**Priorität:** Must Have | **Aufwand:** M

---

### M3-02 · FastAPI-Service mit Docker Compose verbinden

**Als** Entwickler
**möchte ich** Next.js und FastAPI per Docker Compose gemeinsam starten können,
**damit** das gesamte System mit einem einzigen Befehl lauffähig ist.

**Akzeptanzkriterien:**
- [ ] `docker-compose.yml` definiert zwei Services: `frontend` (Next.js, Port 3000) und `api` (FastAPI, Port 8000)
- [ ] Shared Volume für `/data`-Ordner (beide Services lesen/schreiben dieselben Dateien)
- [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local` konfigurierbar
- [ ] FastAPI-Service antwortet auf `GET /health` mit `{"status": "ok"}`
- [ ] `docker compose up` startet alles; `docker compose up --build` nach Code-Änderungen

**docker-compose.yml (Referenz):**
```yaml
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    volumes: ["./data:/app/data"]
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATA_DIR=/app/data

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on: [api]
```

**Priorität:** Must Have | **Aufwand:** M

---

### M3-03 · API-Client-Abstraktion in Next.js

**Als** Entwickler
**möchte ich** einen zentralen, typsicheren API-Client für alle FastAPI-Aufrufe,
**damit** API-URL-Änderungen und Fehlerbehandlung an einer einzigen Stelle verwaltet werden.

**Akzeptanzkriterien:**
- [ ] `src/lib/api.ts` exportiert typisierte Funktionen für alle benötigten Endpoints
- [ ] Alle Fetch-Aufrufe enthalten Timeout (Standard: 30 Sekunden)
- [ ] HTTP-Fehler werden in typisierte `ApiError`-Objekte umgewandelt
- [ ] API-Base-URL kommt aus `NEXT_PUBLIC_API_URL`

**API-Client (Referenz):**
```typescript
// src/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getBerufe(): Promise<BerufStatus[]> { ... }
export async function getBeruf(beruf: string): Promise<BerufDaten> { ... }
export async function startPipeline(options?: PipelineOptions): Promise<PipelineJob> { ... }
export async function getPipelineStatus(jobId: string): Promise<PipelineStatus> { ... }
export async function getFehler(): Promise<FehlerEintrag[]> { ... }
export async function getKonfigs(): Promise<KonfigEintrag[]> { ... }
```

**Priorität:** Must Have | **Aufwand:** S

---

## E12 — Dashboard & Pipeline-Steuerung

---

### M3-04 · Dashboard: Status-Übersicht aller Berufe

**Als** Datenkoordinator
**möchte ich** auf dem Dashboard auf einen Blick den Verarbeitungsstatus aller Berufe sehen,
**damit** ich sofort erkenne, welche Berufe Aufmerksamkeit benötigen.

**Akzeptanzkriterien:**
- [ ] Dashboard zeigt 4 Status-Karten: Verarbeitet / Fehlerhaft / Zur Review / Ausstehend (mit Anzahl)
- [ ] Tabelle aller Berufe: Name, Status-Badge (farbkodiert), Jahr, Konfig-Version, Zeitstempel
- [ ] Status-Badges: ✓ Verarbeitet (grün) | ✗ Fehlerhaft (rot) | ⚠ Zur Review (gelb) | ○ Ausstehend (grau)
- [ ] Tabelle ist sortierbar (nach Name, Status, Datum) und filterbar (nach Status)
- [ ] Klick auf Beruf-Zeile → navigiert zur Einzelansicht `/berufe/{beruf}`
- [ ] Seite aktualisiert sich automatisch alle 5 Sekunden während ein Pipeline-Lauf aktiv ist

**Priorität:** Must Have | **Aufwand:** M

---

### M3-05 · Pipeline-Lauf per UI-Button starten

**Als** Datenkoordinator
**möchte ich** den Pipeline-Lauf direkt im Browser starten können,
**damit** ich kein Terminal öffnen muss.

**Akzeptanzkriterien:**
- [ ] "Pipeline starten"-Button im Dashboard-Header
- [ ] Button löst `POST /api/pipeline/start` aus (Next.js API Route → FastAPI)
- [ ] Nach Start: Button wechselt zu "Läuft..." (deaktiviert), Spinner sichtbar
- [ ] Pro Beruf erscheint in Echtzeit eine Status-Zeile (SSE oder Polling alle 2s)
- [ ] Nach Abschluss: Zusammenfassungs-Toast: "Pipeline abgeschlossen: 12 ✓ | 2 ✗ | 1 ⚠"
- [ ] Während Pipeline läuft: kein zweiter Start möglich

**FastAPI-Endpoint (Referenz):**
```python
@router.post("/pipeline/start")
async def start_pipeline(background_tasks: BackgroundTasks):
    job_id = str(uuid4())
    background_tasks.add_task(run_pipeline_job, job_id)
    return {"jobId": job_id, "status": "gestartet"}

@router.get("/pipeline/status/{job_id}")
async def get_status(job_id: str):
    return pipeline_status_store.get(job_id)
```

**Priorität:** Must Have | **Aufwand:** L

---

### M3-06 · Pipeline-Fortschritt in Echtzeit anzeigen

**Als** Datenkoordinator
**möchte ich** während des laufenden Pipeline-Durchlaufs den Fortschritt pro Beruf live sehen,
**damit** ich nicht auf die CLI-Ausgabe angewiesen bin.

**Akzeptanzkriterien:**
- [ ] Fortschritts-Leiste (Prozent: verarbeitete / gesamt PDFs)
- [ ] Live-Log-Liste: pro Beruf eine Zeile mit Icon (✓/✗/⚠/⚙), Name, Status, Dauer
- [ ] Neue Einträge erscheinen ohne Seitenreload (SSE oder Polling alle 2s)
- [ ] Nach Abschluss: Log bleibt sichtbar; "Neuer Lauf"-Button erscheint
- [ ] Fehlerhafte Einträge sind anklickbar → direkt zur Fehler-Detail-Ansicht

**Priorität:** Should Have | **Aufwand:** M

---

## E13 — JSON-Browser

---

### M3-07 · Berufe-Übersicht: alle extrahierten JSONs auflisten

**Als** Fachexperte BPÜ
**möchte ich** alle erfolgreich extrahierten Berufe in einer durchsuchbaren Liste sehen,
**damit** ich schnell zum gewünschten Beruf navigieren kann.

**Akzeptanzkriterien:**
- [ ] `/berufe`-Seite listet alle JSONs aus `/ausgabe/`
- [ ] Suchfeld filtert Berufe live (client-seitig, keine API-Anfrage nötig)
- [ ] Pro Eintrag: Berufname, Jahr, Prüfungstyp, Anzahl Prüfungsbereiche, Verarbeitungsdatum
- [ ] Klick auf Eintrag → Einzelansicht `/berufe/{beruf}`
- [ ] Leerer Zustand: "Noch keine Berufe verarbeitet — Pipeline starten"

**Priorität:** Must Have | **Aufwand:** S

---

### M3-08 · Beruf-Einzelansicht: JSON strukturiert anzeigen

**Als** Fachexperte BPÜ
**möchte ich** das extrahierte JSON eines Berufs strukturiert und lesbar im Browser sehen,
**damit** ich die Korrektheit der Daten ohne JSON-Kenntnisse prüfen kann.

**Akzeptanzkriterien:**
- [ ] `/berufe/{beruf}`-Seite zeigt alle Felder in strukturierter Ansicht
- [ ] Prüfungsbereiche als aufklappbare Akkordeon-Abschnitte (schriftlich/praktisch farblich unterschieden)
- [ ] Gewichtungen als visuelle Prozent-Balken dargestellt
- [ ] "Rohdaten anzeigen"-Toggle zeigt formatierten JSON-Code (syntax-highlighted)
- [ ] "JSON herunterladen"-Button (direkter Download der .json-Datei)
- [ ] Breadcrumb: Dashboard → Berufe → {Berufname}

**Priorität:** Must Have | **Aufwand:** M

---

## E14 — Fehler-Management UI

---

### M3-09 · Fehler-Liste mit Fehlertyp und Details

**Als** Datenkoordinator
**möchte ich** alle fehlerhaften Berufe mit Fehlertyp und Beschreibung in einer übersichtlichen Liste sehen,
**damit** ich Fehler ohne Terminal-Zugriff priorisieren und verstehen kann.

**Akzeptanzkriterien:**
- [ ] `/fehler`-Seite listet alle Einträge aus `/fehler/**/*.fehler.json`
- [ ] Pro Eintrag: Berufname, Fehlertyp-Badge, Fehlermeldung (Kurzform), Datum
- [ ] Fehlertypen farbkodiert: V1_SCHEMA_FEHLER (orange), V2_KONSISTENZ_FEHLER (orange), PARSING_FAILED (rot), KONFIG_FEHLT (gelb), KI_NICHT_VERFUEGBAR (grau)
- [ ] Klick auf Eintrag → expandiert Detail-Panel mit vollständiger Fehlermeldung und `details`-JSON
- [ ] Filtermöglichkeit nach Fehlertyp
- [ ] Leerer Zustand: "Keine Fehler — alles in Ordnung ✓"

**Priorität:** Must Have | **Aufwand:** M

---

### M3-10 · Fehler-PDF herunterladen und Einzellauf starten

**Als** Datenkoordinator
**möchte ich** direkt aus der Fehler-Liste heraus das fehlerhafte PDF herunterladen und einen Einzellauf starten können,
**damit** ich Fehler ohne Dateisystem-Navigation beheben kann.

**Akzeptanzkriterien:**
- [ ] "PDF herunterladen"-Button pro Fehler-Eintrag → direkter Datei-Download
- [ ] "Erneut verarbeiten"-Button startet Einzellauf (`POST /api/pipeline/run-single`)
- [ ] Nach Start: Status-Indikator im Eintrag (läuft / erfolgreich / fehlerhaft)
- [ ] Bei Erfolg: Eintrag verschwindet aus Fehler-Liste, erscheint im Dashboard als "Verarbeitet"

**Priorität:** Should Have | **Aufwand:** S

---

## E15 — Konfig-Bibliothek UI

---

### M3-11 · Konfig-Bibliothek: alle Konfigs anzeigen

**Als** Datenkoordinator
**möchte ich** alle gespeicherten Konfigs in einer übersichtlichen Tabelle sehen,
**damit** ich den Stand der Konfig-Bibliothek ohne CLI-Kommando im Blick habe.

**Akzeptanzkriterien:**
- [ ] `/konfig`-Seite zeigt zwei Tabellen: "Aktive Konfigs" und "Zur Review (Pending)"
- [ ] Aktive Konfigs: Beruf, Version, Score, Erstellt durch (ki/manuell), Datum
- [ ] Pending-Konfigs: Beruf, Score, Begründung (Kurzform), Datum — hervorgehoben (gelber Hintergrund)
- [ ] Klick auf Konfig-Eintrag → YAML-Inhalt in Modal oder Side-Panel (read-only)
- [ ] Pending-Eintrag: "Prüfen"-Button → navigiert zu `/konfig/{beruf}/verify` (M4)

**Priorität:** Must Have | **Aufwand:** M

---

### M3-12 · Navigation & globales Layout

**Als** Nutzer
**möchte ich** über eine persistente Navigation zwischen allen Seiten wechseln können,
**damit** ich jederzeit weiß, wo ich bin und wohin ich navigieren kann.

**Akzeptanzkriterien:**
- [ ] Sidebar oder Top-Navigation mit Links: Dashboard, Berufe, Fehler, Konfig-Bibliothek
- [ ] Aktive Seite ist visuell hervorgehoben
- [ ] Badge-Zähler an "Fehler" (Anzahl offener Fehler) und "Zur Review" (Anzahl Pending)
- [ ] Responsive: auf kleinen Bildschirmen kollabierbare Navigation
- [ ] Seitentitel im `<title>`-Tag passend zur aktuellen Seite

**Priorität:** Must Have | **Aufwand:** S

---

## Story-Übersicht M3

| ID | Titel | Epic | Priorität | Aufwand | PRD-Ref |
|----|-------|------|-----------|---------|---------|
| M3-01 | Next.js-Projektstruktur anlegen | E11 | Must Have | M | — |
| M3-02 | FastAPI mit Docker Compose verbinden | E11 | Must Have | M | — |
| M3-03 | API-Client-Abstraktion | E11 | Must Have | S | — |
| M3-04 | Dashboard: Status-Übersicht | E12 | Must Have | M | F-30 |
| M3-05 | Pipeline-Lauf per UI-Button starten | E12 | Must Have | L | F-02, F-30 |
| M3-06 | Pipeline-Fortschritt in Echtzeit | E12 | Should Have | M | F-30 |
| M3-07 | Berufe-Übersicht: alle JSONs auflisten | E13 | Must Have | S | F-32 |
| M3-08 | Beruf-Einzelansicht: JSON anzeigen | E13 | Must Have | M | F-32 |
| M3-09 | Fehler-Liste mit Fehlertyp und Details | E14 | Must Have | M | F-34 |
| M3-10 | Fehler-PDF herunterladen & Einzellauf | E14 | Should Have | S | F-34 |
| M3-11 | Konfig-Bibliothek UI | E15 | Must Have | M | F-31 |
| M3-12 | Navigation & globales Layout | E15 | Must Have | S | — |

**Gesamtaufwand M3:** 9 Must Have + 3 Should Have Stories

---

## Empfohlene Implementierungsreihenfolge

```
Phase 1 — Fundament (E11)
  M3-01 → M3-02 → M3-03

Phase 2 — Kern-UI (E12 + E13)
  M3-12 → M3-04 → M3-07 → M3-08

Phase 3 — Pipeline-Steuerung (E12)
  M3-05 → M3-06

Phase 4 — Fehler & Konfig (E14 + E15)
  M3-09 → M3-10 → M3-11
```

---

## FastAPI-Endpoints (benötigt für M3)

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/health` | GET | Health-Check |
| `/berufe` | GET | Liste aller verarbeiteten Berufe |
| `/berufe/{beruf}` | GET | JSON eines Berufs |
| `/fehler` | GET | Liste aller Fehler-Einträge |
| `/fehler/{beruf}/download` | GET | Download des Fehler-PDFs |
| `/konfig` | GET | Liste aller Konfigs (aktiv + pending) |
| `/konfig/{beruf}` | GET | YAML-Inhalt einer Konfig |
| `/pipeline/start` | POST | Batch-Lauf starten |
| `/pipeline/run-single` | POST | Einzellauf für einen Beruf |
| `/pipeline/status/{job_id}` | GET | Status eines laufenden Jobs |

---

## Test-Szenarien M3

| Szenario | Erwartetes Ergebnis |
|----------|---------------------|
| Dashboard lädt ohne Berufe | Leerer Zustand mit Hinweistext |
| Dashboard mit 5 Berufen (2 ok, 1 fehler, 1 review, 1 ausstehend) | Korrekte Badge-Zähler und farbkodierte Tabelle |
| "Pipeline starten" klicken | Button deaktiviert, Fortschritt sichtbar |
| Beruf-Einzelansicht aufrufen | JSON strukturiert angezeigt, Gewichtungsbalken korrekt |
| Fehler-Liste mit 3 Einträgen | Alle 3 korrekt nach Typ farbkodiert |
| PDF-Download-Button | Browser-Download startet |
| Navigation-Badges | Korrekte Zähler an "Fehler" und "Zur Review" |
