# Backlog M5 — Polish (Skalierung, Export, Audit)

**Meilenstein:** M5 — Format-Clustering, HTML-Export, Audit-Trail, Demo-Vorbereitung
**Release:** Polish
**Datum:** 2026-02-24
**Voraussetzung:** M1–M4 abgeschlossen (vollständige Pipeline + UI lauffähig)
**Ziel:** System ist produktionsreif für 300 Berufe. Manuelle Prüfaufwand skaliert mit Layout-Typen statt mit Berufen. Audit-Trail vollständig. HTML-Export nutzbar. Demo-bereit.

---

## Definition of Done (M5)

- [ ] Format-Clustering gruppiert unbekannte PDFs automatisch nach Struktur-Ähnlichkeit
- [ ] Sample-Validation: Bestätigung eines Layout-Typ-Samples überträgt sich auf alle Berufe desselben Typs
- [ ] Unbekannte Layout-Typen werden automatisch isoliert und markiert
- [ ] HTML-Export erzeugt druckoptimierte Seite pro Beruf
- [ ] Audit-Trail (Validation-Report) ist im Browser abrufbar
- [ ] System ist mit 10 Test-PDFs aus mindestens 2 Layout-Typen demonstrierbar

---

## Epics

| Epic | Beschreibung | Stories |
|------|-------------|---------|
| E20 | Format-Clustering | M5-01 bis M5-04 |
| E21 | HTML-Export | M5-05 bis M5-06 |
| E22 | Audit-Trail & Validation-Report | M5-07 bis M5-08 |
| E23 | Demo-Vorbereitung | M5-09 bis M5-10 |

---

## E20 — Format-Clustering

---

### M5-01 · Strukturmerkmale pro PDF extrahieren (Clustering-Features)

**Als** Entwickler
**möchte ich** aus jedem PDF einen Feature-Vektor ableiten,
**damit** Cluster-Algorithmen PDFs nach struktureller Ähnlichkeit gruppieren können.

**Akzeptanzkriterien:**
- [ ] Pro PDF werden folgende Merkmale extrahiert: Anzahl Seiten, Anzahl Tabellen gesamt, Tabellen pro Seite (min/max/avg), Anzahl Spalten pro Tabelle (min/max), Vorhandensein von Schlüsselwörtern ("Gewichtung", "Teil 2", "Abschlussprüfung", "Prüfungsstück")
- [ ] Feature-Vektor wird als `{beruf}.features.json` in `/konfig/clustering/` gespeichert
- [ ] Extraktion läuft automatisch als Teil des Pipeline-Laufs für unbekannte Berufe (vor KI-Konfig-Schritt)
- [ ] Feature-Extraktion ist deterministisch: gleiches PDF → gleicher Vektor

**Feature-Vektor (Referenz):**
```json
{
  "beruf": "elektrotechnik",
  "seitenanzahl": 2,
  "tabellenGesamt": 3,
  "tabellenProSeite": {"min": 1, "max": 2, "avg": 1.5},
  "spaltenProTabelle": {"min": 3, "max": 5},
  "schluesselwoerter": ["Abschlussprüfung", "Gewichtung", "Teil 2"],
  "hatVarianten": false,
  "gewichtungsEbenen": 4
}
```

**Priorität:** Must Have | **Aufwand:** M

---

### M5-02 · Unbekannte PDFs nach Layout-Ähnlichkeit clustern

**Als** Datenkoordinator
**möchte ich**, dass vor der KI-Konfig-Generierung alle unbekannten PDFs automatisch nach struktureller Ähnlichkeit gruppiert werden,
**damit** pro Layout-Typ nur ein KI-Aufruf statt ein Aufruf pro Beruf nötig ist.

