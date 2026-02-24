"""
M1-04 + M1-14 + M2-02 + M2-11 + M2-12: CLI-Einstiegspunkt der BPÜ-Pipeline.

Verwendung:
  python -m api.run_pipeline                               # alle PDFs im Eingangsordner
  python -m api.run_pipeline --input pfad/zu/datei.pdf
  python -m api.run_pipeline --dry-run
  python -m api.run_pipeline --no-ai                       # KI-Schritt deaktivieren
  python -m api.run_pipeline --list-configs
  python -m api.run_pipeline --list-configs --pending      # nur ZUR_REVIEW
  python -m api.run_pipeline --approve-config {beruf}
  python -m api.run_pipeline --reject-config  {beruf}
"""
import argparse
import io
import logging
import sys
from datetime import datetime
from pathlib import Path

# Windows: stdout auf UTF-8 setzen damit Sonderzeichen funktionieren
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from api.config import INPUT_DIR
from api.pipeline import PipelineErgebnis, find_all_pdfs, process_pdf
from api.services.folder_manager import ensure_folder_structure


# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="BPÜ Datenextraktions-Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        metavar="PFAD",
        help="Einzelne PDF-Datei oder Ordner (Standard: Eingangsordner aus .env)",
    )
    parser.add_argument(
        "--data-dir",
        metavar="PFAD",
        help="Basispfad der Ordnerstruktur (überschreibt DATA_DIR aus .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulationsmodus — keine Dateien schreiben oder verschieben",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="KI-Konfig-Generierung deaktivieren (unbekannte Berufe → /fehler/)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Logging-Ausgabe",
    )
    parser.add_argument(
        "--list-configs",
        action="store_true",
        help="Zeigt alle gespeicherten Konfigs und beendet sich",
    )
    parser.add_argument(
        "--pending",
        action="store_true",
        help="Mit --list-configs: zeigt nur Konfigs im Review-Status",
    )
    parser.add_argument(
        "--approve-config",
        metavar="BERUF",
        help="Freigegebene Pending-Konfig für BERUF aktivieren (Major-Bump)",
    )
    parser.add_argument(
        "--reject-config",
        metavar="BERUF",
        help="Pending-Konfig für BERUF ablehnen und löschen",
    )

    args = parser.parse_args()
    _setup_logging(args.verbose)

    # Ordnerstruktur sicherstellen
    ensure_folder_structure()

    # ── Konfig-Aktionen ───────────────────────────────────────────────
    if args.approve_config:
        return _approve_config(args.approve_config)

    if args.reject_config:
        return _reject_config(args.reject_config)

    if args.list_configs:
        _list_configs(nur_pending=args.pending)
        return 0

    # ── PDFs sammeln ─────────────────────────────────────────────────
    if args.input:
        eingang = Path(args.input).resolve()
        if eingang.is_file():
            pdfs = [eingang]
        elif eingang.is_dir():
            pdfs = find_all_pdfs(eingang)
        else:
            print(f"Pfad nicht gefunden: {eingang}", file=sys.stderr)
            return 1
    else:
        pdfs = find_all_pdfs(INPUT_DIR)

    if not pdfs:
        print("Keine PDFs gefunden. Bitte PDFs in den Eingangsordner legen:")
        print(f"  {INPUT_DIR}")
        return 0

    # ── Pipeline-Lauf ────────────────────────────────────────────────
    _print_header(dry_run=args.dry_run, no_ai=args.no_ai)
    ergebnisse: list[PipelineErgebnis] = []

    for pdf in pdfs:
        ergebnis = process_pdf(pdf, dry_run=args.dry_run, no_ai=args.no_ai)
        ergebnisse.append(ergebnis)
        _print_zeile(ergebnis)

    _print_zusammenfassung(ergebnisse)

    # Exit-Code: 1 wenn min. 1 echter Fehler
    fehler = sum(1 for e in ergebnisse if e.status == "FEHLER")
    return 1 if fehler > 0 else 0


# ─────────────────────────────────────────────
# Konfig-Aktionen (approve / reject)
# ─────────────────────────────────────────────

def _approve_config(beruf: str) -> int:
    from api.services.config_manager import approve_config
    print(f"\nKonfig freigeben: '{beruf}'")
    antwort = input("Bestätigen? [j/N] ").strip().lower()
    if antwort != "j":
        print("Abgebrochen.")
        return 0
    try:
        ziel = approve_config(beruf)
        print(f"Konfig freigegeben und gespeichert: {ziel}")
        print("Beruf kann jetzt neu verarbeitet werden.")
        return 0
    except FileNotFoundError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


def _reject_config(beruf: str) -> int:
    from api.services.config_manager import reject_config
    print(f"\nPending-Konfig ablehnen: '{beruf}'")
    antwort = input("Bestätigen? [j/N] ").strip().lower()
    if antwort != "j":
        print("Abgebrochen.")
        return 0
    try:
        reject_config(beruf)
        print(f"Konfig für '{beruf}' abgelehnt und gelöscht.")
        return 0
    except FileNotFoundError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


