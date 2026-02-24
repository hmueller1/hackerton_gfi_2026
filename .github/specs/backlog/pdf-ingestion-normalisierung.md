# Spec: PDF-Ingestion und Normalisierung von Prüfungsdaten

**Status:** In Progress  
**Erstellt:** 2026-02-24  
**Bereich:** `ingestion` / `normalization`  
**Referenz:** [GitHub Issue #3](https://github.com/hmueller1/hackerton_gfi_2026/issues/3)

---

## Zusammenfassung

PDF-Dateien aus einem konfigurierbaren Verzeichnis werden automatisch eingelesen, geparst und in ein definiertes JSON-Schema überführt (Normalisierung). Die normalisierten Daten bilden die Grundlage für die spätere Bereitstellung über die HTTP-REST-API.

---

## Problem / Motivation

Die IHK-Prüfungsunterlagen liegen als PDFs vor (einzelne Seiten sowie ein Gesamtdokument mit >100 Seiten). Die Struktur der Datensätze ist ähnlich, aber nicht identisch. Um die Daten maschinenlesbar und über eine API abfragbar zu machen, müssen sie in ein einheitliches JSON-Format überführt werden.

---

## Ziele

- Alle PDF-Dateien in einem angegebenen Verzeichnis werden automatisch erkannt und verarbeitet.
- Jede PDF-Datei wird in ein normalisiertes JSON-Objekt überführt, das dem definierten Schema entspricht.
- Die normalisierten Objekte werden gesammelt und für den API-Layer bereitgestellt.

## Nicht-Ziele

- Keine UI zur Anzeige der Rohdaten.
- Kein Parsing von PDFs außerhalb des IHK-Prüfungsdaten-Formats.
- Keine automatische Validierung von Prüfungsinhalten (fachliche Korrektheit).
- Kein On-Demand-Trigger über die API (Folge-Spec).

---

## Anforderungen

### Funktional

| ID | Anforderung |
|----|-------------|
| F-01 | Der Ingestion-Service akzeptiert einen Verzeichnispfad als Konfiguration (Umgebungsvariable `PDF_DIR`). |
| F-02 | Alle `.pdf`-Dateien im angegebenen Verzeichnis (nicht rekursiv) werden eingelesen; beide Quellen werden verarbeitet: Einzel-PDFs unter `./doc/berufe/pages/` **und** das Gesamtdokument `gesamt-bpue-w25-data.pdf`. |
| F-03 | Der Rohtext jeder PDF-Datei wird mittels eines externen KI-Dienstes (OpenAI-kompatibler Endpunkt, Modell `claude-sonnet-4-6*`) in ein `Beruf`-JSON-Objekt überführt. Der API-Key und die Base-URL werden über Umgebungsvariablen (`AI_HUB_API_KEY`, `AI_HUB_BASE_URL`) konfiguriert. |
| F-04 | Das extrahierte JSON-Objekt wird gegen das definierte JSON-Schema validiert. |
| F-05 | Valide Objekte werden in MongoDB persistiert (Collection `berufe`). |
| F-06 | Der Ingestion-Prozess wird automatisch **beim Serverstart** ausgeführt. |
| F-07 | Fehlerhafte oder nicht parsbare PDFs werden geloggt und übersprungen (kein Programmabbruch). |
| F-08 | Bereits verarbeitete Dokumente werden anhand des Dateinamens dedupliziert (kein Doppelimport bei Neustart). |

### Nicht-Funktional

| ID | Anforderung |
|----|-------------|
| NF-01 | Der Ingestion-Prozess ist vom HTTP-Layer entkoppelt. |
| NF-02 | Der Normalisierungs-Layer ist rein funktional (keine Seiteneffekte, keine I/O). |
| NF-03 | Der Service ist mit TypeScript Strict Mode implementiert, keine `any`-Typen. |
| NF-04 | Secrets (API-Key, MongoDB-URI) werden ausschließlich über Umgebungsvariablen bereitgestellt, nie im Code. |

---

## Datenschema

Das Zielschema entspricht dem JSON-Schema aus [Issue #3](https://github.com/hmueller1/hackerton_gfi_2026/issues/3):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Schema für pplanzentral.json",
  "type": "object",
  "properties": {
    "beruf": {
      "type": "object",
      "properties": {
        "beschreibung": { "type": "string" },
        "berufNr": {
          "type": "array",
          "items": { "type": "integer" }
        },
        "prüfungsBereich": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "aufgaben": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "name": { "type": "string" },
                    "struktur": { "type": "string" },
                    "termin": {
                      "type": "object",
                      "properties": {
                        "datum": { "type": "string", "format": "date" },
                        "uhrzeitvon": { "type": "string" },
                        "uhrzeitbis": { "type": "string" },
                        "dauer": { "type": ["integer"] }
                      },
                      "required": ["datum", "uhrzeitvon", "uhrzeitbis", "dauer"],
                      "additionalProperties": false
                    },
                    "hilfmittel": { "type": "string" }
                  },
                  "required": ["name", "struktur", "termin"],
                  "additionalProperties": false
                }
              }
            },
            "required": ["name", "aufgaben"],
            "additionalProperties": false
          }
        }
      },
      "required": ["beschreibung", "berufNr", "prüfungsBereich"],
      "additionalProperties": false
    }
  },
  "required": ["beruf"],
  "additionalProperties": false
}
```

### Beispiel-Datensatz (Rumpf)

```json
{
  "beruf": {
    "beschreibung": "Eisenbahner/-in im Betriebsdienst Lokführer/-in und Transport",
    "berufNr": [4980, 4981],
    "prüfungsBereich": [
      {
        "name": "Wirtschafts- und Sozialkunde",
        "aufgaben": [
          {
            "name": "Schriftliche Aufgabenstellungen",
            "struktur": "18 geb. Aufgaben, 3 Abwahl, á 1 Punkt = 15 Punkte dividiert durch Divisor 0,375 = 40 Punkte",
            "termin": {
              "datum": "02.12.2025",
              "uhrzeitvon": "08:00",
              "uhrzeitbis": "09:00",
              "dauer": 60
            },
            "hilfmittel": "Nicht programmierter, netzunabhängiger Taschenrechner ohne Kommunikationsmöglichkeit mit Dritten"
          }
        ]
      }
    ]
  }
}
```

---

## Akzeptanzkriterien

| ID | Kriterium |
|----|-----------|
| AC-01 | Gegeben ein Verzeichnis mit 5 validen PDF-Dateien, werden 5 Dokumente in MongoDB gespeichert. |
| AC-02 | Jedes gespeicherte Dokument besteht die JSON-Schema-Validierung ohne Fehler. |
| AC-03 | Eine nicht-parsbare PDF-Datei im Verzeichnis führt zu einem Log-Eintrag, alle anderen Dateien werden weiterhin verarbeitet. |
| AC-04 | Bei leerem Verzeichnis startet der Server ohne Fehler; MongoDB enthält keine neuen Einträge. |
| AC-05 | Nach Serverstart mit `PDF_DIR=./doc/berufe/pages` enthält MongoDB Einträge für alle verarbeitbaren Einzel-PDFs. |
| AC-06 | `gesamt-bpue-w25-data.pdf` wird ebenfalls eingelesen und in mindestens einem MongoDB-Dokument resultiert. |
| AC-07 | Beim erneuten Start werden keine Duplikate angelegt (Deduplizierung nach Dateiname). |
| AC-08 | Der Normalisierungs-Layer hat keine Abhängigkeiten zu HTTP- oder Datenbankmodulen. |
| AC-09 | Unit-Tests für den Normalisierungs-Layer decken mindestens einen validen und einen fehlerhaften PDF-Eingabefall ab. |

---

## Risiken

| Risiko | Wahrscheinlichkeit | Auswirkung | Maßnahme |
|--------|--------------------|------------|----------|
| PDFs haben stark variierende Layouts | Hoch | Hoch | KI-gestütztes Parsing mit Fallback-Strategie; Fehler-Logging |
| KI-Parsing liefert inkonsistente Feldnamen | Mittel | Mittel | Strenge Schema-Validierung nach Parsing, Felder normalisieren |
| Performance bei >100 PDFs | Mittel | Niedrig | Sequenzielles Einlesen mit Fortschrittslog; Batch-Verarbeitung als Option |
| PDF enthält nicht alle Pflichtfelder | Mittel | Mittel | Partielle Extraktion loggen, Objekt überspringen |

---

## Entschiedene Fragen

| Frage | Entscheidung |
|-------|--------------|
| KI-Dienst | Externer OpenAI-kompatibler Endpunkt: `https://adesso-ai-hub.3asabc.de/v1`, Modell `claude-sonnet-4-6*`. API-Key via `AI_HUB_API_KEY` (Env). |
| Persistenz | MongoDB (Collection `berufe`). URI via `MONGODB_URI` (Env). |
| Trigger | Beim Serverstart. On-Demand-Trigger ist geplant (Folge-Spec). |
| PDF-Quellen | Beide: Einzel-PDFs unter `./doc/berufe/pages/` **und** `gesamt-bpue-w25-data.pdf`. |

---

## Außerhalb des Scope

- HTTP-API-Endpunkte (eigene Spec).
- Authentifizierung / Autorisierung.
- Frontend / UI.
- On-Demand-Ingestion über API (Folge-Spec).
- Unterstützung anderer Dokumentformate (Word, Excel, etc.).
