from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .errors import InvalidDepth, NodeMissing
from .graph import Graph

# Límite de negocio para la exploración (ver docs/decisiones.md, F2).
#   1 = "se compran juntos" (relación directa)
#   2 = "complemento del complemento" (todavía explicable al encargado)
#   3 = tope duro. Con el seed (24 productos alcanzables como máximo), la
#       profundidad 3 ya alcanza 14-19 productos (58-79 %), casi todo el
#       grupo de comestibles; más allá deja de ser una relación con sentido
#       comercial.
DEFAULT_DEPTH = 2
MAX_DEPTH = 3


@dataclass
class Reached:
    """Un producto alcanzado por el BFS."""

    id: str
    level: int          # distancia en saltos desde el origen
    via: str            # nodo desde el que se descubrió (padre en el árbol BFS)
    weight: float       # peso de la arista via -> id


@dataclass
class TraceStep:
    """Un paso de la traza: se saca `node` de la cola y se miran sus vecinos."""

    step: int
    node: str
    level: int
    discovered: list[str] = field(default_factory=list)      # nuevos, se encolan
    already_seen: list[str] = field(default_factory=list)    # ya visitados, se ignoran
    expanded: bool = True   # False si el nodo está en el límite y no se expande


@dataclass
class BfsResult:
    origin: str
    depth: int
    reached: list[Reached]
    trace: list[TraceStep]
    truncated: bool         # True si quedaron vecinos sin explorar por el límite


def bfs(graph: Graph, origin: str, depth: int = DEFAULT_DEPTH) -> BfsResult:
    """BFS propio desde `origin` hasta `depth` saltos.

    Devuelve los productos alcanzados (sin incluir el origen), cada uno con su
    nivel y el nodo por el que se llegó, y la traza paso a paso del recorrido.

    Los vecinos se recorren en orden alfabético para que la traza sea
    determinista y se pueda reproducir a mano.

    Complejidad: O(V + E) en el peor caso; con límite de profundidad solo se
    tocan los nodos y aristas dentro del radio `depth`.
    """
    if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= MAX_DEPTH:
        raise InvalidDepth(depth, MAX_DEPTH)
    if not graph.has_node(origin):
        raise NodeMissing(origin)

    level_of: dict[str, int] = {origin: 0}
    queue: deque[str] = deque([origin])
    reached: list[Reached] = []
    trace: list[TraceStep] = []
    truncated = False

    while queue:
        node = queue.popleft()
        level = level_of[node]
        step = TraceStep(step=len(trace) + 1, node=node, level=level)
        trace.append(step)

        neighbors = graph.neighbors(node)
        if level == depth:
            # Nodo en el borde del radio: se visita pero no se expande.
            step.expanded = False
            if any(n not in level_of for n in neighbors):
                truncated = True
            continue

        for nbr in sorted(neighbors):
            if nbr in level_of:
                step.already_seen.append(nbr)
                continue
            level_of[nbr] = level + 1
            step.discovered.append(nbr)
            reached.append(Reached(id=nbr, level=level + 1, via=node, weight=neighbors[nbr]))
            queue.append(nbr)

    return BfsResult(origin=origin, depth=depth, reached=reached, trace=trace, truncated=truncated)


def connected_components(graph: Graph) -> list[list[str]]:
    """Componentes conexos con BFS repetido sobre los nodos no visitados.

    Cada componente se devuelve ordenado alfabéticamente; la lista de
    componentes va de mayor a menor tamaño (empate: por su primer id).

    Complejidad: O(V + E) — cada nodo y cada arista se procesa una vez.
    """
    seen: set[str] = set()
    components: list[list[str]] = []

    for start in sorted(graph.nodes()):
        if start in seen:
            continue
        seen.add(start)
        queue: deque[str] = deque([start])
        members: list[str] = []
        while queue:
            node = queue.popleft()
            members.append(node)
            for nbr in graph.neighbors(node):
                if nbr not in seen:
                    seen.add(nbr)
                    queue.append(nbr)
        components.append(sorted(members))

    components.sort(key=lambda c: (-len(c), c[0]))
    return components


def component_of(graph: Graph, node_id: str) -> list[str]:
    """Componente conexo que contiene a `node_id` (incluido)."""
    if not graph.has_node(node_id):
        raise NodeMissing(node_id)
    for comp in connected_components(graph):
        if node_id in comp:
            return comp
    return [node_id]  # inalcanzable: todo nodo pertenece a algún componente


if __name__ == "__main__":
    # Traza manual F2 — ejecutable con:
    #   python -m app.core.traversal
    #
    #   leche -- pan -- mermelada        jabon -- detergente      sal (aislado)
    #     |
    #   cafe -- azucar
    g = Graph()
    for p in ("leche", "pan", "mermelada", "cafe", "azucar", "jabon", "detergente", "sal"):
        g.add_node(p)
    g.add_edge("leche", "pan", 2.5)
    g.add_edge("pan", "mermelada", 2.0)
    g.add_edge("leche", "cafe", 3.0)
    g.add_edge("cafe", "azucar", 2.5)
    g.add_edge("jabon", "detergente", 1.5)

    for d in (1, 2):
        r = bfs(g, "leche", d)
        print(f"BFS desde 'leche', profundidad {d} (truncado={r.truncated}):")
        for s in r.trace:
            extra = "" if s.expanded else "  [límite: no se expande]"
            print(f"  paso {s.step}: saco {s.node!r} (nivel {s.level}) "
                  f"-> nuevos {s.discovered}, ya vistos {s.already_seen}{extra}")
        print("  alcanzados:", [(x.id, x.level, f"via {x.via}") for x in r.reached])
        print()

    print("BFS desde 'sal' (aislado):", bfs(g, "sal").reached)
    print("Componentes:", connected_components(g))
    print("Componente de 'jabon':", component_of(g, "jabon"))
