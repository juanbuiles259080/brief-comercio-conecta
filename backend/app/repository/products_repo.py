import sqlite3

from app.core.errors import NodeExists, NodeMissing


def insert(conn: sqlite3.Connection, product_id: str, name: str) -> dict:
    try:
        with conn:
            conn.execute(
                "INSERT INTO products (id, name) VALUES (?, ?)",
                (product_id, name),
            )
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e) or "PRIMARY KEY" in str(e):
            raise NodeExists(product_id) from e
        raise
    return get(conn, product_id)


def get(conn: sqlite3.Connection, product_id: str) -> dict:
    row = conn.execute(
        "SELECT id, name, created_at FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    if row is None:
        raise NodeMissing(product_id)
    return dict(row)


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, name, created_at FROM products ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def exists(conn: sqlite3.Connection, product_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    return row is not None
