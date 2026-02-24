# PRD — KI-gestützte Berufsprüfungs-Datenextraktions-Pipeline

**Version:** 1.0
**Datum:** 2026-02-24
**Autor:** Jonathan
**Basis:** Brainstorming-Session 2026-02-24
**Status:** Entwurf

---

## 1. Projektziel & Problemstellung

### Problem

Die Berufspädagogische Überprüfung (BPÜ) erzeugt pro Prüfungsjahr bis zu 300 heterogene PDFs — eines pro Ausbildungsberuf. Diese PDFs enthalten Prüfungsstrukturen (Prüfungsbereiche, Gewichtungen, Zeitangaben, Aufgabentypen) in unterschiedlichen Tabellenformaten. Eine maschinelle Weiterverarbeitung ist ohne erheblichen manuellen Aufwand nicht möglich.

### Lösung

Eine Webanwendung (Next.js + Python FastAPI), die PDFs vollautomatisch in ein einheitliches JSON-Schema extrahiert — mit einem einmaligen, menschlich verifizierten KI-Konfigurationsschritt je Layout-Typ. Ab dem zweiten Jahreslauf läuft die Pipeline vollständig regelbasiert ohne LLM-Beteiligung.

### Erfolgskriterium

- Alle PDFs eines Jahrgangs werden ohne manuelle Dateneingabe in valides JSON überführt.
- Jede Extraktion ist rückverfolgbar und auditierbar.
- Der manuelle Aufwand skaliert mit der Anzahl der **Layout-Typen** (erwartet: 5–15), nicht mit der Anzahl der **Berufe** (bis zu 300).

---

## 2. Zielgruppen & Nutzer

| Nutzer | Rolle | Hauptbedürfnis |
|--------|-------|----------------|
| Fachexperte BPÜ | Datenanwender | Strukturierte, verlässliche Prüfungsdaten ohne manuelle Eingabe |
| Datenkoordinator | Pipeline-Betreiber | Übersicht über Verarbeitungsstatus, Fehler, Konfig-Bibliothek |
| Prüfer / Auditor | Qualitätssicherung | Audit-Trail und Nachvollziehbarkeit jedes Extraktionslaufs |

---

## 3. Funktionale Anforderungen

### 3.1 Ordner-basierter Pipeline-Trigger

- **F-01:** Die Anwendung überwacht einen konfigurierbaren Eingangsordner.
- **F-02:** Der Verarbeitungslauf wird manuell per UI-Button oder CLI-Befehl gestartet (`python run_pipeline.py --input ./eingang`).
- **F-03:** Unterordnerpfade kodieren Metadaten: `/eingang/{jahr}/{beruf}/` — Beruf und Jahr werden automatisch aus dem Pfad abgeleitet.
- **F-04:** Erfolgreich verarbeitete PDFs werden in einen `/archiv/`-Ordner verschoben (unveränderlich, nur lesend).
- **F-05:** Nicht verarbeitbare PDFs landen automatisch im `/fehler/`-Ordner — kein Datenverlust, keine Blockierung der Pipeline.

### 3.2 PDF-Parsing (Python-Service)

- **F-06:** Tabellenextraktion mit `pdfplumber` (primär) oder `Camelot` (Fallback) — ausschließlich deterministisch, kein LLM im Parsing-Schritt.
- **F-07:** Mehrtabellen-Erkennung pro Seite via Bounding-Box-Analyse (Y-Koordinaten): bis zu 2 Tabellen pro Seite werden korrekt erkannt und getrennt verarbeitet.
- **F-08:** Rohdaten-Extraktion ist reproduzierbar und versioniert (gleiche PDF → gleicher Rohtext).

### 3.3 Layout-Typ-Erkennung & Konfig-Bibliothek

