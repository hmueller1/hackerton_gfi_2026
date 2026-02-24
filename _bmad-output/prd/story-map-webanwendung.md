# Story Map — KI-gestützte Berufsprüfungs-Datenextraktions-Pipeline

**Version:** 1.0
**Datum:** 2026-02-24
**Basis:** PRD v1.0 (`prd-webanwendung.md`)
**Releases:** MVP → Vollständig → Polish

---

## Legende

```
AKTIVITÄT       → Übergeordnetes Nutzerziel (horizontal, Backbone)
  └─ Aufgabe    → Konkrete Nutzerhandlung (Walking Skeleton)
       Story    → Implementierbare User Story (nach Release geordnet)
```

**Nutzer-Kürzel:** `[DK]` Datenkoordinator · `[FE]` Fachexperte BPÜ · `[AU]` Auditor

---

## Backbone (Aktivitäten)

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ A1               │ A2               │ A3               │ A4               │ A5               │ A6               │
│ PIPELINE         │ PDFs EINLESEN    │ KONFIG           │ ERGEBNISSE       │ FEHLER           │ DATEN NUTZEN     │
│ EINRICHTEN       │ & VERARBEITEN    │ VERIFIZIEREN     │ VERWALTEN        │ BEHEBEN          │ & EXPORTIEREN    │
└──────────────────┴──────────────────┴──────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## Walking Skeleton (Kern-Aufgaben je Aktivität)

| A1 — Pipeline einrichten | A2 — PDFs einlesen | A3 — Konfig verifizieren | A4 — Ergebnisse verwalten | A5 — Fehler beheben | A6 — Daten nutzen |
|---|---|---|---|---|---|
| Ordnerstruktur anlegen | Batch-Lauf starten | KI-Konfig prüfen | Dashboard einsehen | Fehler-PDFs sichten | JSON abrufen |
| Eingangsordner konfigurieren | PDFs parsen & extrahieren | Dry-Run validieren | JSON-Daten ansehen | Einzellauf wiederholen | HTML exportieren |
| Konfig-Bibliothek verwalten | Layout-Typ erkennen | Konfig freigeben | Konfig-Bibliothek pflegen | Konfig korrigieren | Audit-Trail lesen |

---

## Release 1 — MVP (Basis-Pipeline lauffähig)

> **Ziel:** End-to-End-Lauf möglich — PDF rein, validiertes JSON raus. Keine KI im kritischen Pfad.

### A1 — Pipeline einrichten

```
Als [DK] möchte ich die Ordnerstruktur (/eingang, /archiv, /fehler, /ausgabe) automatisch anlegen lassen,
damit ich sofort mit dem Ablegen von PDFs beginnen kann.
→ F-01 | Akzeptanz: Ordner existieren nach erstem Start, kein manuelles Anlegen nötig

Als [DK] möchte ich den Eingangsordner-Pfad konfigurieren können,
damit die Pipeline auf verschiedenen Rechnern portabel bleibt.
→ F-01 | Akzeptanz: Pfad in config.yaml oder .env setzbar

Als [DK] möchte ich Metadaten (Beruf, Jahr) aus dem Unterordnerpfad automatisch ableiten lassen,
damit ich keine separaten Metadaten-Dateien pflegen muss.
→ F-03 | Akzeptanz: /eingang/2026/elektrotechnik/ → beruf="elektrotechnik", jahr=2026
```

### A2 — PDFs einlesen & verarbeiten

```
Als [DK] möchte ich den Pipeline-Lauf per CLI-Befehl starten können,
damit ich den Verarbeitungszeitpunkt selbst kontrolliere.
→ F-02 | Akzeptanz: `python run_pipeline.py --input ./eingang` verarbeitet alle PDFs im Ordner

Als [DK] möchte ich, dass jedes PDF mit pdfplumber extrahiert wird,
damit die Rohdaten deterministisch und reproduzierbar sind.
→ F-06 | Akzeptanz: Gleiches PDF → identischer Rohtext bei jedem Lauf

Als [DK] möchte ich, dass die Mehrtabellen-Erkennung via Bounding-Box-Analyse funktioniert,
damit 1- und 2-Tabellen-Seiten korrekt unterschieden werden.
→ F-07 | Akzeptanz: Seiten mit 2 Tabellen erzeugen 2 separate Extraktionsobjekte

Als [DK] möchte ich, dass erfolgreich verarbeitete PDFs ins /archiv/ verschoben werden,
damit der Eingangsordner sauber bleibt und Originale erhalten sind.
→ F-04 | Akzeptanz: PDF im /archiv/ ist identisch mit Original (kein Modify)

Als [DK] möchte ich, dass fehlerhafte PDFs automatisch in /fehler/ wandern,
damit die Pipeline nicht blockiert und kein PDF verloren geht.
→ F-05 | Akzeptanz: Fehler-PDF + Fehlerlog-Datei im /fehler/-Ordner
```

