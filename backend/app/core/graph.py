from __future__ import annotations

from .errors import EdgeExists, InvalidWeight, NodeExists, NodeMissing, SelfLoop


class Graph:
    """Grafo no dirigido con pesos usando lista de adyacencia.

    Representación interna: ``dict[str, dict[str, float]]`` — por cada nodo,
    un dict ``vecino -> peso``. Al ser no dirigido, una arista ``(a, b, w)``
    se guarda **dos veces**: ``_adj[a][b] = w`` y ``_adj[b][a] = w``.

    Complejidades:
    - ``add_node``, ``add_edge``, ``has_node``, ``has_edge``: O(1).
    - ``neighbors(id)``: O(deg(id)).
    - ``edges()``: O(V + E).
    """

    def __init__(self) -> None:
        self._adj: dict[str, dict[str, float]] = {}

    # ---------- nodos ----------
    def add_node(self, node_id: str) -> None:
        if node_id in self._adj:
            raise NodeExists(node_id)
        self._adj[node_id] = {}

    def remove_node(self, node_id: str) -> None:
        if node_id not in self._adj:
            raise NodeMissing(node_id)
        for neighbor in list(self._adj[node_id]):
            del self._adj[neighbor][node_id]
        del self._adj[node_id]

    def has_node(self, node_id: str) -> bool:
        return node_id in self._adj

    def nodes(self) -> list[str]:
        return list(self._adj)

    # ---------- aristas ----------
    def add_edge(self, a: str, b: str, weight: float = 1.0) -> None:
        if a == b:
            raise SelfLoop(a)
        if a not in self._adj:
            raise NodeMissing(a)
        if b not in self._adj:
            raise NodeMissing(b)
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            raise InvalidWeight(weight)
        if b in self._adj[a]:
            raise EdgeExists(a, b)
        w = float(weight)
        self._adj[a][b] = w
        self._adj[b][a] = w

    def remove_edge(self, a: str, b: str) -> None:
        if a not in self._adj or b not in self._adj[a]:
            raise NodeMissing(a if a not in self._adj else b)
        del self._adj[a][b]
        del self._adj[b][a]

    def has_edge(self, a: str, b: str) -> bool:
        return a in self._adj and b in self._adj[a]

    def neighbors(self, node_id: str) -> dict[str, float]:
        if node_id not in self._adj:
            raise NodeMissing(node_id)
        return dict(self._adj[node_id])

    def edges(self) -> list[tuple[str, str, float]]:
        result: list[tuple[str, str, float]] = []
        for a, nbrs in self._adj.items():
            for b, w in nbrs.items():
                if a < b:
                    result.append((a, b, w))
        return result

    # ---------- introspección ----------
    def __len__(self) -> int:
        return len(self._adj)

    def edge_count(self) -> int:
        return sum(len(v) for v in self._adj.values()) // 2


if __name__ == "__main__":
    # Traza manual F1 (T5) — ejecutable con:
    #   python -m app.core.graph
    # Sirve de evidencia para el pitch y la bitácora.
    g = Graph()
    for p in ("leche", "pan", "cafe", "huevos"):
        g.add_node(p)
    g.add_edge("leche", "pan")
    g.add_edge("cafe", "pan")
    g.add_edge("cafe", "huevos", weight=2.5)
    g.add_edge("leche", "huevos")

    print(f"Nodos ({len(g)}): {g.nodes()}")
    print(f"Aristas ({g.edge_count()}):")
    for a, b, w in g.edges():
        print(f"  {a} -- {b}  (peso {w})")
    print(f"Vecinos de 'cafe': {g.neighbors('cafe')}")
    print(f"has_edge(leche, pan)  -> {g.has_edge('leche', 'pan')}")
    print(f"has_edge(leche, cafe) -> {g.has_edge('leche', 'cafe')}")
