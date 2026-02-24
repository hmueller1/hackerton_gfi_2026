# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hackathon project to extract IHK (Chamber of Commerce) vocational exam schedules from PDF documents into structured JSON using AI vision + text extraction. The source PDFs contain German exam data for the Winter 2025 term.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Environment variables (see `.env.example`):
- `MODEL_HUB_API_KEY` — API key for Adesso AI Hub
- `MODEL_HUB_URL` — Base URL (`https://adesso-ai-hub.3asabc.de/v1`)
- `MODEL_HUB_MODEL` — Model name (e.g. `claude-sonnet-4-5*`)

## Running the Extraction

```bash
python src/extract_pruefungsdaten.py --page 5        # single page
python src/extract_pruefungsdaten.py --pages 1-10    # page range
python src/extract_pruefungsdaten.py --pages 1,3,5   # specific pages
python src/extract_pruefungsdaten.py --all            # all 115 pages
python src/extract_pruefungsdaten.py --all -q         # quiet mode
```

Input PDFs are in `doc/berufe/pages/` (per-page) and `doc/berufe/gesamt-bpue-w25-data.pdf` (full document). Output JSON files go to `doc/berufe/output/` (gitignored).

## Architecture

The system uses a hybrid approach: **pdfplumber** extracts text, **PyMuPDF (fitz)** renders PDF pages to images, then both are sent to the AI model via an OpenAI-compatible API (Adesso Model Hub) to produce structured JSON.

**`src/extract_pruefungsdaten.py`** — Single-file script handling the full pipeline:
1. Text extraction from PDF (`extract_text_from_pdf`)
2. PDF-to-image conversion as Base64 PNG (`pdf_to_base64_image`)
3. AI parsing with a German-language prompt that defines the output schema (`parse_with_ai`)
4. Per-page processing and JSON file output (`process_page`)

## Data Schema

Output must conform to `doc/berufe/schema.json` (JSON Schema Draft-07). Hierarchy:

```
beruf
├── beschreibung (profession name)
├── berufNr[] (profession numbers, integers)
└── prüfungsBereich[] (exam areas)
    ├── name
    └── aufgaben[] (tasks)
        ├── name
        ├── struktur (point calculation, weighted factors)
        ├── termin {datum, uhrzeitvon, uhrzeitbis, dauer}
        └── hilfmittel (allowed aids, optional)
```

Example outputs are in `doc/berufe/beispiel.json` and `doc/berufe/output/beruf_*.json`.

## Key Conventions

- All domain content (prompts, field names, data) is in **German**
- The AI API uses the **OpenAI client** with a custom `base_url` (not direct Anthropic SDK)
- Python 3.10+ required (uses `X | None` type union syntax)
- No test suite exists yet; validation is via JSON Schema conformance
- Practical exams with unknown dates use `"TBD"` as the datum value
