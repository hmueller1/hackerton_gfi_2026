# Spec: Keine Doppel-Ingestion bereits eingelesener PDF-Dateien

**Status:** Implemented  
**Bereich:** `src/ingestion`, `src/persistence`  
**Erstellt:** 2026-02-24

---

## Zusammenfassung

Bereits erfolgreich verarbeitete PDF-Dateien sollen beim erneuten Start der Anwendung **nicht nochmals eingelesen, geparst oder gespeichert** werden. Dies schont KI-Token-Budget und verhindert Datenduplikate in MongoDB.

---

## Problem / Motivation

Der Ingestion-Service wird bei jedem `onApplicationBootstrap`-Event ausgeführt. Ohne Deduplizierung würde jede PDF-Datei bei jedem Neustart erneut:

1. via `PdfReaderService` gelesen (I/O),
2. via `AiParserService` geparst (KI-API-Aufruf, teuer),
3. in MongoDB gespeichert (Datenduplikat oder Constraint-Fehler).

---

## Ziele

- Jede PDF-Datei wird **höchstens einmal** erfolgreich in MongoDB gespeichert.
- Bereits gespeicherte Dateien werden beim Neustart **übersprungen** (kein KI-Aufruf).
- Eine **klare Log-Ausgabe** zeigt an, welche Dateien übersprungen wurden.
- Fehlgeschlagene Ingestions (kein DB-Eintrag) werden beim nächsten Start **erneut versucht**.

## Nicht-Ziele

- Kein Mechanismus zur **Aktualisierung** bereits gespeicherter Berufe bei geänderter PDF.
- Keine Deduplizierung auf Inhaltsebene (nur filename-basiert).
- Kein manueller Re-Ingestion-Endpunkt (separates Feature).

---

## Anforderungen

| # | Anforderung |
|---|-------------|
| R1 | Vor dem KI-Aufruf prüft der `IngestionService` via `BerufRepository.existsByFilename(filename)`, ob die Datei bereits gespeichert ist. |
| R2 | Ist die Datei bereits vorhanden, wird sie **ohne KI-Aufruf** übersprungen; ein `Logger.debug`-Eintrag wird erzeugt. |
| R3 | Das Mongoose-Schema definiert `filename` als `unique: true`, um Duplikate auf DB-Ebene zu verhindern. |
| R4 | Ein fehlgeschlagener Ingestion-Versuch (Exception oder `normalize` gibt `null` zurück) hinterlässt **keinen** DB-Eintrag, sodass die Datei beim nächsten Start erneut versucht wird. |
| R5 | Die `existsByFilename`-Methode im Repository ist mit einem Unit-Test abgedeckt. |

---

## Akzeptanzkriterien

| # | Kriterium | Testbar durch |
|---|-----------|---------------|
| AC1 | Startet die App zweimal mit denselben PDFs, enthält MongoDB nach dem zweiten Start **dieselbe Anzahl** Dokumente wie nach dem ersten. | E2E- oder Integrations-Test |
| AC2 | Der Log enthält beim zweiten Start für jede bereits vorhandene Datei eine Debug-Meldung wie `Skipping <filename>: already ingested`. | Log-Assertion im Test |
| AC3 | `BerufRepository.existsByFilename` gibt `true` zurück, wenn ein Dokument mit diesem Dateinamen existiert, sonst `false`. | Unit-Test |
| AC4 | Ein doppelter `save`-Aufruf mit demselben Dateinamen wirft einen MongoDB Unique-Constraint-Fehler (kein stilles Überschreiben). | Unit-/Integrations-Test |
| AC5 | Eine Datei, deren Verarbeitung mit einem Fehler abgebrochen wurde, ist **nicht** in MongoDB vorhanden und wird beim nächsten Start erneut versucht. | Unit-Test (`IngestionService`) |

---

## Offene Fragen

- **OQ1:** Soll es einen Admin-Endpunkt geben, um eine einzelne Datei manuell neu einzulesen (Force-Re-Ingest)? → Scope dieses Features: **Nein** (separates Backlog-Item).
- **OQ2:** Soll `existsByFilename` einen Index auf `filename` nutzen? → Ja, bereits via `unique: true` im Schema impliziert; expliziter Index empfohlen.

---

## Außerhalb des Scopes

- Inhaltliche Deduplizierung (gleicher Beruf, andere Datei).
- Versionierung von Berufs-Datensätzen.
- Webhook-/Watch-basiertes Neuladen bei Dateiänderung.
