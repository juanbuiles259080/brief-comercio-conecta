from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import network, products, relations
from app.core.errors import (
    EdgeExists,
    GraphError,
    InvalidWeight,
    NodeExists,
    NodeMissing,
    SelfLoop,
)
from app.config import SKIP_SEED
from app.repository import hydrate_graph
from app.repository.db import get_connection, init_schema, is_empty, load_seed

_STATUS_BY_ERROR: dict[type[GraphError], int] = {
    NodeExists: 409,
    EdgeExists: 409,
    NodeMissing: 404,
    InvalidWeight: 400,
    SelfLoop: 400,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_connection()
    init_schema(conn)
    if is_empty(conn) and not SKIP_SEED:
        load_seed(conn)
    app.state.conn = conn
    app.state.graph = hydrate_graph(conn)
    yield
    conn.close()


app = FastAPI(
    title="ComercioConecta API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(GraphError)
async def _graph_error_handler(request: Request, exc: GraphError) -> JSONResponse:
    status_code = _STATUS_BY_ERROR.get(type(exc), 500)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


app.include_router(products.router)
app.include_router(relations.router)
app.include_router(network.router)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "nodes": len(app.state.graph),
        "edges": app.state.graph.edge_count(),
    }
