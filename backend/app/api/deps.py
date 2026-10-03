import sqlite3

from fastapi import Request

from app.core.graph import Graph


def get_conn(request: Request) -> sqlite3.Connection:
    return request.app.state.conn


def get_graph(request: Request) -> Graph:
    return request.app.state.graph
