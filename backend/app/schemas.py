from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrippedBase(BaseModel):
    """Base para payloads de entrada: strings se trimman antes de validar."""

    model_config = ConfigDict(str_strip_whitespace=True)


# ---------- Products ----------
class ProductIn(_StrippedBase):
    id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)


class ProductOut(BaseModel):
    id: str
    name: str
    created_at: str


# ---------- Relations ----------
class RelationIn(_StrippedBase):
    a: str = Field(min_length=1, max_length=64)
    b: str = Field(min_length=1, max_length=64)
    weight: float = Field(default=1.0, gt=0)

    @model_validator(mode="after")
    def _no_self_loop(self) -> "RelationIn":
        if self.a == self.b:
            raise ValueError("a and b must be different (no self-loops)")
        return self


class RelationOut(BaseModel):
    a: str
    b: str
    weight: float


# ---------- Network ----------
class NodeInfo(BaseModel):
    id: str
    name: str


class EdgeInfo(BaseModel):
    a: str
    b: str
    weight: float


class NetworkOut(BaseModel):
    nodes: list[NodeInfo]
    edges: list[EdgeInfo]


# ---------- Exploración (F2) ----------
class ReachedOut(BaseModel):
    id: str
    name: str
    level: int
    via: str
    weight: float


class TraceStepOut(BaseModel):
    step: int
    node: str
    level: int
    discovered: list[str]
    already_seen: list[str]
    expanded: bool


class ExploreOut(BaseModel):
    origin: NodeInfo
    depth: int
    max_depth: int
    isolated: bool
    truncated: bool
    reached: list[ReachedOut]
    trace: list[TraceStepOut]
    message: str


class ComponentOut(BaseModel):
    index: int
    size: int
    isolated: bool
    products: list[NodeInfo]


class ComponentsOut(BaseModel):
    count: int
    components: list[ComponentOut]
    message: str


# ---------- Propuesta comercial (F3) ----------
class RecommendationOut(BaseModel):
    rank: int
    product: NodeInfo
    kind: str                 # "direct" | "indirect"
    strength: float           # fuerza de la relación (ver core/recommend.py)
    strength_label: str       # "Casi siempre juntos" | "Frecuente" | "Ocasional"
    support: int              # rutas que respaldan la recomendación
    via: list[NodeInfo]       # productos puente (vacío si es directo)
    reason: str               # explicación en lenguaje de negocio


class RecommendationsOut(BaseModel):
    origin: NodeInfo
    status: str               # "ok" | "isolated"
    limit: int
    total_candidates: int
    recommendations: list[RecommendationOut]
    message: str
    rule: str                 # regla aplicada, en lenguaje de negocio