### A4 — Ergebnisse verwalten (MVP-Minimal)

```
Als [DK] möchte ich den Verarbeitungsstatus per CLI-Ausgabe sehen,
damit ich weiß, welche PDFs erfolgreich verarbeitet wurden.
→ implizit F-02 | Akzeptanz: Pro PDF: "✓ elektrotechnik.json gespeichert" oder "✗ kaufmann-buero → /fehler/"
```

### A5 — Fehler beheben (MVP-Minimal)

```
Als [DK] möchte ich aus dem Fehlerlog den Grund für einen fehlgeschlagenen Lauf lesen können,
damit ich das Problem ohne Debugging-Kenntnisse identifizieren kann.
→ F-05, F-26, F-27 | Akzeptanz: Fehlerlog enthält: Dateiname, Fehlertyp (V1/V2/Parsing), Beschreibung

Als [DK] möchte ich ein einzelnes PDF erneut verarbeiten können,
damit ich nach einer Korrektur nicht den gesamten Batch neu starten muss.
→ F-02 | Akzeptanz: `--input ./fehler/elektrotechnik.pdf` verarbeitet nur diese Datei
```

### Validierungs-Gates (MVP — Pflicht)

```
Als [DK] möchte ich, dass jedes JSON vor dem Speichern gegen das Schema validiert wird (V1),
damit strukturell ungültige Daten nie im /ausgabe/-Ordner landen.
→ F-26 | Akzeptanz: Fehlende Pflichtfelder oder falsche Typen → /fehler/, kein JSON-Output

Als [DK] möchte ich, dass Gewichtungen automatisch auf 100% geprüft werden (V2),
damit mathematische KI-Fehler deterministisch abgefangen werden.
→ F-27 | Akzeptanz: Summe < 99% oder > 101% → V2-Fehler, Beruf → /fehler/
```

---

## Release 2 — Vollständig (KI-Konfig + Verifikations-UX + Frontend)

> **Ziel:** KI-gestützter Konfig-Schritt mit menschlicher Verifikation. Vollwertiges Next.js-Frontend.

### A1 — Pipeline einrichten

```
Als [DK] möchte ich die Pipeline per UI-Button im Browser starten können,
damit ich kein Terminal öffnen muss.
→ F-02, F-30 | Akzeptanz: Button "Pipeline starten" im Dashboard triggert den Lauf

Als [DK] möchte ich die Konfig-Bibliothek im Browser verwalten können,
damit ich bestehende Berufs-Konfigs einsehen und bearbeiten kann.
→ F-11, F-31 | Akzeptanz: Liste aller {beruf}.yaml Dateien, editierbar im Browser
```

### A2 — PDFs einlesen & verarbeiten

```
Als [DK] möchte ich, dass bekannte Layout-Typen ohne LLM-Aufruf verarbeitet werden,
damit der Jahres-Lauf schnell und kostenfrei läuft.
→ F-12 | Akzeptanz: Konfig vorhanden → kein API-Call, direkte Verarbeitung

Als [DK] möchte ich, dass die KI bei unbekanntem Layout automatisch eine YAML-Konfig generiert,
damit ich nicht manuell YAML schreiben muss.
→ F-09, F-10 | Akzeptanz: Konfig enthält Prüfungstyp, Spalten-Semantik, Transponierungsregeln

Als [DK] möchte ich zu jeder KI-generierten Konfig einen Konfidenz-Score mit Begründung sehen,
damit ich weiß, worauf ich meine Prüfaufmerksamkeit richten soll.
→ F-13 | Akzeptanz: Score + Text wie "Spalte 3 unklar — Gewichtung oder Punktzahl?"

Als [DK] möchte ich, dass Berufe mit Score < 85% automatisch zur manuellen Review markiert werden,
damit kein unsicherer Konfig-Vorschlag unbemerkt durchläuft.
→ F-13, F-30 | Akzeptanz: Dashboard-Status "Zur Review" für betroffene Berufe
```

### A3 — Konfig verifizieren

