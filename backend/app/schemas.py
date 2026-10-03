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
