from __future__ import annotations

from dataclasses import dataclass, field

from .errors import InvalidLimit, NodeMissing
from .graph import Graph
from .traversal import bfs

# ---------------------------------------------------------------------------
# Regla de negocio de la propuesta comercial (ver docs/decisiones.md, F3).
#
# Qué se recomienda, dado un producto de interés (el "origen"):
#
#   1. Candidatos = productos alcanzables con BFS hasta 2 saltos.
#      - 1 salto  -> "directo": se compra junto con el origen.
#      - 2 saltos -> "indirecto": se compra junto con algo que sí acompaña
#        al origen. Más lejos que eso NO se recomienda (3+ saltos es casi
#        todo el catálogo, no una relación demostrable).
#   2. Fuerza de la relación:
#      - directo   = peso de la arista origen-candidato.
#      - indirecto = min(peso origen-puente, peso puente-candidato): una
#        cadena es tan fuerte como su eslabón más débil. Si hay varios
#        puentes se toma el más fuerte; el "respaldo" es cuántos puentes
#        cumplen el umbral del punto 3.
#   3. Filtro: un indirecto solo entra si su fuerza >= MIN_INDIRECT_STRENGTH
#      ("frecuente" o más en ambos eslabones); los puentes más débiles se
#      descartan. Un directo siempre entra: tiene
#      una compra conjunta registrada con el origen.
#   4. Orden: primero los directos, luego los indirectos; dentro de cada
#      grupo, mayor fuerza, luego más respaldo, luego id (determinista).
#   5. Nunca se recomienda el propio origen, ni nada fuera de los candidatos,
#      ni se rellena la lista si hay pocos: si no hay relación, no hay
#      recomendación.
# ---------------------------------------------------------------------------
RECOMMEND_DEPTH = 2
MIN_INDIRECT_STRENGTH = 1.5
DEFAULT_LIMIT = 5
MAX_LIMIT = 10

# Escala del peso (ver comentario de seed.sql): 1.0 esperable, 1.5-2.0
# frecuente, 2.5-3.0 casi siempre juntos.
STRONG = 2.5
FREQUENT = 1.5


def strength_label(strength: float) -> str:
    if strength >= STRONG:
        return "Casi siempre juntos"
    if strength >= FREQUENT:
        return "Frecuente"
    return "Ocasional"


@dataclass
class Bridge:
    """Producto intermedio que conecta el origen con un candidato indirecto."""

    id: str
    strength: float  # min(peso origen-puente, peso puente-candidato)


@dataclass
class Recommendation:
    id: str
    kind: str  # "direct" | "indirect"
    strength: float
    bridges: list[Bridge] = field(default_factory=list)  # vacío si es directo

    @property
    def support(self) -> int:
        """Cuántas rutas independientes respaldan la recomendación."""
        return 1 if self.kind == "direct" else len(self.bridges)


@dataclass
class RecommendResult:
    origin: str
    isolated: bool
    recommendations: list[Recommendation]  # ya ordenadas y recortadas a `limit`
    total_candidates: int                  # elegibles antes de recortar


def recommend(graph: Graph, origin: str, limit: int = DEFAULT_LIMIT) -> RecommendResult:
    """Propuesta comercial explicable para `origin` según la regla de arriba.

    Complejidad: el BFS es O(V + E) acotado al radio 2; calcular los puentes
    recorre los vecinos de los vecinos del origen, O(sum deg(v)) <= O(E).
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_LIMIT:
        raise InvalidLimit(limit, MAX_LIMIT)
    if not graph.has_node(origin):
        raise NodeMissing(origin)

    direct = graph.neighbors(origin)
    if not direct:
        return RecommendResult(origin=origin, isolated=True, recommendations=[], total_candidates=0)

    reached = bfs(graph, origin, RECOMMEND_DEPTH).reached
    candidates: list[Recommendation] = []

    for r in reached:
        if r.level == 1:
            candidates.append(Recommendation(id=r.id, kind="direct", strength=r.weight))
            continue
        # Nivel 2: buscar todos los puentes (vecinos directos del origen que
        # también son vecinos del candidato).
        bridges = [
            Bridge(id=m, strength=min(w_om, graph.neighbors(m)[r.id]))
            for m, w_om in sorted(direct.items())
            if graph.has_edge(m, r.id)
        ]
        # Solo cuentan los puentes que cumplen el umbral: son los que respaldan
        # la recomendación y los únicos que se nombran en la razón.
        bridges = [b for b in bridges if b.strength >= MIN_INDIRECT_STRENGTH]
        if not bridges:
            continue
        bridges.sort(key=lambda b: (-b.strength, b.id))
        candidates.append(
            Recommendation(id=r.id, kind="indirect", strength=bridges[0].strength, bridges=bridges)
        )

    candidates.sort(key=lambda c: (c.kind != "direct", -c.strength, -c.support, c.id))
    return RecommendResult(
        origin=origin,
        isolated=False,
        recommendations=candidates[:limit],
        total_candidates=len(candidates),
    )


if __name__ == "__main__":
    # Traza manual F3 — ejecutable con:
    #   python -m app.core.recommend
    #
    #   leche --(2.5)-- pan --(2.0)-- mermelada
    #     |               \--(1.0)-- jugo
    #   (3.0)
    #     |
    #   cafe --(2.5)-- azucar        jabon --(1.5)-- detergente      sal (aislado)
    g = Graph()
    for p in ("leche", "pan", "mermelada", "jugo", "cafe", "azucar", "jabon", "detergente", "sal"):
        g.add_node(p)
    g.add_edge("leche", "pan", 2.5)
    g.add_edge("pan", "mermelada", 2.0)
    g.add_edge("pan", "jugo", 1.0)
    g.add_edge("leche", "cafe", 3.0)
    g.add_edge("cafe", "azucar", 2.5)
    g.add_edge("jabon", "detergente", 1.5)

    for origin in ("leche", "jabon", "sal"):
        res = recommend(g, origin)
        print(f"Recomendaciones para {origin!r} (aislado={res.isolated}):")
        for i, rec in enumerate(res.recommendations, 1):
            via = ", ".join(f"{b.id}({b.strength})" for b in rec.bridges) or "-"
            print(f"  {i}. {rec.id:<10} {rec.kind:<8} fuerza={rec.strength} respaldo={rec.support} puentes={via}")
        if not res.recommendations:
            print("  (ninguna: no hay relación demostrable)")
        print()
    # Esperado para 'leche':
    #   cafe (directo 3.0), pan (directo 2.5), azucar (indirecto, min(3.0,2.5)=2.5),
    #   mermelada (indirecto, min(2.5,2.0)=2.0). 'jugo' queda fuera: min(2.5,1.0)=1.0 < 1.5.
