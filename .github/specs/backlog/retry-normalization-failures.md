# Retry-Logik für Normalisierungsfehler

**Status:** Draft  
**Bereich:** `src/ingestion`, `src/persistence`  
**Erstellt:** 2026-02-24

---

## Zusammenfassung

PDFs, bei denen `normalize()` fehlschlägt (Rückgabe `null`), werden aktuell dauerhaft übersprungen — mit lediglich einer WARN-Meldung. Da der KI-Parser nicht deterministisch ist, könnte ein erneuter Versuch erfolgreich sein. Diese Spec beschreibt eine Retry-Logik, die gescheiterte PDFs trackt und automatisch (beim Startup) sowie manuell (per HTTP-Endpunkt) erneut verarbeitet.

---

## Problem / Motivation

In `IngestionService.onApplicationBootstrap` gibt es zwei Fehlerpfade:

1. `normalize(rawJson) === null` — Schemvalidierung schlug fehl (KI-Ausgabe ungültig).
2. Ausnahme im `try/catch` — allgemeiner Verarbeitungsfehler.

In beiden Fällen wird die Datei beim nächsten Startup übersprungen, weil `existsByFilename` nur **erfolgreich persistierte** Berufe kennt. Fehlgeschlagene PDFs sind dauerhaft verloren, solange kein manuelles Eingreifen erfolgt.

Da der KI-Parser (Claude Sonnet) bei erneutem Aufruf ein anderes, eventuell valides JSON zurückgeben kann, ist Retry sinnvoll.

---

## Ziele

- Fehlgeschlagene PDFs in MongoDB persistieren (eigene Collection: `failed_ingestions`).
- Beim Startup: Retry für alle Einträge, die `retryCount < MAX_RETRIES`.
- HTTP-Endpunkt `POST /ingestion/retry` zum manuellen Auslösen eines Retry-Laufs.
- Nach erfolgreichem Retry: Eintrag aus `failed_ingestions` entfernen, Beruf normal speichern.
- Konfigurierbare maximale Retry-Anzahl via Umgebungsvariable `INGESTION_MAX_RETRIES` (Default: 3).

## Nicht-Ziele

- Kein automatisches Polling / Cronjob (kein Scheduling-Modul).
- Keine Unterscheidung zwischen verschiedenen Fehlerursachen beim Retry-Entscheid.
- Kein Retry für PDFs, bei denen der PDF-Leser selbst fehlschlägt (nur Normalisierungsfehler und KI-Parser-Fehler sind relevant).

---

## Anforderungen

### Datenpersistenz

| Feld | Typ | Beschreibung |
|---|---|---|
| `filename` | `string` (unique) | Dateiname des PDF |
| `reason` | `string` | Letzter Fehlergrund (`'normalization_failed'` / Fehlermeldung) |
| `retryCount` | `number` | Anzahl bisheriger Versuche |
| `lastAttemptAt` | `Date` | Zeitstempel des letzten Versuchs |

### Ingestion-Flow (Startup)

Retry erfolgt **inline** während der laufenden Verarbeitung (synchron, kein zweiter Pass):

1. Für jedes PDF wird die KI-Parse + Normalize-Pipeline bis zu `MAX_RETRIES`-mal versucht (beim ersten Fehler sofort).
2. Jeder Fehlschlag wird mit Versuchsnummer geloggt (`WARN`).
3. Erst nach Ausschöpfung aller Versuche wird der Eintrag in `failed_ingestions` persistiert.
4. Erfolgreicher Retry: `berufRepository.save` aufrufen; kein Eintrag in `failed_ingestions`.

### HTTP-Endpunkt

```
POST /ingestion/retry
Response 200: { retried: number, succeeded: number, stillFailing: number }
```

- Löst denselben Retry-Lauf manuell aus.
- Respektiert `MAX_RETRIES` nicht — jede Datei in `failed_ingestions` wird einmal versucht (überschreibt Retry-Limit für manuelle Auslösung).

### Konfiguration

```env
INGESTION_MAX_RETRIES=3   # Default: 3, Startup-Retry wird übersprungen wenn retryCount >= Wert
```

---

## Akzeptanzkriterien

1. **AC-1 — Fehlereintrag wird erstellt:** Wenn `normalize()` `null` zurückgibt, existiert anschließend ein Dokument in `failed_ingestions` mit korrektem `filename`, `reason = 'normalization_failed'`, `retryCount = 1`.
2. **AC-2 — Kein Doppeleintrag:** Schlägt dasselbe PDF beim zweiten Startup erneut fehl, wird `retryCount` auf `2` erhöht — es entsteht kein zweites Dokument.
3. **AC-3 — Retry-Limit:** PDFs mit `retryCount >= INGESTION_MAX_RETRIES` werden beim Startup-Retry übersprungen (WARN-Log).
4. **AC-4 — Erfolgreicher Retry:** Nach erfolgreichem Retry ist das PDF in `berufe` vorhanden und **nicht mehr** in `failed_ingestions`.
5. **AC-5 — HTTP-Endpunkt erreichbar:** `POST /ingestion/retry` gibt `200` mit dem korrekten Zähler-Objekt zurück.
6. **AC-6 — Manueller Retry ignoriert Limit:** `POST /ingestion/retry` versucht auch PDFs mit `retryCount >= MAX_RETRIES`.
7. **AC-7 — Kein Seiteneffekt auf erfolgreiche PDFs:** PDFs, die in `berufe` vorhanden sind, werden durch den Retry-Lauf nicht erneut verarbeitet.

---

## Offene Fragen

1. Soll `POST /ingestion/retry` nur für spezifische Dateinamen auslösbar sein (`?filename=foo.pdf`), oder immer für alle?
2. Sollen fehlgeschlagene Einträge nach Erreichen des Limits automatisch archiviert/gelöscht werden, oder dauerhaft in `failed_ingestions` verbleiben?
3. ~~Soll der Retry-Lauf beim Startup synchron oder asynchron laufen?~~ → **Entschieden: synchroner Inline-Retry** — jeder Fehlschlag wird sofort und direkt in der Verarbeitungsschleife erneut versucht.

---

## Außerhalb des Scopes

- Alerting / Benachrichtigungen bei dauerhaft fehlenden PDFs.
- Automatisches Löschen alter `failed_ingestions`-Einträge.
- UI zur Anzeige fehlgeschlagener PDFs.
- Retry für den PDF-Leser (`PdfReaderService`).
