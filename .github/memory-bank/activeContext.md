# Aktiver Kontext — Data-Dobby

## Aktueller Fokus
NestJS-Grundstruktur implementiert — Module und Fachlogik stehen als nächstes an.

## Status
- NestJS-Projektgerüst lauffähig (`pnpm build` ✓, `pnpm test` ✓).
- Alle Module als Platzhalter angelegt: `ingestion`, `normalization`, `persistence`, `api`, `domain`.
- Spec für PDF-Ingestion + Normalisierung im Backlog, Implementierung steht aus.

## Letzte Änderungen
- Node.js 22 und pnpm installiert.
- `package.json`, `tsconfig.json`, `tsconfig.build.json`, `nest-cli.json`, `.eslintrc.js`, `.prettierrc` erstellt.
- `src/main.ts`, `src/app.module.ts`, `src/app.controller.ts`, `src/app.service.ts` erstellt.
- Platzhalter-Module erstellt: `src/ingestion/`, `src/normalization/`, `src/persistence/`, `src/api/`.
- Domain-Interfaces angelegt: `src/domain/interfaces.ts` (`Beruf`, `PruefungsBereich`, `Aufgabe`, `Termin`).
- `.env.example` mit allen Pflicht-Umgebungsvariablen dokumentiert.
- `@nestjs/config` im `AppModule` global registriert.
- Spec `.github/specs/active/nestjs-projekt-setup.md` erstellt (Status: In Progress).

## Nächste Schritte
1. Spec `nestjs-projekt-setup.md` auf `Implemented` setzen und in `done/` verschieben.
2. Ingestion-Modul implementieren: PDF-Parsing → KI-Normalisierung → Schema-Validierung → MongoDB.
3. Persistence-Modul implementieren: MongoDB-Verbindung via `@nestjs/mongoose`.
4. API-Modul implementieren: `GET /berufe`, `GET /berufe/:kennung`.
5. `/specify` für HTTP-API-Endpunkte aufrufen.

