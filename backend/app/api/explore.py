import sqlite3

from fastapi import APIRouter, Depends, Query

from app.core.graph import Graph
from app.core.traversal import DEFAULT_DEPTH, MAX_DEPTH, bfs, component_of, connected_components
from app.repository import products_repo
from app.schemas import (
    ComponentOut,
    ComponentsOut,
    ExploreOut,
    NodeInfo,
    ReachedOut,
    TraceStepOut,
)

from .deps import get_conn, get_graph

router = APIRouter(tags=["explore"])


def _names(conn: sqlite3.Connection) -> dict[str, str]:
    return {p["id"]: p["name"] for p in products_repo.list_all(conn)}


@router.get("/explore/{product_id}", response_model=ExploreOut)
def explore(
    product_id: str,
    depth: int = Query(
        DEFAULT_DEPTH,
        ge=1,
        le=MAX_DEPTH,
        description="Saltos máximos desde el producto (1 = compra directa).",
    ),
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> ExploreOut:
    """Productos alcanzables desde `product_id` con BFS propio, con traza."""
    result = bfs(graph, product_id, depth)  # NodeMissing -> 404
    names = _names(conn)
    isolated = not graph.neighbors(product_id)

    if isolated:
        message = "Producto aislado: no tiene relaciones de compra conjunta registradas."
    else:
        direct = sum(1 for r in result.reached if r.level == 1)
        message = (
            f"{len(result.reached)} productos relacionados hasta {depth} "
            f"{'salto' if depth == 1 else 'saltos'} ({direct} directos)."
        )
        if result.truncated:
            message += " Hay más productos fuera del límite de profundidad."

    return ExploreOut(
        origin=NodeInfo(id=product_id, name=names.get(product_id, product_id)),
        depth=depth,
        max_depth=MAX_DEPTH,
        isolated=isolated,
        truncated=result.truncated,
        reached=[
            ReachedOut(id=r.id, name=names.get(r.id, r.id), level=r.level, via=r.via, weight=r.weight)
            for r in result.reached
        ],
        trace=[
            TraceStepOut(
                step=s.step,
                node=s.node,
                level=s.level,
                discovered=s.discovered,
                already_seen=s.already_seen,
                expanded=s.expanded,
            )
            for s in result.trace
        ],
        message=message,
    )


def _component_out(index: int, members: list[str], names: dict[str, str]) -> ComponentOut:
    return ComponentOut(
        index=index,
        size=len(members),
        isolated=len(members) == 1,
        products=[NodeInfo(id=m, name=names.get(m, m)) for m in members],
    )


@router.get("/components", response_model=ComponentsOut)
def list_components(
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> ComponentsOut:
    """Grupos de productos conectados entre sí (componentes conexos)."""
    comps = connected_components(graph)
    names = _names(conn)

    if not comps:
        message = "Red vacía: no hay productos cargados."
    else:
        isolated = sum(1 for c in comps if len(c) == 1)
        message = f"{len(comps)} {'grupo' if len(comps) == 1 else 'grupos'} independientes"
        message += f" ({isolated} {'producto aislado' if isolated == 1 else 'productos aislados'})." if isolated else "."

    return ComponentsOut(
        count=len(comps),
        components=[_component_out(i + 1, c, names) for i, c in enumerate(comps)],
        message=message,
    )


@router.get("/components/{product_id}", response_model=ComponentOut)
def get_component(
    product_id: str,
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> ComponentOut:
    """Grupo al que pertenece `product_id`."""
    members = component_of(graph, product_id)  # NodeMissing -> 404
    comps = connected_components(graph)
    return _component_out(comps.index(members) + 1, members, _names(conn))