**Akzeptanzkriterien:**
- [ ] Clustering-Algorithmus: regelbasiertes Merkmals-Matching (kein ML, für Reproduzierbarkeit); zwei PDFs gelten als ähnlich wenn ≥ 4 von 5 Merkmalen übereinstimmen
- [ ] Clustering läuft vor dem KI-Schritt über alle neuen, konfig-losen PDFs
- [ ] Ergebnis: Liste von Clustern mit je einem designierten Repräsentanten-PDF
- [ ] CLI-Ausgabe: "Clustering: 15 neue Berufe → 3 Layout-Typen erkannt (Cluster A: 8, B: 5, C: 2)"
- [ ] Clustering-Ergebnis wird in `/konfig/clustering/cluster-{datum}.json` gespeichert
- [ ] Nur für den Repräsentanten eines Clusters wird KI-Konfig generiert; alle anderen warten

**Clustering-Ergebnis (Referenz):**
```json
{
  "datum": "2026-02-24T15:00:00Z",
  "cluster": [
    {
      "id": "cluster-A",
      "repraesentant": "anlagenmechaniker",
      "mitglieder": ["industriemechaniker", "konstruktionsmechaniker", "zerspanungsmechaniker"],
      "aehnlichkeit": 0.92
    },
    {
      "id": "cluster-B",
      "repraesentant": "elektroanlagenmonteur",
      "mitglieder": ["elektroniker-energie", "elektroniker-automatisierung"],
      "aehnlichkeit": 0.88
    }
  ]
}
```

**Priorität:** Must Have | **Aufwand:** L

---

### M5-03 · Sample-Validation: bestätigte Konfig auf Cluster-Mitglieder übertragen

**Als** Datenkoordinator
**möchte ich**, dass nach Bestätigung der Konfig für den Cluster-Repräsentanten alle anderen Cluster-Mitglieder automatisch mit derselben Konfig verarbeitet werden,
**damit** der manuelle Prüfaufwand mit Layout-Typen skaliert, nicht mit Berufen.

**Akzeptanzkriterien:**
- [ ] Dual-View zeigt Hinweis: "Diese Konfig gilt nach Bestätigung für: [Liste der Cluster-Mitglieder]"
- [ ] Nach Bestätigung der Repräsentanten-Konfig: automatischer Batch-Lauf für alle Cluster-Mitglieder
- [ ] Jedes Cluster-Mitglied erhält eigene Konfig-Datei (Kopie mit angepasstem `beruf`-Feld)
- [ ] Cluster-Mitglieder werden mit `erstelltDurch: "cluster-erbschaft"` und Verweis auf Repräsentanten gespeichert
- [ ] Schlägt die Verarbeitung für ein Mitglied an (V1/V2-Fehler) → nur dieses Mitglied → `/fehler/`; andere werden trotzdem verarbeitet
- [ ] Dashboard zeigt nach Batch-Lauf: "Cluster A: 7/8 verarbeitet ✓ | 1 fehlerhaft ✗"

**Priorität:** Must Have | **Aufwand:** M

---

### M5-04 · Unbekannte Layout-Typen isolieren und markieren

**Als** Datenkoordinator
**möchte ich**, dass PDFs, die keinem bekannten Cluster zugeordnet werden können, automatisch isoliert werden,
**damit** neue Formate nicht unbemerkt mit falscher Konfig verarbeitet werden.

**Akzeptanzkriterien:**
- [ ] PDF ohne Cluster-Match → Status `NEUER_LAYOUT_TYP`, in separater Sektion im Dashboard
- [ ] Kein automatisches Clustering, kein KI-Aufruf; Beruf wartet auf manuelle Klassifikation
- [ ] Dashboard-Sektion "Neue Layout-Typen (N)": zeigt Beruf, Feature-Vektor-Zusammenfassung, "Cluster zuweisen"-Button
- [ ] "Cluster zuweisen"-Button: Dropdown mit bestehenden Clustern + "Neuen Cluster anlegen"
- [ ] "Neuen Cluster anlegen": startet Standard-KI-Konfig-Generierung (M2-Flow) für diesen Beruf als neuen Repräsentanten

**Priorität:** Must Have | **Aufwand:** M

---

