# System-Patterns — Data-Dobby

## Architekturstil
Layered Monolith — drei klar getrennte Schichten: Ingestion → Normalization → API.

## Schlüsselentscheidungen
- **NestJS** als HTTP-Framework wegen eingebauter Dependency Injection, Modul-System und TypeScript-First-Ansatz.
- **Funktionaler Normalisierungs-Layer**: Keine Seiteneffekte, reine Transformationsfunktionen — erleichtert Unit-Tests erheblich.
- **DTOs** (Data Transfer Objects) als einzige Schnittstelle zwischen Normalization und API, um Rohdaten-Lecks zu verhindern.
- **Strict TypeScript** mit ESLint + Prettier für konsistente Codequalität.

## Muster
- **Mapper-Funktion**: Eine reine Funktion pro Quellformat, die Rohtext auf das einheitliche Schema abbildet.
- **DTO-Schema-Validierung**: NestJS `ValidationPipe` + `class-validator` für eingehende Requests und ausgehende Responses.
- **Repository-Pattern** (optional): Abstraktion der Datenquelle, damit PDF-Ingestion gegen andere Quellen ausgetauscht werden kann.

## Schicht-Grenzen
| Schicht | Darf zugreifen auf | Darf NICHT zugreifen auf |
|---|---|---|
| Ingestion | Dateisystem / PDF-Bibliothek | HTTP, Normalization, API |
| Normalization | Rohdaten (Strings/Objekte) | HTTP, Dateisystem |
| API | Normalization-Output (DTOs) | Rohdaten, Ingestion direkt |

