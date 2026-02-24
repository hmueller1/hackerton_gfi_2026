#!/usr/bin/env python3
"""
IHK Prüfungsdaten Extraktion

Extrahiert strukturierte JSON-Daten aus den PDF-Seiten des Prüfungstermins W25
mittels pdfplumber (Textextraktion) und der Anthropic API (Strukturierung).

Verwendung:
  export ANTHROPIC_API_KEY=<your-key>
  python src/extract_pruefungsdaten.py --page 1
  python src/extract_pruefungsdaten.py --pages 1-10
  python src/extract_pruefungsdaten.py --all

Ausgabe: doc/berufe/output/beruf_<NNN>.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import anthropic
import pdfplumber

PAGES_DIR = Path("doc/berufe/pages")
OUTPUT_DIR = Path("doc/berufe/output")

EXTRACTION_PROMPT = """Extrahiere die Prüfungsdaten aus folgendem PDF-Text eines IHK-Prüfungsübersichtsblatts.

Gib die Daten als JSON zurück, das genau diesem Schema entspricht:
{
  "beruf": {
    "beschreibung": "<Name des Ausbildungsberufs ohne Berufsnummer und ohne Klammern>",
    "berufNr": [<Berufsnummer(n) als Integer>],
    "prüfungsBereich": [
      {
        "name": "<Bezeichnung des Prüfungsbereichs>",
        "aufgaben": [
          {
            "name": "<Aufgabenbezeichnung>",
            "struktur": "<Aufgabenstruktur, z.B. Anzahl geb./ungeb. Aufgaben, Punkte, Faktor/Divisor>",
            "termin": {
              "datum": "<DD.MM.YYYY oder 'TBD' wenn nicht angegeben>",
              "uhrzeitvon": "<HH:MM>",
              "uhrzeitbis": "<HH:MM>",
              "dauer": <Dauer in Minuten als Integer>
            },
            "hilfmittel": "<Erlaubte Hilfsmittel oder 'keine'>'"
          }
        ]
      }
    ]
  }
}

Regeln:
- berufNr: Extrahiere alle Nummern in Klammern hinter dem Berufsnamen als Integer-Array
- Jeder Prüfungsbereich (WISO, Schriftliche Prüfung, Praktische Prüfung, Schwerpunkte etc.) wird ein eigener Eintrag in prüfungsBereich
- WISO (Wirtschafts- und Sozialkunde) immer als eigenen Prüfungsbereich erfassen
- Für Bereiche ohne festes Datum (z.B. Praktische Prüfung mit Prüfungszeitraum): datum="TBD", uhrzeitvon="00:00", uhrzeitbis="00:00", dauer=0
- Dauer: Berechne aus der Vorgabezeit in Minuten (1 Std. = 60 Min., 1,5 Std. = 90 Min.)
- Wenn Teil 1 und Teil 2 denselben Zeitslot haben, erstelle trotzdem separate aufgaben-Einträge
- hilfmittel: Wenn "keine" angegeben oder nicht vorhanden, schreibe "keine"
- Antworte NUR mit gültigem JSON, ohne Erklärungen, Kommentare oder Markdown-Formatierung

PDF-Text:
"""


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrahiert den gesamten Text aus einer PDF-Datei mit pdfplumber."""
    with pdfplumber.open(pdf_path) as pdf:
        texts = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)


def parse_with_ai(text: str, client: anthropic.Anthropic) -> dict:
    """Sendet den extrahierten PDF-Text an die Anthropic API zur JSON-Strukturierung."""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT + text,
            }
        ],
    )

    response_text = message.content[0].text.strip()

    # Entferne eventuelle Markdown-Codeblöcke
    if response_text.startswith("```"):
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text)
        response_text = re.sub(r"\s*```$", "", response_text).strip()

    return json.loads(response_text)


def process_page(
    page_num: int, client: anthropic.Anthropic, verbose: bool = True
) -> dict | None:
    """Verarbeitet eine einzelne PDF-Seite und speichert das extrahierte JSON."""
    pdf_path = PAGES_DIR / f"gesamt-bpue-w25-data_{page_num}.pdf"

    if not pdf_path.exists():
        print(f"  Datei nicht gefunden: {pdf_path}", file=sys.stderr)
        return None

    if verbose:
        print(f"Verarbeite Seite {page_num}: {pdf_path.name}")

    try:
        text = extract_text_from_pdf(pdf_path)

        if not text.strip():
            print(f"  Kein Text extrahierbar aus Seite {page_num}", file=sys.stderr)
            return None

        data = parse_with_ai(text, client)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"beruf_{page_num:03d}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if verbose:
            beruf = data.get("beruf", {})
            beschreibung = beruf.get("beschreibung", "Unbekannt")
            beruf_nr = beruf.get("berufNr", [])
            bereiche = len(beruf.get("prüfungsBereich", []))
            print(f"  -> {beschreibung} {beruf_nr} ({bereiche} Prüfungsbereiche)")
            print(f"  -> Gespeichert: {output_file}")

        return data

    except json.JSONDecodeError as e:
        print(f"  JSON-Fehler bei Seite {page_num}: {e}", file=sys.stderr)
        return None
    except anthropic.APIError as e:
        print(f"  API-Fehler bei Seite {page_num}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Fehler bei Seite {page_num}: {e}", file=sys.stderr)
        return None


def get_available_pages() -> list[int]:
    """Gibt alle verfügbaren Seitennummern sortiert zurück."""
    pages = []
    for pdf_file in PAGES_DIR.glob("gesamt-bpue-w25-data_*.pdf"):
        match = re.search(r"_(\d+)\.pdf$", pdf_file.name)
        if match:
            pages.append(int(match.group(1)))
    return sorted(pages)


def parse_page_range(pages_arg: str) -> list[int]:
    """Parst einen Seitenbereich wie '1-10' oder '1,3,5,10-20'."""
    pages = []
    for part in pages_arg.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


def main():
    parser = argparse.ArgumentParser(
        description="Extrahiert IHK Prüfungsdaten aus PDF-Seiten mittels Anthropic API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python src/extract_pruefungsdaten.py --page 1
  python src/extract_pruefungsdaten.py --pages 1-10
  python src/extract_pruefungsdaten.py --pages 1,3,5
  python src/extract_pruefungsdaten.py --all
        """,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--page", type=int, metavar="NR", help="Einzelne Seite verarbeiten")
    group.add_argument("--all", action="store_true", help="Alle verfügbaren Seiten verarbeiten")
    group.add_argument(
        "--pages",
        type=str,
        metavar="BEREICH",
        help="Seitenbereich, z.B. '1-10' oder '1,3,5'",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Weniger Ausgabe")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Fehler: Umgebungsvariable ANTHROPIC_API_KEY ist nicht gesetzt.", file=sys.stderr)
        print("Setze sie mit: export ANTHROPIC_API_KEY=<dein-api-key>", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    if args.page:
        pages = [args.page]
    elif args.all:
        pages = get_available_pages()
        if not args.quiet:
            print(f"Gefunden: {len(pages)} Seiten in {PAGES_DIR}")
    elif args.pages:
        pages = parse_page_range(args.pages)

    success = 0
    failed = 0

    for page_num in pages:
        result = process_page(page_num, client, verbose=not args.quiet)
        if result:
            success += 1
        else:
            failed += 1

    if len(pages) > 1 and not args.quiet:
        print(f"\nErgebnis: {success} erfolgreich, {failed} fehlgeschlagen")
        print(f"Ausgabe in: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
