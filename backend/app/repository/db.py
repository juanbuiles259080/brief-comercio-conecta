import sqlite3
from pathlib import Path

from app.config import DATA_DIR, DB_PATH, SEED_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relations (
    a      TEXT NOT NULL,
    b      TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (a, b),
    FOREIGN KEY (a) REFERENCES products(id),
    FOREIGN KEY (b) REFERENCES products(id),
    CHECK (weight > 0),
    CHECK (a < b)
);
"""


def get_connection(path: Path | str | None = None) -> sqlite3.Connection:
    """Abre una conexión SQLite con `foreign_keys` activo y filas tipo dict."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Crea las tablas si no existen. Idempotente."""
    conn.executescript(SCHEMA)
    conn.commit()


def is_empty(conn: sqlite3.Connection) -> bool:
    """True si todavía no hay productos cargados."""
    row = conn.execute("SELECT COUNT(*) FROM products").fetchone()
    return row[0] == 0


def load_seed(conn: sqlite3.Connection, path: Path | str | None = None) -> None:
    """Ejecuta el script de seed. Idempotente gracias a INSERT OR IGNORE."""
    seed_path = Path(path) if path else SEED_PATH
    sql = seed_path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
