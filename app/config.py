import os
from pathlib import Path

# Data directory for uploads and database
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "seed_library.db"))

# Logging configuration
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "seed_library.log"

# Import limits
MAX_IMPORT_BYTES = int(os.getenv("MAX_IMPORT_BYTES", 5 * 1024 * 1024))  # 5 MB default
ALLOWED_IMPORT_EXTENSIONS = (".xlsx", ".xls")
ALLOWED_IMPORT_CONTENT_TYPES = {
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
