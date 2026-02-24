# System-Patterns — Data-Dobby

## Architekturstil
Layered Monolith — drei klar getrennte Schichten: Ingestion → Normalization → API.

## Schlüsselentscheidungen
- **NestJS** als HTTP-Framework wegen eingebauter Dependency Injection, Modul-System und TypeScript-First-Ansatz.
- **Funktionaler Normalisierungs-Layer**: Keine Seiteneffekte, reine Transformationsfunktionen — erleichtert Unit-Tests erheblich.
- **AJV-Schema-Validierung** im Normalization-Layer statt class-validator, da die Daten von einem KI-Dienst kommen und nicht aus HTTP-Requests.
- **DTOs** (Data Transfer Objects) als einzige Schnittstelle zwischen Normalization und API, um Rohdaten-Lecks zu verhindern.
- **Strict TypeScript** mit ESLint + Prettier für konsistente Codequalität.

## Muster

### Startup-Ingestion-Pattern
`IngestionService` implementiert `OnApplicationBootstrap`. Beim Start werden alle PDFs aus `PDF_DIR` sequenziell verarbeitet. Fehler pro Datei werden geloggt und übersprungen — kein Programmabbruch.

### Dedup-by-Filename-Pattern
Vor dem Verarbeiten prüft `BerufRepository.existsByFilename()`, ob ein Dokument mit demselben Dateinamen bereits existiert. Duplikate werden übersprungen.

### AI-Parse-and-Validate-Pattern
Rohtext → KI-Dienst (OpenAI-kompatibler Endpunkt) → JSON-Antwort → AJV-Schema-Validierung → typisiertes `BerufDocument` oder `null`.

### Repository-Pattern
`BerufRepository` abstrahiert MongoDB-Zugriff. Öffentliche Methoden: `existsByFilename()`, `save()`, `findAll()`, `findById()`.

### API-Service-Pattern (Datumsfilterung)
Die `vonDatum`-Filterung ist als reine Funktion (`filterBereiche`) außerhalb der Service-Klasse implementiert. Sie filtert `PruefungsBereich[]` auf Aufgaben mit `termin.datum >= vonDatum` und entfernt leere Bereiche. Validierung des Datumsformats (`YYYY-MM-DD`) erfolgt per Regex in einer separaten reinen Funktion vor dem Repository-Zugriff. Fehler werden als NestJS-Exceptions (`BadRequestException`, `NotFoundException`) geworfen — keine Custom-Exception-Klassen.

## Schicht-Grenzen
| Schicht | Darf zugreifen auf | Darf NICHT zugreifen auf |
|---|---|---|
| Ingestion | Dateisystem, PDF-Bibliothek, KI-Dienst, Persistence | HTTP, Normalization-Internals |
| Normalization | Rohdaten (unknown) | HTTP, Dateisystem, Datenbank |
| Persistence | MongoDB via Mongoose | HTTP, Ingestion, Normalization |
| API | Persistence (Repository) | Rohdaten, Ingestion direkt |