- **F-09:** Bei unbekanntem PDF-Layout startet der KI-Konfigurationsschritt: das LLM analysiert die Tabellenstruktur und generiert eine Mapping-Konfig (YAML).
- **F-10:** Die generierte Konfig beschreibt das Mapping vollständig: Prüfungstyp, Spalten-Semantik, Transponierungsregeln, Gewichtungsebenen.
- **F-11:** Jeder Beruf erhält eine eigene Konfig-Datei (`{beruf}.yaml`) in der Konfig-Bibliothek.
- **F-12:** Bei bekanntem Layout-Typ (bestehende Konfig vorhanden) läuft die Verarbeitung vollständig regelbasiert — kein LLM-Aufruf.
- **F-13:** Die KI gibt zu jeder generierten Konfig einen **Konfidenz-Score + Begründung** aus. Unter dem Schwellwert (Standard: 85%) wird der Beruf automatisch zur manuellen Review markiert.

### 3.4 Format-Clustering für Skalierung

- **F-14:** Vor der Konfig-Generierung clustert die KI alle unbekannten PDFs nach Struktur-Ähnlichkeit (Layout-Typ-Bibliothek).
- **F-15:** Pro Layout-Typ wird nur ein repräsentatives Sample (3 Berufe) manuell validiert. Alle anderen Berufe des gleichen Typs erben die Validierung.
- **F-16:** Unbekannte Layout-Typen werden automatisch isoliert und zur manuellen Klassifikation markiert.

### 3.5 Verifikations-UX (Result-First Dual-View)

- **F-17:** Nach der Konfig-Generierung zeigt die Anwendung einen **Dry-Run Preview**:
  - Primäransicht: extrahierte Daten als strukturierte Tabelle / JSON-Vorschau
  - Sekundäransicht: zugrundeliegende YAML-Konfig (aufklappbar oder parallel)
- **F-18:** Der Nutzer kann die Konfig direkt im UI bearbeiten und den Dry-Run sofort neu starten.
- **F-19:** Erst nach expliziter Nutzer-Bestätigung wird die Konfig in die Bibliothek übernommen und der Beruf vollständig verarbeitet.

### 3.6 Ziel-Schema (JSON-Output)

- **F-20:** Das JSON-Schema ist für alle Berufe identisch — strukturelle Unterschiede werden durch `null`-Werte und Arrays abgebildet, nicht durch Schema-Varianten.
- **F-21:** `berufNr` ist immer ein Array (auch bei Einzelnummer).
- **F-22:** `prüfungsTyp`-Feld ist Pflicht — steuert die Konfig-Auswahl und trägt semantische Information.
- **F-23:** Gewichtungs-Struktur: bis zu 4 Ebenen (`imPrüfungsbereich`, `schriftlichePrüfung`, `teil2`, `gesamtergebnis`) — nicht vorhandene Ebenen = `null`.
- **F-24:** Praktische Prüfungs-Varianten (ODER-Verknüpfung) werden als `varianten[]`-Array vollständig gespeichert.
- **F-25:** Sub-Aufgaben pro Prüfungsbereich werden als `aufgaben[]`-Array abgebildet.

### 3.7 Validierungs-Gates

- **F-26 (V1 — Pflicht):** JSON-Schema-Gate: Strukturvalidierung vor dem Speichern. Pflichtfelder vorhanden, Datentypen korrekt, Arrays nicht leer. Fehler → `/fehler/`, kein Output.
- **F-27 (V2 — Pflicht):** Numerische Konsistenz: Gewichtungen summieren auf 100% (±1% Toleranz), Zeitangaben > 0 und < 24h, BerufNr numerisch und positiv.
- **F-28 (V3 — Optional):** LLM-Rückverifikation: Original-PDF-Rohtext + extrahiertes JSON als Input, gezielter Diff-Prompt ("Findest du im JSON einen Wert, der im PDF nicht vorkommt?").
- **F-29 (V4 — Optional):** Diff-Report als Audit-Trail: `validation-report-{beruf}-{datum}.json` wird neben dem JSON gespeichert.

### 3.8 Frontend & Verwaltung (Next.js)

