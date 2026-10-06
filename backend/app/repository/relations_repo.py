import sqlite3

from app.core.errors import EdgeExists, InvalidWeight, NodeMissing, SelfLoop


def _normalize(a: str, b: str) -> tuple[str, str]:
    """Canonicaliza el par (a,b) para un grafo no dirigido: siempre `a < b`."""
    return (a, b) if a < b else (b, a)


def insert(
    conn: sqlite3.Connection, a: str, b: str, weight: float = 1.0
) -> dict:
    if a == b:
        raise SelfLoop(a)
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
        raise InvalidWeight(weight)

    lo, hi = _normalize(a, b)
    try:
        with conn:
            conn.execute(
                "INSERT INTO relations (a, b, weight) VALUES (?, ?, ?)",
                (lo, hi, float(weight)),
            )
    except sqlite3.IntegrityError as e:
        msg = str(e)
        if "FOREIGN KEY" in msg:
            # El API debería precheckear existencia; esto es red de seguridad.
            raise NodeMissing(f"{a} or {b}") from e
        if "PRIMARY KEY" in msg or "UNIQUE" in msg:
            raise EdgeExists(a, b) from e
        if "CHECK" in msg:
            # weight > 0 o a < b (no debería porque normalizamos)
            raise InvalidWeight(weight) from e
        raise
    return {"a": lo, "b": hi, "weight": float(weight)}


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT a, b, weight FROM relations ORDER BY a, b"
    ).fetchall()
    return [dict(r) for r in rows]
