# Aktiver Kontext — Data-Dobby

## Aktueller Fokus
PDF-Ingestion + Normalisierung implementiert. Nächster Schritt: HTTP-API-Endpunkte für `/berufe`.

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

## Nächste Schritte
1. API-Modul implementieren: `GET /berufe`, `GET /berufe/:id`.
2. `/specify` für HTTP-API-Endpunkte aufrufen.
3. End-to-End-Test mit echten Umgebungsvariablen durchführen.
