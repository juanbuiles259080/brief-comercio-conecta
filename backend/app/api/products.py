import sqlite3

from fastapi import APIRouter, Depends, status

from app.core.graph import Graph
from app.repository import products_repo
from app.schemas import ProductIn, ProductOut

from .deps import get_conn, get_graph

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductIn,
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> dict:
    row = products_repo.insert(conn, payload.id, payload.name)
    graph.add_node(payload.id)
    return row


@router.get("", response_model=list[ProductOut])
def list_products(conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return products_repo.list_all(conn)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: str,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    return products_repo.get(conn, product_id)
