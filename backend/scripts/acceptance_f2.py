"""Script de aceptación - Feature 2 ComercioConecta (exploración de relaciones).

Cubre lo que pide el brief para F2 y la guía:
  - red vacía (sin productos ni grupos)
  - escenario normal: BFS con límite de profundidad y traza, grupos conexos
  - producto aislado
  - producto inexistente
  - datos inválidos: profundidad fuera de rango o con formato incorrecto

Reutiliza el arranque de servidor y el formato de salida de `acceptance.py`
(F1): levanta su propio `uvicorn` contra una DB temporal sin seed.

Uso (desde backend/):
    python scripts/acceptance_f2.py
"""
from __future__ import annotations

import sys

import requests

from acceptance import BASE, _detail, _results, check, section, start_server, stop_server

# Red de prueba (pesos entre paréntesis):
#
#   leche --(2.5)-- pan --(2.0)-- mermelada      jabon --(1.5)-- detergente
#     |
#   (3.0)                                        sal  (aislado)
#     |
#   cafe --(2.5)-- azucar --(1.0)-- yogur
#
PRODUCTS = [
    ("leche", "Leche"), ("pan", "Pan"), ("mermelada", "Mermelada"),
    ("cafe", "Cafe"), ("azucar", "Azucar"), ("yogur", "Yogur"),
    ("jabon", "Jabon"), ("detergente", "Detergente"), ("sal", "Sal"),
]
RELATIONS = [
    ("leche", "pan", 2.5), ("pan", "mermelada", 2.0), ("leche", "cafe", 3.0),
    ("cafe", "azucar", 2.5), ("azucar", "yogur", 1.0), ("jabon", "detergente", 1.5),
]


def _levels(body: dict) -> dict[str, int]:
    return {r["id"]: r["level"] for r in body.get("reached", [])}


