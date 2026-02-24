# Aktiver Kontext — Data-Dobby

## Aktueller Fokus
HTTP-API-Layer (`GET /berufe`, `GET /berufe/:id`) implementiert und getestet. Nächster Schritt: Spec `manuelle-pruefung-review-workflow.md` umsetzen.

## Status
- NestJS-Projektgerüst lauffähig (`pnpm build` ✓, `pnpm test` ✓).
- Domain-Interfaces (`interfaces.ts`) entsprechen Spec-Schema.
- Persistence-Layer: Mongoose-Schema, `BerufRepository` mit Dedup-by-filename, MongoDB-Integration via `MONGODB_URI`.
- Normalization-Layer: Pure function `normalize()` mit AJV-Schema-Validierung, Unit-Tests grün.
- Ingestion-Layer: `PdfReaderService` (pdf-parse v2), `AiParserService` (OpenAI-kompatibler Client), `IngestionService` (OnApplicationBootstrap, sequenziell, Fehler-Logging).
- Spec `pdf-ingestion-normalisierung.md` implementiert und nach `done/` verschoben.

## Letzte Änderungen
- `src/domain/interfaces.ts`: Interfaces an Spec-Schema angepasst (`Termin`, `Aufgabe`, `PruefungsBereich`, `Beruf`, `BerufDocument`).
- Abhängigkeiten installiert: `pdf-parse`, `mongoose`, `@nestjs/mongoose`, `openai`, `ajv`.
- `src/persistence/beruf.schema.ts`: Mongoose-Schema mit eindeutigem `filename`-Index.
- `src/persistence/beruf.repository.ts`: `existsByFilename()` + `save()`.
- `src/persistence/persistence.module.ts`: MongoDB-Verbindung via `MONGODB_URI`, Feature-Registration.
- `src/normalization/normalizer.ts`: Pure `normalize()`-Funktion mit AJV-Validierung.
- `src/normalization/normalizer.spec.ts`: 3 Unit-Tests (valide, fehlerhaft, null).
- `src/ingestion/pdf-reader.service.ts`: Liest PDFs via `pdf-parse` v2 (`PDFParse({ data })`).
- `src/ingestion/ai-parser.service.ts`: OpenAI-kompatibler Client, parst JSON-Antwort.
- `src/ingestion/ingestion.service.ts`: Startup-Trigger, sequenzielle Verarbeitung, Dedup, Fehler-Logging.
- `src/ingestion/ingestion.module.ts`: Importiert `PersistenceModule` + `ConfigModule`.

## Letzte Änderungen (aktuell)
- Spec `deduplication-ingestion.md` implementiert → `done/` verschoben.
- `src/ingestion/ingestion.service.ts`: Debug-Log `Skipping <filename>: already ingested` für übersprungene Dateien ergänzt.
- `src/ingestion/ingestion.service.spec.ts`: 4 Unit-Tests (AC2, AC5 ×2, Happy Path) — alle grün.
- `src/persistence/beruf.repository.spec.ts`: 2 Unit-Tests für `existsByFilename` (AC3) — alle grün.
- `src/persistence/beruf.repository.ts`: `findAll()` und `findById()` ergänzt.
- `src/api/beruf-api.service.ts` (neu): `BerufApiService` mit `findAll()`, `findById()`, `vonDatum`-Validierung (`YYYY-MM-DD`) und reiner Filterfunktion `filterBereiche()`.
- `src/api/beruf-api.controller.ts` (neu): `@Controller('berufe')` mit `GET /berufe` und `GET /berufe/:id`.
- `src/api/api.module.ts`: `PersistenceModule` importiert, `BerufApiService` + `BerufApiController` registriert.
- `src/api/beruf-api.service.spec.ts` (neu): 7 Unit-Tests (Datumsfilterung, 404, 400); alle grün.
- Spec `api-berufe-endpunkte.md` → Status `Implemented`, nach `done/` verschoben.

## Nächste Schritte
1. Spec `manuelle-pruefung-review-workflow.md` (backlog) planen und umsetzen:
   - `status`-Feld ins Mongoose-Schema.
   - `ReviewModule` mit Endpunkten implementieren.
   - Minimal-Frontend unter `/review/ui` ausliefern.
2. End-to-End-Test mit echten Umgebungsvariablen (`MONGODB_URI`, `AI_HUB_API_KEY`) durchführen.
