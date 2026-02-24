# Spec: HTTP-API für Prüfungspläne

**Status:** Implemented  
**Bereich:** `src/api`  
**Erstellt:** 2026-02-24

---

## Zusammenfassung

Bereitstellung von zwei HTTP-REST-Endpunkten, über die normalisierte Prüfungspläne (`Beruf`-Objekte) im JSON-Format abgefragt werden können. Zusätzlich soll eine optionale Datumsfilterung möglich sein.

---

## Problem / Motivation

Die Ingestion- und Normalisierungs-Pipeline speichert aufbereitete Prüfungspläne in MongoDB. Bisher gibt es keine Möglichkeit, diese Daten extern abzufragen. Die Bereitstellung einer REST-API schließt diese Lücke und ermöglicht anderen Systemen und Frontends den Zugriff.

---

## Ziele

- `GET /berufe` gibt alle gespeicherten Berufe mit ihren Prüfungsbereichen zurück.
- `GET /berufe/:id` gibt einen einzelnen Beruf anhand der MongoDB-Dokument-ID zurück.
- Beide Endpunkte unterstützen einen optionalen Query-Parameter `vonDatum` (Format `YYYY-MM-DD`), um nur Berufe zurückzugeben, bei denen mindestens ein Prüfungstermin **am oder nach** dem angegebenen Datum liegt.
- Antworten sind vollständig typisiert (keine `any`-Typen).

## Nicht-Ziele

- Authentifizierung / Autorisierung (nicht im aktuellen Scope).
- Schreib-/Mutationsendpunkte (POST, PUT, DELETE).
- Paginierung (kann in einem Folge-Spec adressiert werden).
- Volltextsuche.

---

## Anforderungen

### Funktional

| ID  | Anforderung |
|-----|-------------|
| F-1 | `GET /berufe` liefert ein JSON-Array aller `Beruf`-Dokumente aus MongoDB (`200 OK`). |
| F-2 | `GET /berufe?vonDatum=YYYY-MM-DD` liefert nur Berufe, bei denen mindestens ein `Termin.datum >= vonDatum` existiert. |
| F-3 | `GET /berufe/:id` liefert ein einzelnes `Beruf`-Dokument anhand der MongoDB-ID (`200 OK`). |
| F-4 | `GET /berufe/:id` mit unbekannter ID liefert `404 Not Found` mit einer aussagekräftigen Fehlermeldung. |
| F-5 | Der Query-Parameter `vonDatum` wird auf `YYYY-MM-DD`-Format validiert; ungültige Werte liefern `400 Bad Request`. |
| F-6 | Die Antwortstruktur entspricht dem bestehenden `Beruf`-Interface aus `src/domain/interfaces.ts`, ergänzt um `_id` und `filename`. |

### Nicht-funktional

| ID   | Anforderung |
|------|-------------|
| NF-1 | Kein direkter Zugriff auf Rohdaten oder die Ingestion-Schicht — ausschließlich über `BerufRepository`. |
| NF-2 | Strikt typisiert (TypeScript strict mode, kein `any`). |
| NF-3 | Funktionaler Stil: Datumfilterung als reine Funktion im Service. |
| NF-4 | NestJS-Konventionen: Controller, Service, Module; keine Logik im Controller. |

---

## Akzeptanzkriterien

| ID   | Kriterium | Testbar? |
|------|-----------|----------|
| AC-1 | `GET /berufe` gibt `200` und ein Array zurück (kann leer sein). | Ja — E2E / Unit |
| AC-2 | `GET /berufe?vonDatum=2026-01-01` gibt nur Berufe zurück, bei denen mind. ein Termin ≥ 2026-01-01 existiert. | Ja — Unit (reine Filterfunktion) |
| AC-3 | `GET /berufe?vonDatum=kein-datum` gibt `400` zurück. | Ja — E2E / Unit |
| AC-4 | `GET /berufe/:id` mit gültiger ID gibt den Beruf mit `200` zurück. | Ja — E2E |
| AC-5 | `GET /berufe/:id` mit unbekannter ID gibt `404` zurück. | Ja — E2E / Unit |
| AC-6 | Der `ApiModule` importiert `PersistenceModule` und ist im `AppModule` registriert. | Ja — Compile-Check |
| AC-7 | Keine neuen `any`-Typen eingeführt. | Ja — `tsc --noEmit` |

---

## Offene Fragen

1. ~~Soll `vonDatum` auch in `GET /berufe/:id` unterstützt werden?~~ → **Ja**: Aufgaben innerhalb des gefundenen Berufs werden auf `termin.datum >= vonDatum` gefiltert; leere Bereiche werden entfernt.
2. ~~Soll `_id` und `filename` in der Antwort enthalten sein?~~ → **Ja**: Antwort enthält `_id`, `filename` und vollständiges `beruf`-Objekt.
3. ~~Datumsformat für `vonDatum`?~~ → **YYYY-MM-DD** (lexikalisch vergleichbar mit gespeichertem `Termin.datum`).

---

## Out of Scope

- Authentifizierung und Autorisierung.
- Schreiboperationen über die API.
- Paginierung und Sortierung.
- OpenAPI/Swagger-Dokumentation (separater Spec).
- Aggregationsabfragen (z. B. nach Berufsbereich oder Berufsgruppe).
