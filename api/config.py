"""M1-02: Zentrale Konfiguration — lädt Pfade aus .env oder Umgebungsvariablen."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Basispfad (relativ zum Repo-Root oder absolut)
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()

# Unterordner
INPUT_DIR   = DATA_DIR / "eingang"
ARCHIVE_DIR = DATA_DIR / "archiv"
ERROR_DIR   = DATA_DIR / "fehler"
OUTPUT_DIR  = DATA_DIR / "ausgabe"
CONFIG_DIR  = DATA_DIR / "konfig"
PENDING_DIR = CONFIG_DIR / "pending"
REPORTS_DIR = DATA_DIR / "reports"

# Konfig-Schwellwert für KI-Konfidenz (M2)
KONFIDENZ_SCHWELLWERT = int(os.getenv("KONFIDENZ_SCHWELLWERT", "85"))
