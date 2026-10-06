import sqlite3

from fastapi import APIRouter, Depends

from app.core.graph import Graph
from app.repository import products_repo
from app.schemas import EdgeInfo, NetworkOut, NodeInfo

from .deps import get_conn, get_graph

router = APIRouter(tags=["network"])


@router.get("/network", response_model=NetworkOut)
def get_network(
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> NetworkOut:
    """Devuelve nodos (con nombre, desde la DB) y aristas (desde el Graph en RAM)."""
    name_by_id = {p["id"]: p["name"] for p in products_repo.list_all(conn)}
    return NetworkOut(
        nodes=[NodeInfo(id=n, name=name_by_id.get(n, n)) for n in graph.nodes()],
        edges=[EdgeInfo(a=a, b=b, weight=w) for a, b, w in graph.edges()],
    )
