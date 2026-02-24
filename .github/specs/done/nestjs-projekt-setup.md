# Spec: NestJS-Projektgrundstruktur für Data-Dobby

**Status:** Implemented  
**Erstellt:** 2026-02-24  
**Bereich:** `root` (Projektgerüst)

---

## Zusammenfassung

Das NestJS-Grundgerüst für Data-Dobby wird eingerichtet. Es umfasst die Projektinitialisierung mit `pnpm`, TypeScript-Strict-Mode, die vorgesehene Modulstruktur (ingestion, normalization, persistence, api, domain) sowie Build-, Test- und Lint-Konfiguration.

---

## Problem / Motivation

Aktuell existiert kein Quellcode — nur Dokumentation und PDF-Rohdaten. Ohne ein lauffähiges NestJS-Projekt können keine Module, keine API und keine Ingestion-Logik implementiert werden. Dieser Schritt ist die Voraussetzung für alle weiteren Specs.

---

## Ziele

- Lauffähiges NestJS-Projekt unter `/src` mit `pnpm` als Paketmanager.
- TypeScript im Strict-Mode konfiguriert (keine `any`-Typen).
- Modulstruktur entspricht dem Architektur-Snapshot: `ingestion`, `normalization`, `persistence`, `api`, `domain`.
- Umgebungsvariablen werden über `@nestjs/config` geladen; `.env.example` dokumentiert alle Required-Vars.
- `pnpm start:dev`, `pnpm build`, `pnpm test` und `pnpm lint` funktionieren.

## Nicht-Ziele

- Keine Implementierung von Fachlogik (Parsing, KI-Aufruf, Datenbankabfragen) in dieser Spec.
- Kein Docker-Setup (Folge-Spec).
- Keine CI/CD-Pipeline (Folge-Spec).

---

## Anforderungen

### Funktional

| ID   | Anforderung |
|------|-------------|
| F-01 | NestJS-Projekt wird mit `pnpm` initialisiert; kein `npm`/`yarn`. |
| F-02 | `src/`-Verzeichnis enthält Platzhalter-Module: `ingestion`, `normalization`, `persistence`, `api`. |
| F-03 | Gemeinsame Interfaces/DTOs liegen unter `src/domain/` (`Beruf`, `PruefungsBereich`, `Aufgabe`, `Termin`). |
| F-04 | `@nestjs/config` ist installiert; `ConfigModule.forRoot()` wird im `AppModule` registriert. |
| F-05 | `.env.example` dokumentiert alle Pflicht-Umgebungsvariablen (`AI_HUB_API_KEY`, `AI_HUB_BASE_URL`, `MONGODB_URI`, `PDF_DIR`). |
| F-06 | API läuft auf Port 3000 (konfigurierbar via `PORT`-Env). |

### Nicht-Funktional

| ID   | Anforderung |
|------|-------------|
| NF-01 | `tsconfig.json` mit `strict: true`, `noImplicitAny: true`, `strictNullChecks: true`. |
| NF-02 | ESLint + Prettier nach NestJS-Standard konfiguriert. |
| NF-03 | Jest als Test-Runner; `pnpm test` läuft ohne Fehler. |

---

## Akzeptanzkriterien

| ID   | Kriterium |
|------|-----------|
| AC-01 | `pnpm start:dev` startet die Anwendung ohne Fehler; Healthcheck `GET /` antwortet mit HTTP 200. |
| AC-02 | `pnpm build` erzeugt ein `dist/`-Verzeichnis ohne TypeScript-Fehler. |
| AC-03 | `pnpm test` läuft grün (mindestens der generierte App-Smoke-Test). |
| AC-04 | `pnpm lint` meldet keine Fehler. |
| AC-05 | Alle fünf Module (`ingestion`, `normalization`, `persistence`, `api`, `domain`) sind als NestJS-Module oder TypeScript-Verzeichnis unter `src/` vorhanden. |
| AC-06 | `.env.example` enthält alle vier Pflicht-Variablen mit Beschreibungskommentar. |
| AC-07 | `tsconfig.json` enthält `"strict": true`. |

---

## Offene Fragen

_Keine — alle relevanten Technologieentscheidungen sind im Tech-Kontext dokumentiert._

---

## Out of Scope

- Fachliche Implementierung der Module.
- Docker / Container-Setup.
- CI/CD-Pipelines.
- MongoDB-Verbindung (Folge-Spec: persistence-Modul).
