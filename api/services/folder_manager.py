"""M1-01: Ordnerstruktur automatisch anlegen."""
from pathlib import Path
from api.config import (
    DATA_DIR, INPUT_DIR, ARCHIVE_DIR, ERROR_DIR,
    OUTPUT_DIR, CONFIG_DIR, PENDING_DIR, REPORTS_DIR,
)

REQUIRED_DIRS = [
    INPUT_DIR,
    ARCHIVE_DIR,
    ERROR_DIR,
    OUTPUT_DIR,
    CONFIG_DIR,
    PENDING_DIR,
    CONFIG_DIR / "archiv",
    CONFIG_DIR / "clustering",
    REPORTS_DIR,
]


def ensure_folder_structure() -> None:
    """Legt alle benötigten Ordner an, falls sie nicht existieren."""
    created = []
    for d in REQUIRED_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)

    if created:
        for d in created:
            print(f"  Ordner angelegt: {d.relative_to(DATA_DIR.parent)}")

    print("Ordnerstruktur bereit [OK]")
