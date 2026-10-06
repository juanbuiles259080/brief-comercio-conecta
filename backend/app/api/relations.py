import sqlite3

from fastapi import APIRouter, Depends, status

from app.core.errors import NodeMissing
from app.core.graph import Graph
from app.repository import products_repo, relations_repo
from app.schemas import RelationIn, RelationOut

from .deps import get_conn, get_graph

router = APIRouter(prefix="/relations", tags=["relations"])


@router.post("", response_model=RelationOut, status_code=status.HTTP_201_CREATED)
def create_relation(
    payload: RelationIn,
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> dict:
    # Precheck por separado: si falta uno, el 404 indica cuál.
    if not products_repo.exists(conn, payload.a):
        raise NodeMissing(payload.a)
    if not products_repo.exists(conn, payload.b):
        raise NodeMissing(payload.b)

    row = relations_repo.insert(conn, payload.a, payload.b, payload.weight)
    graph.add_edge(payload.a, payload.b, payload.weight)
    return row


@router.get("", response_model=list[RelationOut])
def list_relations(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return relations_repo.list_all(conn)
