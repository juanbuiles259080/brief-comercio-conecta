class GraphError(Exception):
    """Base de las excepciones de dominio del grafo."""


class NodeExists(GraphError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node already exists: {node_id!r}")
        self.node_id = node_id


class NodeMissing(GraphError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node does not exist: {node_id!r}")
        self.node_id = node_id


class EdgeExists(GraphError):
    def __init__(self, a: str, b: str) -> None:
        super().__init__(f"Edge already exists: ({a!r}, {b!r})")
        self.a = a
        self.b = b


class InvalidWeight(GraphError):
    def __init__(self, weight: object) -> None:
        super().__init__(f"Invalid weight: {weight!r} (must be a number > 0)")
        self.weight = weight


class SelfLoop(GraphError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Self-loop not allowed: {node_id!r} with itself")
        self.node_id = node_id
