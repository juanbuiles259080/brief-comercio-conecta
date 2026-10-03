import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SEED_PATH = DATA_DIR / "seed.sql"

# Permite override vía env para tests de aceptación (DB temporal).
_env_db = os.environ.get("COMERCIO_DB_PATH")
DB_PATH = Path(_env_db) if _env_db else DATA_DIR / "comercio.db"

# Flag para desactivar el seed inicial (útil en aceptación).
SKIP_SEED = os.environ.get("COMERCIO_SKIP_SEED") == "1"