## E21 — HTML-Export

---

### M5-05 · HTML-Export einer Prüfungsstruktur erzeugen

**Als** Fachexperte BPÜ
**möchte ich** die Prüfungsstruktur eines Berufs als formatierten HTML-Export herunterladen können,
**damit** ich sie in Präsentationen, Berichte oder E-Mails einbetten kann.

**Akzeptanzkriterien:**
- [ ] "HTML exportieren"-Button in Beruf-Einzelansicht (`/berufe/{beruf}`)
- [ ] HTML enthält: Berufname, BerufNr, Prüfungstyp, alle Prüfungsbereiche mit Aufgaben und Gewichtungen
- [ ] Tabellendarstellung mit CSS (kein externes Framework, inline-Styles für E-Mail-Kompatibilität)
- [ ] Druck-optimiert: `@media print`-CSS, Seitenumbrüche an sinnvollen Stellen
- [ ] Dateiname: `pruefungsstruktur-{beruf}-{jahr}.html`
- [ ] `GET /api/berufe/{beruf}/export/html` — FastAPI generiert und streamt die HTML-Datei

**HTML-Template-Struktur (Referenz):**
```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Prüfungsstruktur: {Berufname} {Jahr}</title>
  <style>
    /* Druck-optimiert, keine externen Abhängigkeiten */
    body { font-family: Arial, sans-serif; font-size: 11pt; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ccc; padding: 4px 8px; }
    .praktisch { background: #f0f7f0; }
    .schriftlich { background: #f0f0f7; }
    @media print { .no-print { display: none; } }
  </style>
</head>
<body>
  <h1>{Berufname}</h1>
  <p>BerufNr: {berufNr} | Prüfungstyp: {prüfungsTyp} | Stand: {jahr}</p>
  <!-- Prüfungsbereiche als Tabellen -->
</body>
</html>
```

**Priorität:** Must Have | **Aufwand:** M

---

### M5-06 · Batch-HTML-Export für alle Berufe eines Jahrgangs

**Als** Fachexperte BPÜ
**möchte ich** alle Berufe eines Jahrgangs auf einmal als HTML-Paket exportieren können,
**damit** ich eine komplette Übersicht für einen Jahrgang erstellen kann.

**Akzeptanzkriterien:**
- [ ] Dashboard: "Alle exportieren"-Button → ZIP-Download mit allen HTML-Dateien des aktuellen Jahrgangs
- [ ] ZIP-Datei: `pruefungsstrukturen-{jahr}.zip` mit Dateien `{beruf}.html` darin
- [ ] Index-Datei `index.html` im ZIP: Liste aller Berufe mit Links zu den Einzeldateien
- [ ] Fortschritts-Indikator während ZIP-Generierung (für große Jahrgänge mit 300 Berufen)
- [ ] `POST /api/export/html-batch?jahr={jahr}` — asynchrone Generierung, Download-Link per Polling

**Priorität:** Could Have | **Aufwand:** M

---

## E22 — Audit-Trail & Validation-Report

---

### M5-07 · Validation-Report im Browser anzeigen

**Als** Auditor
**möchte ich** den Validierungs-Report eines Extraktionslaufs direkt im Browser einsehen können,
**damit** ich die Korrektheit eines Laufs ohne Dateisystem-Zugriff belegen kann.

**Akzeptanzkriterien:**
- [ ] Beruf-Einzelansicht (`/berufe/{beruf}`) enthält Tab "Audit-Trail"
- [ ] Tab zeigt letzten Validation-Report: Zeitstempel, V1-Ergebnis, V2-Ergebnis, Konfig-Version, Score
- [ ] Vergangene Reports (bei mehreren Läufen) als aufklappbare Liste (neuester zuerst)
- [ ] "Report herunterladen"-Button: Download der `validation-report-{beruf}-{datum}.json`-Datei
- [ ] V3-Report (falls aktiviert): separate Sektion "LLM-Rückverifikation" mit Ergebnis und verwendetem Prompt

