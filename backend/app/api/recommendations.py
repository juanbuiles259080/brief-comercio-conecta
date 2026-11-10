import sqlite3

from fastapi import APIRouter, Depends, Query

from app.core.graph import Graph
from app.core.recommend import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Recommendation,
    recommend,
    strength_label,
)
from app.repository import products_repo
from app.schemas import NodeInfo, RecommendationOut, RecommendationsOut

from .deps import get_conn, get_graph

router = APIRouter(tags=["recommendations"])

RULE = (
    "Se proponen primero los productos que se compran junto con el elegido y, "
    "después, los que acompañan a esos productos, solo si ambos vínculos son "
    "frecuentes. Se ordenan por fuerza del vínculo. Nunca se completa la lista "
    "con productos sin relación demostrable."
)

_FREQ_PHRASE = {
    "Casi siempre juntos": "casi siempre",
    "Frecuente": "con frecuencia",
    "Ocasional": "de vez en cuando",
}


def _join(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " y " + names[-1]


def _reason(rec: Recommendation, label: str, origin: str, names: dict[str, str]) -> str:
    freq = _FREQ_PHRASE[label]
    if rec.kind == "direct":
        return f"Se compra junto con {origin} {freq}."
    bridge_names = [names.get(b.id, b.id) for b in rec.bridges]
    verb = "acompaña" if len(bridge_names) == 1 else "acompañan"
    # Frase válida para todos los puentes nombrados: usa el más débil de ellos.
    bridge_freq = _FREQ_PHRASE[strength_label(min(b.strength for b in rec.bridges))]
    return (
        f"No se registra junto con {origin}, pero sí con {_join(bridge_names)}, "
        f"que {verb} a {origin} {bridge_freq}."
    )


@router.get("/recommendations/{product_id}", response_model=RecommendationsOut)
def get_recommendations(
    product_id: str,
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description="Máximo de productos a proponer.",
    ),
    conn: sqlite3.Connection = Depends(get_conn),
    graph: Graph = Depends(get_graph),
) -> RecommendationsOut:
    """Propuesta explicable para `product_id` (regla en `core/recommend.py`)."""
    result = recommend(graph, product_id, limit)  # NodeMissing -> 404
    names = {p["id"]: p["name"] for p in products_repo.list_all(conn)}
    origin_name = names.get(product_id, product_id)

    items: list[RecommendationOut] = []
    for i, rec in enumerate(result.recommendations, start=1):
        label = strength_label(rec.strength)
        items.append(
            RecommendationOut(
                rank=i,
                product=NodeInfo(id=rec.id, name=names.get(rec.id, rec.id)),
                kind=rec.kind,
                strength=rec.strength,
                strength_label=label,
                support=rec.support,
                via=[NodeInfo(id=b.id, name=names.get(b.id, b.id)) for b in rec.bridges],
                reason=_reason(rec, label, origin_name, names),
            )
        )

    if result.isolated:
        status = "isolated"
        message = (
            f"Aún no hay compras conjuntas registradas para {origin_name}, "
            "así que no se propone ningún producto."
        )
    else:
        status = "ok"
        n = len(items)
        message = f"{n} {'producto' if n == 1 else 'productos'} con relación demostrable con {origin_name}."
        if n < limit and result.total_candidates == n:
            message += " No hay más productos con relación suficiente; la lista no se completa con otros."
        elif result.total_candidates > n:
            message += f" Hay {result.total_candidates - n} más con relación suficiente que no se muestran."

    return RecommendationsOut(
        origin=NodeInfo(id=product_id, name=origin_name),
        status=status,
        limit=limit,
        total_candidates=result.total_candidates,
        recommendations=items,
        message=message,
        rule=RULE,
    )
