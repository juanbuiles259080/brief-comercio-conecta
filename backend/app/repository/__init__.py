import sqlite3

from app.core.graph import Graph

from . import products_repo, relations_repo


def hydrate_graph(conn: sqlite3.Connection) -> Graph:
    """Construye un Graph en RAM leyendo todo lo persistido en SQLite.

    Se corre una sola vez al startup. Después, cada mutación debe sincronizar
    SQL ↔ Graph (ver patrón en `docs/decisiones.md`).
    """
    graph = Graph()
    for p in products_repo.list_all(conn):
        graph.add_node(p["id"])
    for r in relations_repo.list_all(conn):
        graph.add_edge(r["a"], r["b"], r["weight"])
    return graph