**Report-Anzeige (Referenz):**
```
Audit-Trail: anlagenmechaniker
─────────────────────────────────────────────────────
Lauf: 2026-02-24 15:00:00   Konfig: v1.0   Score: —
  V1 Schema-Gate      ✓ bestanden
  V2 Konsistenz       ✓ bestanden  (Gewichtungen: 40+60=100% ✓, 50+50=100% ✓)
  V3 LLM-Verifikation ○ nicht aktiviert
  Quelldatei: pruefung.pdf (archiviert)
  Dauer: 1.2s
```

**Priorität:** Must Have | **Aufwand:** S

---

### M5-08 · V3 LLM-Rückverifikation aktivieren und ausführen

**Als** Auditor
**möchte ich** für ausgewählte Berufe optional eine LLM-Rückverifikation aktivieren können,
**damit** bei kritischen Berufen eine zusätzliche Qualitätssicherungsschicht verfügbar ist.

**Akzeptanzkriterien:**
- [ ] V3 aktivierbar per Konfig (`v3_aktiviert: true` in `config.yaml`) oder per UI-Toggle in der Beruf-Einzelansicht
- [ ] V3-Prompt: Original-PDF-Rohtext + extrahiertes JSON + Targeted-Diff-Prompt ("Findest du im JSON einen Wert, der im PDF nicht vorkommt?")
- [ ] V3-Ergebnis: `{"befund": "kein_widerspruch" | "widerspruch_gefunden", "details": "..."}` im Report
- [ ] V3-Fehler → Warnung im Audit-Trail (kein blockierendes Gate, nur dokumentiert)
- [ ] V3-Kosten werden pro Lauf geloggt (Tokens verbraucht)

**Priorität:** Could Have | **Aufwand:** M

---

## E23 — Demo-Vorbereitung

---

### M5-09 · Demo-Datensatz: 10 Test-PDFs aus 2 Layout-Typen vorbereiten

**Als** Entwickler
**möchte ich** einen vollständigen Demo-Datensatz aus realen PDFs,
**damit** der Hackathon-Demo alle Pipeline-Pfade zeigen kann.

**Akzeptanzkriterien:**
- [ ] 10 PDFs ausgewählt: 5x Layout-Typ A (z. B. Anlagenmechaniker-Familie), 5x Layout-Typ B (z. B. Elektroanlagenmonteur-Familie)
- [ ] 2 PDFs bewusst fehlerhaft (leere Tabelle, falsche Gewichtungssumme) für Fehler-Demonstrations-Pfad
- [ ] 1 PDF von komplett neuem Layout-Typ für Clustering-Demo
- [ ] Demo-Skript (`demo/README.md`) dokumentiert die Reihenfolge der Schritte für eine 5-Minuten-Demo
- [ ] Reset-Skript (`demo/reset.sh`) löscht alle Ausgabe-Dateien und stellt Eingangs-PDFs wieder her

**Demo-Reihenfolge (Referenz):**
```
1. Reset → sauberer Ausgangszustand
2. Pipeline starten → bekannte Berufe (Typ A+B) laufen durch (M1-Flow)
3. Fehlerhafte PDFs zeigen (Fehler-Liste im Browser)
4. Neuen Beruf einschleusen → KI-Konfig-Generierung (M2-Flow)
5. Dual-View öffnen → Konfig prüfen, editieren, Dry-Run (M4-Flow)
6. Bestätigen → JSON erzeugt
7. HTML-Export zeigen
8. Audit-Trail aufrufen
```

**Priorität:** Must Have | **Aufwand:** S

---

### M5-10 · Performance-Test: 50 PDFs Batch-Lauf

**Als** Datenkoordinator
**möchte ich** sicherstellen, dass die Pipeline mit 50 PDFs (Teilmenge des Jahrgangs) in akzeptabler Zeit läuft,
**damit** ein realistischer Einsatz mit 300 Berufen planbar ist.

