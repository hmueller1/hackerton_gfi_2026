"""
Liest alle Einzelseiten aus doc/berufe/pages/ und sortiert sie als
    data/eingang/2026/{beruf-slug}/pruefung.pdf
ein — bereit für die Pipeline.

Duplikate (gleicher Beruf, verschiedene Fachrichtungen) bekommen das
Fachrichtungs-Kürzel als Suffix, z.B.:
    kunststoff-und-kautschuktechnologe-bauteile
    kunststoff-und-kautschuktechnologe-formteile

Aufruf: python import_pages.py [--dry-run]
"""
import re
import shutil
import sys
from pathlib import Path

import pdfplumber

PAGES_DIR = Path("doc/berufe/pages")
EINGANG   = Path("data/eingang")
JAHR      = 2026
DRY_RUN   = "--dry-run" in sys.argv


def _slug(name: str) -> str:
    """Normalisiert einen Namen zu einem dateisystem-sicheren Slug."""
    name = re.sub(r"\(.*?\)", "", name)          # (4010, 4011, ...) entfernen
    name = re.sub(r"/-\w*", "", name)            # /-in, /-in/- entfernen
    name = (name
            .replace("ä", "ae").replace("Ä", "ae")
            .replace("ö", "oe").replace("Ö", "oe")
            .replace("ü", "ue").replace("Ü", "ue")
            .replace("ß", "ss"))
    name = re.sub(r"[,;/\\]", " ", name)
    name = re.sub(r"[^a-zA-Z0-9\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"-{2,}", "-", name)
    return name.lower().strip("-")


def _fachrichtung(lines: list[str]) -> str | None:
    """
    Extrahiert Fachrichtung aus Kürzel-Zeile (3. nicht-leere Zeile).
    Beispiel: 'KTBT Bauteile (1975)' -> 'Bauteile'
              'BIOL (Änd.-VO ...)' -> None (kein Fachrichtungsname)
    """
    # Suche Zeile mit Kürzel-Muster: 2-5 Großbuchstaben gefolgt von Text
    for line in lines[2:5]:
        m = re.match(r"^[A-Z]{2,6}\s+([A-Za-zÄÖÜäöüß][\w\s-]{2,}?)(?:\s*\(.*)?$", line)
        if m:
            teil = m.group(1).strip()
            # Nicht "Teil" als Fachrichtung werten
            if teil.lower().startswith("teil"):
                return None
            return teil
    return None


def extract_info(pdf_path: Path) -> dict | None:
    """Liest Beruf-Name und Fachrichtung aus einer Seite."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = pdf.pages[0].extract_text() or ""
    except Exception as e:
        print(f"  [FEHLER] {pdf_path.name}: {e}")
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    beruf_raw = None
    beruf_idx = None
    for i, l in enumerate(lines):
        m = re.search(r"Ausbildungsberuf:\s*(.*)", l)
        if m:
            inline = m.group(1).strip()
            if inline:
                beruf_raw = inline
            elif i + 1 < len(lines):
                # Name steht in der Folgezeile (ggf. mehrere, durch Komma getrennt)
                beruf_raw = lines[i + 1]
                beruf_idx = i + 1
            break

    if not beruf_raw:
        return None

    fachrichtung = _fachrichtung(lines)
    return {"beruf_raw": beruf_raw, "fachrichtung": fachrichtung}


def main():
    pages = sorted(
        PAGES_DIR.glob("*.pdf"),
        key=lambda p: int(re.search(r"_(\d+)\.pdf$", p.name).group(1))
    )

    print(f"Gefunden: {len(pages)} Seiten in {PAGES_DIR}")
    print(f"Ziel:     {EINGANG}/{JAHR}/{{beruf}}/pruefung.pdf")
    if DRY_RUN:
        print("MODUS:    --dry-run (keine Dateien werden kopiert)\n")
    else:
        print()

    ok = fehler = dup = 0
    # beruf_base_slug -> list of (page_path, fachrichtung)
    gruppen: dict[str, list[tuple[Path, str | None]]] = {}

    # Erst alle Seiten lesen und gruppieren
    infos: list[tuple[Path, dict | None]] = []
    for page in pages:
        info = extract_info(page)
        infos.append((page, info))
        if info:
            base = _slug(info["beruf_raw"])
            gruppen.setdefault(base, []).append((page, info["fachrichtung"]))

    # Nun Slugs final vergeben
    slug_map: dict[Path, str] = {}
    for base, eintraege in gruppen.items():
        if len(eintraege) == 1:
            slug_map[eintraege[0][0]] = base
        else:
            # Mehrere Seiten für denselben Beruf -> Fachrichtung als Suffix
            seen_fach: dict[str, int] = {}
            for page, fach in eintraege:
                if fach:
                    fach_slug = _slug(fach)
                    candidate = f"{base}-{fach_slug}"
                else:
                    candidate = base
                # Wenn trotzdem noch Dopplung: Nummer anhängen
                if candidate in seen_fach:
                    seen_fach[candidate] += 1
                    candidate = f"{candidate}-{seen_fach[candidate]}"
                else:
                    seen_fach[candidate] = 1
                slug_map[page] = candidate

    # Ausgabe und ggf. Kopieren
    used_slugs: dict[str, Path] = {}
    for page, info in infos:
        if info is None:
            print(f"  [SKIP]  {page.name} -- kein 'Ausbildungsberuf:' gefunden")
            fehler += 1
            continue

        slug = slug_map.get(page)
        if not slug:
            fehler += 1
            continue

        if slug in used_slugs:
            print(f"  [DUP]   {page.name} -> {slug} (bereits: {used_slugs[slug].name})")
            dup += 1
            continue

        used_slugs[slug] = page

        fach_label = f"  [{info['fachrichtung']}]" if info["fachrichtung"] else ""
        print(f"  [OK]    {page.name:40s} -> {slug}{fach_label}")

        if not DRY_RUN:
            ziel_dir = EINGANG / str(JAHR) / slug
            ziel_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(page, ziel_dir / "pruefung.pdf")

        ok += 1

    print(f"\nFertig: {ok} kopiert, {dup} Duplikate, {fehler} Fehler")
    if DRY_RUN:
        print("(dry-run -- keine Dateien veraendert)")


if __name__ == "__main__":
    main()