def run_scenarios() -> None:
    section("A) RED VACIA")

    r = requests.get(f"{BASE}/components")
    body = r.json()
    check(
        "GET /components con red vacía",
        "status=200, count=0, components=[]",
        f"status={r.status_code}, count={body.get('count')}, components={body.get('components')}",
        r.status_code == 200 and body.get("count") == 0 and body.get("components") == [],
    )

    r = requests.get(f"{BASE}/explore/leche")
    check(
        "GET /explore/leche con red vacía",
        "status=404 (el producto no existe)",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "leche" in _detail(r),
    )

    # Carga de la red de prueba
    for pid, name in PRODUCTS:
        requests.post(f"{BASE}/products", json={"id": pid, "name": name}).raise_for_status()
    for a, b, w in RELATIONS:
        requests.post(f"{BASE}/relations", json={"a": a, "b": b, "weight": w}).raise_for_status()

    section("B) EXPLORACION NORMAL (BFS con límite de profundidad)")

    r = requests.get(f"{BASE}/explore/leche", params={"depth": 1})
    body = r.json()
    check(
        "GET /explore/leche?depth=1 -> solo vecinos directos",
        "status=200, alcanzados {cafe:1, pan:1}, truncated=True",
        f"status={r.status_code}, alcanzados={_levels(body)}, truncated={body.get('truncated')}",
        r.status_code == 200
        and _levels(body) == {"cafe": 1, "pan": 1}
        and body.get("truncated") is True,
    )

    r = requests.get(f"{BASE}/explore/leche")
    body = r.json()
    check(
        "GET /explore/leche (depth por defecto = 2)",
        "status=200, depth=2, alcanzados {cafe:1, pan:1, azucar:2, mermelada:2}",
        f"status={r.status_code}, depth={body.get('depth')}, alcanzados={_levels(body)}",
        r.status_code == 200
        and body.get("depth") == 2
        and _levels(body) == {"cafe": 1, "pan": 1, "azucar": 2, "mermelada": 2},
    )

    via = {x["id"]: x["via"] for x in body.get("reached", [])}
    check(
        "Cada alcanzado indica por qué producto se llegó",
        "via: azucar<-cafe, mermelada<-pan, cafe<-leche",
        f"via={via}",
        via.get("azucar") == "cafe" and via.get("mermelada") == "pan" and via.get("cafe") == "leche",
    )

    check(
        "El origen no aparece entre los alcanzados",
        "'leche' no está en reached",
        f"ids={[x['id'] for x in body.get('reached', [])]}",
        "leche" not in _levels(body),
    )

    trace = body.get("trace", [])
    order = [s["node"] for s in trace]
    check(
        "Traza BFS en orden por niveles (vecinos en orden alfabético)",
        "orden=['leche','cafe','pan','azucar','mermelada']",
        f"orden={order}",
        order == ["leche", "cafe", "pan", "azucar", "mermelada"],
    )

    check(
        "Nodos en el límite no se expanden (yogur queda fuera)",
        "azucar.expanded=False, 'yogur' no alcanzado, truncated=True",
        f"expanded={[(s['node'], s['expanded']) for s in trace if s['level'] == 2]}, "
        f"truncated={body.get('truncated')}",
        all(not s["expanded"] for s in trace if s["level"] == 2)
        and "yogur" not in _levels(body)
        and body.get("truncated") is True,
    )

    r = requests.get(f"{BASE}/explore/leche", params={"depth": 3})
    body = r.json()
    check(
        "GET /explore/leche?depth=3 -> alcanza yogur, nunca el grupo higiene",
        "yogur nivel 3; jabon/detergente/sal ausentes; truncated=False",
        f"alcanzados={_levels(body)}, truncated={body.get('truncated')}",
        r.status_code == 200
        and _levels(body).get("yogur") == 3
        and not {"jabon", "detergente", "sal"} & set(_levels(body))
        and body.get("truncated") is False,
    )

    section("C) GRUPOS / COMPONENTES CONEXOS")

    r = requests.get(f"{BASE}/components")
    body = r.json()
    groups = [[p["id"] for p in c["products"]] for c in body.get("components", [])]
    check(
        "GET /components separa los 3 grupos (mayor a menor)",
        "count=3: [comestibles(6), higiene(2), sal(1)]",
        f"status={r.status_code}, count={body.get('count')}, grupos={groups}",
        r.status_code == 200
        and body.get("count") == 3
        and groups == [
            ["azucar", "cafe", "leche", "mermelada", "pan", "yogur"],
            ["detergente", "jabon"],
            ["sal"],
        ],
    )

    r = requests.get(f"{BASE}/components/jabon")
    body = r.json()
    check(
        "GET /components/jabon -> su grupo es solo higiene",
        "status=200, size=2, products=[detergente, jabon]",
        f"status={r.status_code}, size={body.get('size')}, "
        f"products={[p['id'] for p in body.get('products', [])]}",
        r.status_code == 200
        and body.get("size") == 2
        and [p["id"] for p in body.get("products", [])] == ["detergente", "jabon"],
    )

    section("D) PRODUCTO AISLADO")

    r = requests.get(f"{BASE}/explore/sal")
    body = r.json()
    check(
        "GET /explore/sal -> aislado, sin inventar relacionados",
        "status=200, isolated=True, reached=[], mensaje 'aislado'",
        f"status={r.status_code}, isolated={body.get('isolated')}, reached={body.get('reached')}, "
        f"message={body.get('message')!r}",
        r.status_code == 200
        and body.get("isolated") is True
        and body.get("reached") == []
        and "aislado" in body.get("message", ""),
    )

    r = requests.get(f"{BASE}/components/sal")
    body = r.json()
    check(
        "GET /components/sal -> grupo de un solo producto",
        "status=200, size=1, isolated=True",
        f"status={r.status_code}, size={body.get('size')}, isolated={body.get('isolated')}",
        r.status_code == 200 and body.get("size") == 1 and body.get("isolated") is True,
    )

    section("E) PRODUCTO INEXISTENTE")

    r = requests.get(f"{BASE}/explore/fantasma")
    check(
        "GET /explore/fantasma",
        "status=404, detail menciona 'fantasma'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "fantasma" in _detail(r),
    )

    r = requests.get(f"{BASE}/components/fantasma")
    check(
        "GET /components/fantasma",
        "status=404, detail menciona 'fantasma'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "fantasma" in _detail(r),
    )

    section("F) DATOS INVALIDOS: profundidad")

    for value, why in (("0", "menor a 1"), ("4", "mayor al tope de negocio 3"),
                       ("-1", "negativa"), ("dos", "no es entero"), ("1.5", "decimal")):
        r = requests.get(f"{BASE}/explore/leche", params={"depth": value})
        check(
            f"GET /explore/leche?depth={value} ({why})",
            "status=422",
            f"status={r.status_code}",
            r.status_code == 422,
        )


def main() -> int:
    section("SCRIPT DE ACEPTACION - F2 ComercioConecta")
    print(f"  Servidor: {BASE}  (DB temporal, seed desactivado)")
    print("  Levantando uvicorn...")

    proc, tmp_db = start_server()
    print("  Listo.")
    try:
        run_scenarios()
    finally:
        stop_server(proc, tmp_db)

    section("RESUMEN")
    passed = sum(1 for _, s in _results if s == "PASS")
    total = len(_results)
    print(f"  Resultado: {passed}/{total} PASS")
    if passed != total:
        print("  Fallaron:")
        for label, status in _results:
            if status == "FAIL":
                print(f"    - {label}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