```
Als [DK] möchte ich einen Dry-Run-Preview sehen, bevor ich eine Konfig freigebe,
damit ich das Ergebnis beurteilen kann, ohne die Konfig zu verstehen.
→ F-17 | Akzeptanz: Primär: strukturierte Datentabelle / JSON-Vorschau; Sekundär: YAML aufklappbar

Als [DK] möchte ich die Konfig direkt im Dual-View-Editor bearbeiten und sofort neu testen,
damit Korrekturen ohne Kontextwechsel möglich sind.
→ F-18 | Akzeptanz: YAML bearbeiten → "Neu testen" → neuer Dry-Run in <5 Sekunden

Als [DK] möchte ich eine Konfig explizit bestätigen müssen, bevor sie gespeichert wird,
damit kein ungeprüfter Konfig-Vorschlag in die Bibliothek gelangt.
→ F-19 | Akzeptanz: Kein Speichern ohne expliziten "Bestätigen"-Klick; kein Bypass möglich
```

### A4 — Ergebnisse verwalten

```
Als [DK] möchte ich im Dashboard alle Berufe mit Status sehen (verarbeitet / fehlerhaft / ausstehend / zur Review),
damit ich den Gesamtfortschritt des Laufs auf einen Blick erfasse.
→ F-30 | Akzeptanz: Farbkodierte Status-Übersicht, aktualisiert nach jedem Beruf

Als [FE] möchte ich das extrahierte JSON eines Berufs im Browser strukturiert ansehen,
damit ich die Korrektheit der Daten prüfen kann.
→ F-32 | Akzeptanz: JSON als aufklappbare Baumstruktur; Rohdaten-Ansicht als Fallback

Als [DK] möchte ich alle bekannten Layout-Typen in der Konfig-Bibliothek sehen und verwalten,
damit die Wissensbasis des Systems wächst und nachvollziehbar bleibt.
→ F-31 | Akzeptanz: Liste mit Layout-Typ, zugeordnete Berufe, Konfig-Version, Datum
```

### A5 — Fehler beheben

```
Als [DK] möchte ich im Browser eine Liste aller fehlerhaften Berufe mit Fehlergrund sehen,
damit ich Fehler ohne Terminal priorisieren und bearbeiten kann.
→ F-34 | Akzeptanz: Tabelle mit Beruf, Fehlertyp (V1/V2/Parsing/KI), Zeitstempel

Als [DK] möchte ich das fehlerhafte Original-PDF direkt aus der Fehler-Liste herunterladen,
damit ich es ohne Dateisystem-Navigation öffnen kann.
→ F-34 | Akzeptanz: Download-Link pro Fehlereintrag
```

---

## Release 3 — Polish (Skalierung + Audit + Export)

> **Ziel:** Produktionsreif für 300 Berufe. Audit-Trail vollständig. HTML-Export nutzbar.

### A2 — PDFs einlesen & verarbeiten (Skalierung)

```
Als [DK] möchte ich, dass unbekannte PDFs vor der Konfig-Generierung nach Layout-Ähnlichkeit geclustert werden,
damit nicht für jeden Beruf einzeln eine KI-Konfig generiert werden muss.
→ F-14 | Akzeptanz: 300 PDFs → 5–15 Cluster; pro Cluster 1 KI-Aufruf statt 300

Als [DK] möchte ich, dass Berufe desselben Layout-Typs die validierte Konfig erben,
damit der manuelle Prüfaufwand mit Layout-Typen skaliert, nicht mit Berufen.
→ F-15 | Akzeptanz: Nach Bestätigung von 3 Sample-Berufen → alle anderen des Typs automatisch verarbeitet

Als [DK] möchte ich, dass unbekannte Layout-Typen automatisch isoliert und markiert werden,
damit neue Formate nicht unbemerkt mit falscher Konfig verarbeitet werden.
→ F-16 | Akzeptanz: Unbekannter Typ → Status "Neuer Layout-Typ erkannt", kein automatisches Matching
```

### A3 — Konfig verifizieren (Skalierung)

```
Als [DK] möchte ich bei der Sample-Validierung sehen, welche anderen Berufe denselben Layout-Typ haben,
damit ich informiert entscheide, für wen die Konfig gültig ist.
→ F-15 | Akzeptanz: Dual-View zeigt "Diese Konfig gilt für: [Liste ähnlicher Berufe]"
```

### A5 — Fehler beheben (LLM-Verifikation)

