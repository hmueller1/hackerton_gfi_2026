# Spec: Manueller Prüf- und Freigabe-Workflow (Human-in-the-Loop Review)

**Status:** Draft  
**Erstellt:** 2026-02-24  
**Bereich:** `src/review/`, `src/persistence/`, Frontend (eingebettetes Mini-UI)

---

## Zusammenfassung

Sachbearbeiter können neu eingelesene Dokumente manuell prüfen, das normalisierte JSON-Objekt direkt bearbeiten und anschließend freigeben. Erst nach expliziter Freigabe gilt ein Dokument als final genehmigt und verschwindet aus der Review-Warteschlange.

---

## Problem / Motivation

Derzeit werden PDF-Dokumente vollautomatisch eingelesen, normalisiert und persistent gespeichert — ohne menschliche Qualitätssicherung. KI-Parsing ist fehleranfällig: Feldwerte können falsch extrahiert oder komplett fehlen. Fehlerhafte Daten würden ohne Review direkt in die produktive API fließen.

Ein manueller Review-Schritt erlaubt es Sachbearbeitern, Fehler zu korrigieren, bevor Daten für externe Systeme sichtbar werden.

---

## Ziele

- Sachbearbeiter sehen eine Liste aller Dokumente mit Status `pending_review`.
- Pro Dokument öffnet sich eine Split-View: links Original-PDF, rechts editierbares JSON.
- Das JSON-Objekt kann direkt im Browser bearbeitet und gespeichert werden.
- Nach Freigabe wechselt der Status auf `approved`; das Dokument verschwindet aus der Review-Liste.
- Die bestehende `GET /berufe`-API liefert **nur** Dokumente mit Status `approved`.

## Nicht-Ziele

- Kein Rollenmanagement / Authentifizierung (out of scope für diesen Hackathon-Sprint).
- Keine Versionierung von Review-Änderungen (kein Audit-Trail im ersten Schritt).
- Kein Ablehnungs-Workflow (kein `rejected`-Status, kein Löschen aus der UI).
- Kein Realtime-Push (kein WebSocket); einfache Polling-fähige REST-API genügt.

---

## Anforderungen

### Backend

| ID | Anforderung |
|----|-------------|
| B1 | Das Mongoose-Schema `BerufeDocument` erhält ein Pflichtfeld `status: 'pending_review' \| 'approved'` (Default: `'pending_review'`). |
| B2 | `BerufRepository` wird um `findPending()`, `findById(id)`, `updateBeruf(id, beruf)` und `approve(id)` erweitert. |
| B3 | `IngestionService` speichert neue Dokumente immer mit `status: 'pending_review'`. |
| B4 | `GET /berufe` und `GET /berufe/:id` (API-Layer) filtern auf `status: 'approved'`. |
| B5 | Neues `ReviewModule` mit folgenden Endpunkten: |
|    | `GET /review` — Liste aller `pending_review`-Dokumente (id, filename, beschreibung). |
|    | `GET /review/:id` — vollständiges `beruf`-JSON + `filename` + `pdfUrl` für ein Dokument. |
|    | `PATCH /review/:id` — ersetzt das `beruf`-JSON (validiert gegen AJV-Schema). |
|    | `POST /review/:id/approve` — setzt `status: 'approved'`. |
| B6 | `GET /review/:id` liefert eine `pdfUrl` (relativer Pfad zum Abruf der Original-PDF-Datei über `GET /review/:id/pdf`). |
| B7 | `GET /review/:id/pdf` streamt die Original-PDF-Datei (aus dem Ingestion-Quellverzeichnis) als `application/pdf`. |

### Frontend

| ID | Anforderung |
|----|-------------|
| F1 | Ein einfaches Single-Page-HTML/JS-Interface wird unter `/review/ui` statisch ausgeliefert (NestJS `ServeStaticModule` oder eingebetteter Controller). |
| F2 | Die Listenansicht zeigt: `filename`, `beschreibung`, Zeitstempel (`createdAt`). |
| F3 | Klick auf einen Eintrag öffnet die Split-View: links `<iframe>`/`<embed>` für die PDF, rechts ein `<textarea>` (oder JSON-Editor) mit dem `beruf`-JSON. |
| F4 | „Speichern"-Button sendet `PATCH /review/:id` mit dem bearbeiteten JSON. Bei Validierungsfehler wird eine Fehlermeldung angezeigt. |
| F5 | „Freigeben"-Button sendet `POST /review/:id/approve`. Nach Erfolg: Rückkehr zur Liste; freigegebenes Dokument erscheint nicht mehr. |
| F6 | Fehler (Netzwerk, Validierung) werden inline als Meldung dargestellt — kein `alert()`. |

---

## Akzeptanzkriterien (testbar)

| # | Kriterium |
|---|-----------|
| AC1 | Nach Ingestion eines neuen PDFs hat das gespeicherte Dokument `status: 'pending_review'`. |
| AC2 | `GET /review` gibt das neue Dokument zurück; `GET /berufe` gibt es **nicht** zurück. |
| AC3 | `PATCH /review/:id` mit validem JSON aktualisiert das `beruf`-Objekt in der Datenbank. |
| AC4 | `PATCH /review/:id` mit invalide JSON-Struktur (fehlende Pflichtfelder) antwortet mit HTTP 422 und einer Fehlermeldung. |
| AC5 | `POST /review/:id/approve` setzt `status: 'approved'`. Danach liefert `GET /review` dieses Dokument nicht mehr, `GET /berufe` hingegen schon. |
| AC6 | `GET /review/:id/pdf` liefert den korrekten `Content-Type: application/pdf` und den Binär-Inhalt der Originaldatei. |
| AC7 | Die UI zeigt nach Freigabe eines Dokuments die aktualisierte Liste ohne das freigegebene Dokument. |

---

## Offene Fragen

1. **PDF-Speicherort:** Werden PDFs nach Ingestion in einem festen Verzeichnis behalten (z. B. `doc/berufe/`)? Pfad muss für Streaming bekannt sein.
2. **JSON-Editor:** Reicht ein `<textarea>` mit Pretty-Print, oder soll eine leichtgewichtige Bibliothek (z. B. `jsoneditor`) eingebunden werden?
3. **Migration:** Bestehende Dokumente in MongoDB haben kein `status`-Feld — Migration benötigt (Default `approved` für Altdaten oder `pending_review`)?

---

## Out of Scope

- Authentifizierung und Autorisierung.
- Audit-Trail / Änderungshistorie.
- E-Mail-Benachrichtigungen bei neuen Dokumenten.
- Ablehnung / Löschen von Dokumenten.
- Mobiles Layout.