**Akzeptanzkriterien:**
- [ ] Batch-Lauf mit 50 bekannten PDFs (alle Konfigs vorhanden) in < 5 Minuten
- [ ] Kein Memory-Leak: RSS-Speicher nach dem Lauf < 500 MB
- [ ] Parallelisierung: PDFs werden in Batches von 5 parallel verarbeitet (konfigurierbar)
- [ ] Hochrechnung auf 300 PDFs wird dokumentiert: "50 PDFs in X Minuten → 300 PDFs ≈ X * 6 Minuten"
- [ ] Ergebnis im Demo-Skript festgehalten

**Technische Notizen:**
```python
# pipeline.py — Parallelisierung
import asyncio
from asyncio import Semaphore

async def run_pipeline_batch(pdf_paths: list[Path], parallel: int = 5):
    sem = Semaphore(parallel)
    async def process_one(path):
        async with sem:
            return await asyncio.to_thread(process_pdf, path)
    return await asyncio.gather(*[process_one(p) for p in pdf_paths])
```

**Priorität:** Should Have | **Aufwand:** M

---

## Story-Übersicht M5

| ID | Titel | Epic | Priorität | Aufwand | PRD-Ref |
|----|-------|------|-----------|---------|---------|
| M5-01 | Strukturmerkmale pro PDF extrahieren | E20 | Must Have | M | F-14 |
| M5-02 | Unbekannte PDFs nach Ähnlichkeit clustern | E20 | Must Have | L | F-14 |
| M5-03 | Sample-Validation auf Cluster-Mitglieder übertragen | E20 | Must Have | M | F-15 |
| M5-04 | Unbekannte Layout-Typen isolieren | E20 | Must Have | M | F-16 |
| M5-05 | HTML-Export einzelner Beruf | E21 | Must Have | M | F-33 |
| M5-06 | Batch-HTML-Export als ZIP | E21 | Could Have | M | F-33 |
| M5-07 | Validation-Report im Browser | E22 | Must Have | S | F-29 |
| M5-08 | V3 LLM-Rückverifikation | E22 | Could Have | M | F-28 |
| M5-09 | Demo-Datensatz vorbereiten | E23 | Must Have | S | — |
| M5-10 | Performance-Test: 50 PDFs | E23 | Should Have | M | — |

**Gesamtaufwand M5:** 6 Must Have + 1 Should Have + 3 Could Have Stories

---

## Empfohlene Implementierungsreihenfolge

```
Phase 1 — Clustering-Fundament (E20)
  M5-01 → M5-02 → M5-03 → M5-04   ← Feature-Extraktion zuerst, dann Cluster-Logik

Phase 2 — Export (E21)
  M5-05 → [M5-06 optional]   ← Einzel-Export vor Batch

Phase 3 — Audit (E22)
  M5-07 → [M5-08 optional]   ← Report-Anzeige vor V3

Phase 4 — Demo (E23)
  M5-09 → M5-10   ← Demo-Daten zuerst, dann Performance
```

---

## Test-Szenarien M5

| Szenario | Erwartetes Ergebnis |
|----------|---------------------|
| 8 PDFs mit 2 Layout-Typen als Batch | 2 Cluster erkannt, je 1 KI-Aufruf |
| Cluster-Repräsentant bestätigen | 7 weitere Berufe automatisch verarbeitet |
| 1 Cluster-Mitglied hat V2-Fehler | Nur dieses in /fehler/, andere verarbeitet |
| PDF ohne Cluster-Match | Status NEUER_LAYOUT_TYP, Dashboard-Sektion |
| HTML-Export für Anlagenmechaniker | Valides HTML, druckbar, alle Felder vorhanden |
| Audit-Trail für verarbeiteten Beruf | V1+V2-Ergebnis sichtbar, Download funktioniert |
| 50-PDF Performance-Test | < 5 Minuten, kein Memory-Leak |
| Demo-Reset-Skript | Sauberer Ausgangszustand, alle PDFs wieder in /eingang/ |