```
Als [AU] möchte ich optionale LLM-Rückverifikation aktivieren können (V3),
damit zusätzliche Sicherheit bei kritischen Berufen möglich ist.
→ F-28 | Akzeptanz: V3 aktivierbar per Konfig; Prompt: "Findest du im JSON einen Wert, der im PDF nicht vorkommt?"
```

### A6 — Daten nutzen & exportieren

```
Als [FE] möchte ich die Prüfungsstruktur eines Berufs als druckbare HTML-Seite exportieren,
damit ich sie in Präsentationen und Berichte einbetten kann.
→ F-33 | Akzeptanz: HTML-Export mit strukturierter Tabellenansicht; druckoptimiertes CSS

Als [AU] möchte ich den Validierungs-Report jedes Laufs als JSON abrufen können,
damit ich die Korrektheit eines Extraktionslaufs nachträglich belegen kann.
→ F-29 | Akzeptanz: validation-report-{beruf}-{datum}.json neben JSON-Output; abrufbar im Browser

Als [AU] möchte ich im Audit-Trail sehen, welche Konfig-Version für einen Lauf verwendet wurde,
damit ich Änderungen zwischen Jahrgängen nachvollziehen kann.
→ F-29 | Akzeptanz: Report enthält konfig-datei, konfig-version, konfidenz-score, validierungsschritte
```

---

## Story-Map-Übersicht (visuell komprimiert)

```
AKTIVITÄT  │ A1 Einrichten     │ A2 Verarbeiten    │ A3 Verifizieren   │ A4 Verwalten      │ A5 Fehler         │ A6 Exportieren
───────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────
AUFGABE    │ Ordner anlegen    │ Batch starten     │ KI-Konfig prüfen  │ Dashboard sehen   │ Fehler sichten    │ JSON abrufen
           │ Pfad konfig.      │ PDFs parsen       │ Dry-Run testen    │ JSON ansehen      │ Einzellauf retry  │ HTML exportieren
           │ Bibliothek verw.  │ Layout erkennen   │ Konfig freigeben  │ Bibliothek pflegen│ Konfig korrigieren│ Audit-Trail lesen
───────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────
RELEASE 1  │ Ordnerstruktur    │ CLI-Trigger       │ —                 │ CLI-Status        │ Fehlerlog (CLI)   │ —
  MVP      │ Pfad-Metadaten    │ pdfplumber        │                   │                   │ Einzellauf CLI    │
           │                   │ Mehrtabellen      │                   │                   │                   │
           │                   │ Archiv/Fehler     │                   │                   │                   │
           │                   │ V1+V2 Gates       │                   │                   │                   │
───────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────
RELEASE 2  │ UI-Button         │ Bekannte Konfigs  │ Dual-View Preview │ Dashboard UI      │ Fehler-Liste UI   │ —
  Vollst.  │ Konfig-UI         │ KI-Konfig-Gen.    │ Editor + Retry    │ JSON-Browser      │ PDF-Download      │
           │                   │ Konfidenz-Score   │ Bestätigen-Gate   │ Konfig-Bibliothek │                   │
───────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────┼───────────────────
RELEASE 3  │ —                 │ Format-Clustering │ Sample-Validation │ —                 │ V3 LLM-Verif.     │ HTML-Export
  Polish   │                   │ Layout-Bibliothek │ Typ-Erbschaft     │                   │                   │ Audit-Trail UI
           │                   │ Isolation neu.    │                   │                   │                   │ Validation-Report
```

---

## Story-Count je Release

| Release | Stories | Schwerpunkt |
|---------|---------|-------------|
| MVP | 10 | Basis-Pipeline: CLI, pdfplumber, V1+V2, Archiv/Fehler |
| Vollständig | 14 | KI-Konfig, Dual-View UX, Next.js-Frontend |
| Polish | 8 | Clustering, Skalierung, HTML-Export, Audit-Trail |
| **Gesamt** | **32** | |

---

## Meilenstein-Mapping (Hackathon)

| Meilenstein | Release | Stories |
|-------------|---------|---------|
| M1 — Basis-Pipeline | MVP | A1+A2 (CLI, Parsing, Validierung) |
| M2 — KI-Konfig | Vollständig | A2 (KI-Konfig-Gen., Konfidenz-Score) |
| M3 — Frontend | Vollständig | A1+A4+A5 (Dashboard, JSON-Browser, Fehler-UI) |
| M4 — Integration | Vollständig | A3 (Dual-View, Bestätigen-Gate, Next.js↔FastAPI) |
| M5 — Polish | Polish | A2 (Clustering) + A6 (Export, Audit) |