- **F-30:** Dashboard: Übersicht aller Berufe mit Status (verarbeitet, fehlerhaft, ausstehend, zur Review).
- **F-31:** Konfig-Bibliothek: Liste aller bekannten Layout-Typen und Berufs-Konfigs, editierbar.
- **F-32:** JSON-Anzeige: strukturierte Darstellung des extrahierten JSONs pro Beruf.
- **F-33:** HTML-Export: formatierter Export der Prüfungsstruktur als druckbare HTML-Seite.
- **F-34:** Fehler-Log: Liste aller fehlerhaften Berufe mit Fehlergrund, Download der Original-PDFs aus `/fehler/`.

---

## 4. Nicht-funktionale Anforderungen

| Anforderung | Ziel |
|-------------|------|
| **Korrektheit** | Zero-Tolerance bei Struktur-Fehlern (V1+V2 sind blocking Gates) |
| **Reproduzierbarkeit** | Gleiche PDF + gleiche Konfig → identisches JSON (keine LLM-Nondeterminismus im kritischen Pfad) |
| **Nachvollziehbarkeit** | Jeder Lauf ist auditierbar (Validation-Report, Konfig-Version, Timestamp) |
| **Skalierbarkeit** | Skaliert mit Layout-Typen (~5–15), nicht mit Berufen (~300) |
| **Performance** | Verarbeitung von 300 PDFs in einem Batchlauf < 30 Minuten (ohne LLM-Schritt) |
| **Verfügbarkeit** | Lokale Anwendung (kein SaaS), Deployment auf einzelnem Rechner oder Server |

---

## 5. Tech-Stack

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| **Frontend** | Next.js (React) | Vollwertiges Frontend, API-Orchestrierung, JSON-Verwaltung, HTML-Export |
| **Backend / Parsing** | Python (FastAPI) | pdfplumber für Bounding-Box-basierte Mehrtabellen-Erkennung — kein JS-Äquivalent |
| **PDF-Extraktion** | pdfplumber (primär), Camelot (Fallback) | Deterministisch, reproduzierbar, liefert Koordinaten |
| **Konfig-Format** | YAML | Menschenlesbar, editierbar, versionierbar mit Git |
| **Output-Format** | JSON | Einheitliches Schema, downstream-nutzbar |
| **LLM** | Claude API (Sonnet) | Konfig-Generierung und optionale V3-Rückverifikation |
| **Kommunikation** | Next.js API Routes → FastAPI per HTTP | Klare Trennung: Python = Datenqualität, Next.js = Nutzererlebnis |

---

## 6. Architektur-Übersicht

```
/eingang/{jahr}/{beruf}/
        │
        ▼
┌─────────────────────────────────────┐
│  Next.js Frontend                   │
│  - Dashboard                        │
│  - Verifikations-UX (Dual-View)     │
│  - Konfig-Bibliothek                │
│  - JSON-Anzeige & HTML-Export       │
└──────────────┬──────────────────────┘
               │ API Route (HTTP)
               ▼
┌─────────────────────────────────────┐
│  Python FastAPI Service             │
│  1. PDF-Parsing (pdfplumber)        │
│  2. Layout-Typ-Erkennung            │
│  3. Konfig-Lookup / KI-Generierung  │
│  4. JSON-Erzeugung                  │
│  5. V1+V2 Validierung               │
└──────────────┬──────────────────────┘
               │
       ┌───────┴──────────┐
       ▼                  ▼
/ausgabe/{beruf}.json   /fehler/   /archiv/
/konfig/{beruf}.yaml
/reports/validation-report-{beruf}.json
```

---

## 7. Ordnerstruktur (Output)

```
/data/
  eingang/          # Eingangs-PDFs (nach Verarbeitung leer)
    {jahr}/
      {beruf}/
  archiv/           # Verarbeitete Original-PDFs (read-only)
  fehler/           # Fehlerhafte PDFs mit Fehlerlog
  ausgabe/          # Extrahierte JSON-Dateien
    {beruf}.json
  konfig/           # Konfig-Bibliothek
    {beruf}.yaml
  reports/          # Validierungs-Audit-Trail
    validation-report-{beruf}-{datum}.json
```

---

## 8. User Journeys

### Journey 1 — Neues PDF, bekannter Layout-Typ (Normalfall ab Jahr 2)