# ─────────────────────────────────────────────
# Ausgabe-Funktionen
# ─────────────────────────────────────────────

def _print_header(dry_run: bool, no_ai: bool = False) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    modi = []
    if dry_run:
        modi.append("DRY-RUN")
    if no_ai:
        modi.append("NO-AI")
    modus = f" [{', '.join(modi)}]" if modi else ""
    print(f"\nBPÜ Pipeline — Lauf {ts}{modus}")
    print("─" * 70)


def _print_zeile(e: PipelineErgebnis) -> None:
    name = e.pdf_path.name
    try:
        rel  = e.pdf_path.relative_to(INPUT_DIR)
        name = str(rel)
    except ValueError:
        pass

    dauer = f"({e.dauer_ms}ms)"

    if e.status == "ERFOLG":
        ziel = str(e.ausgabe_pfad.name) if e.ausgabe_pfad else ""
        print(f"✓  {name:<45} → ausgabe/{ziel:<30} {dauer}")
    elif e.status == "ZUR_REVIEW":
        score_str = f"Score: {e.konfidenz_score}/100" if e.konfidenz_score is not None else "Score: ?"
        print(f"~  {name:<45} → konfig/pending/ [ZUR_REVIEW | {score_str}]  {dauer}")
        if e.ki_begruendung:
            print(f"   Begründung: \"{e.ki_begruendung}\"")
    elif e.status == "FEHLER":
        print(f"✗  {name:<45} → fehler/ [{e.fehler_typ}] {dauer}")
    else:
        print(f"⚠  {name:<45} → fehler/ [{e.fehler_typ}] {dauer}")


def _print_zusammenfassung(ergebnisse: list[PipelineErgebnis]) -> None:
    gesamt     = len(ergebnisse)
    erfolg     = sum(1 for e in ergebnisse if e.status == "ERFOLG")
    fehler     = sum(1 for e in ergebnisse if e.status == "FEHLER")
    uebersp    = sum(1 for e in ergebnisse if e.status == "UEBERSPRUNGEN")
    zur_review = sum(1 for e in ergebnisse if e.status == "ZUR_REVIEW")

    print("─" * 70)
    teile = [
        f"Gesamt: {gesamt}",
        f"Erfolgreich: {erfolg}",
        f"Fehlerhaft: {fehler}",
        f"Übersprungen: {uebersp}",
    ]
    if zur_review:
        teile.append(f"Zur Review: {zur_review}")
    print(" | ".join(teile))
    print()


def _list_configs(nur_pending: bool = False) -> None:
    import yaml
    from api.config import CONFIG_DIR, PENDING_DIR

    if not nur_pending:
        print("\nKonfig-Bibliothek")
        print("─" * 70)
        aktive = sorted(CONFIG_DIR.glob("*.yaml"))
        if aktive:
            print(f"{'Beruf':<32} {'Version':<10} {'Score':<8} {'Durch':<10} {'Datum'}")
            for p in aktive:
                try:
                    with open(p, encoding="utf-8") as f:
                        k = yaml.safe_load(f)
                    version = k.get("version", "?")
                    durch   = k.get("erstelltDurch", "manuell")
                    datum   = k.get("erstelltAm", "—")
                    ki      = k.get("konfidenz")
                    score   = str(ki.get("score", "—")) if isinstance(ki, dict) else "—"
                except Exception:
                    version, durch, datum, score = "?", "?", "?", "?"
                print(f"  {p.stem:<30} {version:<10} {score:<8} {durch:<10} {datum}")
        else:
            print("  (keine aktiven Konfigs)")

    pending = sorted(PENDING_DIR.glob("*.yaml"))
    if pending:
        print(f"\nZUR REVIEW ({len(pending)} ausstehend)")
        print("─" * 70)
        print(f"{'Beruf':<35} {'Score':<8} {'Begründung'}")
        for p in pending:
            try:
                with open(p, encoding="utf-8") as f:
                    k = yaml.safe_load(f)
                ki          = k.get("konfidenz") or {}
                score       = str(ki.get("score", "?")) if isinstance(ki, dict) else "?"
                begruendung = str(ki.get("begruendung", "")).strip()[:50]
            except Exception:
                score, begruendung = "?", "?"
            beruf_name = p.stem.replace(".review", "")
            print(f"  {beruf_name:<33} {score:<8} {begruendung}")
        print()
        print("  Freigeben: python -m api.run_pipeline --approve-config {beruf}")
        print("  Ablehnen:  python -m api.run_pipeline --reject-config  {beruf}")
    elif nur_pending:
        print("\n  (keine Konfigs zur Review)")
    print()


if __name__ == "__main__":
    sys.exit(main())
