# Tech-Kontext — Data-Dobby

## Stack
- Sprache: TypeScript (strict mode, keine `any`-Typen)
- Laufzeit: Node.js
- Framework: NestJS
- PDF-Parsing: `pdf-parse` oder `pdfjs-dist` (TBD)
- KI-Dienst: Externer OpenAI-kompatibler Endpunkt — `https://adesso-ai-hub.3asabc.de/v1`, Modell `claude-sonnet-4-6*`
  - Paket: `openai` (npm)
  - Konfiguration via Env: `AI_HUB_API_KEY`, `AI_HUB_BASE_URL`
- Datenbank: MongoDB
  - Konfiguration via Env: `MONGODB_URI`
  - Collection: `berufe`
- Paketmanager: pnpm

## Umgebungsvariablen (required)
| Variable | Beschreibung |
|----------|--------------|
| `AI_HUB_API_KEY` | API-Key für den externen KI-Dienst |
| `AI_HUB_BASE_URL` | Base-URL des KI-Dienstes (z. B. `https://adesso-ai-hub.3asabc.de/v1`) |
| `MONGODB_URI` | Verbindungs-URI zur MongoDB-Instanz |
| `PDF_DIR` | Pfad zum Verzeichnis mit den zu verarbeitenden PDFs |

## Build / Run
```bash
pnpm install
pnpm build          # tsc / nest build
pnpm start:dev      # Entwicklungsserver mit Watch
pnpm start          # Produktionsstart
```

## Test
```bash
pnpm test           # Unit-Tests (Jest)
pnpm test:cov       # Coverage-Report
```

## Lint / Format
```bash
pnpm lint           # ESLint
pnpm format         # Prettier
```

## Constraints
- API läuft auf Port 3000.
- Kein direkter HTTP-Zugriff aus dem Ingestion-Layer.
- Normalization-Layer ist rein funktional (keine Seiteneffekte, keine I/O).
- Secrets niemals im Code — ausschließlich über Umgebungsvariablen.