1. Nutzer legt PDFs in `/eingang/2027/elektrotechnik/` ab.
2. Nutzer startet Pipeline per UI-Button.
3. System erkennt Layout-Typ, lädt bestehende Konfig — kein LLM-Aufruf.
4. JSON wird erzeugt, V1+V2 bestanden → gespeichert in `/ausgabe/`.
5. PDF → `/archiv/`, Dashboard zeigt "Verarbeitet ✓".

### Journey 2 — Neues PDF, unbekannter Layout-Typ (Erstlauf)

1. Nutzer legt neues PDF ab, startet Pipeline.
2. System erkennt: kein passender Layout-Typ → startet KI-Konfigurationsschritt.
3. KI generiert YAML-Konfig mit Konfidenz-Score (z. B. 91%).
4. System führt Dry-Run durch → zeigt Result-First Dual-View.
5. Nutzer prüft Ergebnis (primär) und Konfig (sekundär), bestätigt oder korrigiert.
6. Konfig wird gespeichert, Beruf vollständig verarbeitet.

### Journey 3 — Niedriger Konfidenz-Score (< 85%)

1. KI generiert Konfig mit Score 72% und Begründung: "Spalte 3 unklar — Gewichtung oder Punktzahl?"
2. Dashboard markiert Beruf als "Zur manuellen Review".
3. Nutzer öffnet Dual-View, sieht Hinweis, korrigiert Konfig, bestätigt.
4. Pipeline setzt fort.

### Journey 4 — Validierungsfehler (V1 oder V2)

1. Extraktion läuft, V2-Check schlägt an: Gewichtungen summieren auf 98% (unter Toleranz).
2. Beruf landet in `/fehler/` mit Fehlerbericht.
3. Dashboard zeigt Fehler mit Grund, Download-Link zur Original-PDF.
4. Nutzer analysiert, korrigiert ggf. Konfig, startet Einzellauf.

---

## 9. Out-of-Scope (Version 1.0)

- Verarbeitung von Scan-PDFs (OCR) — alle PDFs sind Text-PDFs.
- Echtzeit-Dateiüberwachung (Watcher) — bewusstes Over-Engineering für seltenen Batch-Prozess.
- Multi-User-Betrieb / Authentifizierung.
- Automatischer Deployment-Prozess / CI-CD-Pipeline.
- Direkte Datenbankanbindung — JSON-Dateien als primäres Output-Format.
- API-Anbindung an externe Systeme (Downstream-Integration ist Folge-Scope).

---

## 10. Offene Punkte & Risiken

| Punkt | Risiko | Mitigation |
|-------|--------|------------|
| Heterogenität der PDFs höher als erwartet | Mehr als 15 Layout-Typen | Format-Clustering priorisieren, früh Stichprobe von 20+ PDFs analysieren |
| LLM-Konfig-Qualität | Falsch generierte Konfig unbemerkt | Result-First Dual-View ist Pflicht-Gate — kein Bypass |
| Camelot-Installation | Betriebssystem-Abhängigkeiten (Ghostscript) | pdfplumber als primäres Tool, Camelot als dokumentierter Fallback |
| Schema-Änderungen zwischen Jahrgängen | Neue Prüfungsformen, die Schema brechen | Schema-Versionierung von Anfang an vorsehen (v1.0, v2.0) |

---

## 11. Meilensteine (Hackathon)

| # | Meilenstein | Inhalt |
|---|-------------|--------|
| M1 | Basis-Pipeline | Python FastAPI mit pdfplumber, Rohdaten-Extraktion, V1+V2-Validierung |
| M2 | KI-Konfig | LLM-Konfigurationsschritt, Konfig-Bibliothek, Konfidenz-Scoring |
| M3 | Frontend | Next.js Dashboard, Dual-View Verifikations-UX, JSON-Anzeige |
| M4 | Integration | Next.js ↔ FastAPI Verbindung, vollständiger End-to-End-Lauf |
| M5 | Polish | HTML-Export, Fehler-Log, Audit-Trail, Demo-Vorbereitung |
