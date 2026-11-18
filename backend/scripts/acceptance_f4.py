"""Script de aceptación - Feature 4 ComercioConecta (panel comercial integrado).

Recorre el flujo completo del cliente, de punta a punta, contra la API real:
  analista carga productos y relaciones -> se explora la red -> el encargado
  consulta un producto -> recibe una propuesta explicable.

Cubre los cinco escenarios que pide el brief para F4:
  A) red vacía   B) caso normal   C) producto aislado
  D) producto inexistente   E) dato inválido
y agrega F) los cambios de datos se reflejan en la propuesta.

La diferencia con acceptance_f3.py: aquí se comprueba que carga, exploración y
propuesta son CONSISTENTES entre sí (la propuesta sale de lo explorado, los
productos puente son vecinos directos, todo vive en el mismo grupo).

Uso (desde backend/):
    python scripts/acceptance_f4.py
"""
from __future__ import annotations

import sys

import requests

from acceptance import BASE, _detail, _results, check, section, start_server, stop_server

# Red de prueba (pesos entre paréntesis):
#
#   leche --(2.5)-- pan --(2.0)-- mermelada
#     |               \--(1.0)-- jugo
#   (3.0)
#     |
#   cafe --(2.5)-- azucar        jabon --(1.5)-- detergente      sal (aislado)
PRODUCTS = [
    ("leche", "Leche"), ("pan", "Pan"), ("mermelada", "Mermelada"), ("jugo", "Jugo"),
    ("cafe", "Cafe"), ("azucar", "Azucar"),
    ("jabon", "Jabon"), ("detergente", "Detergente"), ("sal", "Sal"),
]
RELATIONS = [
    ("leche", "pan", 2.5), ("pan", "mermelada", 2.0), ("pan", "jugo", 1.0),
    ("leche", "cafe", 3.0), ("cafe", "azucar", 2.5), ("jabon", "detergente", 1.5),
]


def _rec_ids(body: dict) -> list[str]:
    return [r["product"]["id"] for r in body.get("recommendations", [])]


def _network() -> tuple[int, int]:
    n = requests.get(f"{BASE}/network").json()
    return len(n["nodes"]), len(n["edges"])


def run_scenarios() -> None:
    # ------------------------------------------------------------------
    section("A) RED VACIA")

    r = requests.get(f"{BASE}/network")
    body = r.json()
    check(
        "GET /network sin datos",
        "status=200, nodes=[], edges=[]",
        f"status={r.status_code}, nodes={len(body.get('nodes', []))}, edges={len(body.get('edges', []))}",
        r.status_code == 200 and body.get("nodes") == [] and body.get("edges") == [],
    )

    r = requests.get(f"{BASE}/components")
    body = r.json()
    check(
        "GET /components sin datos",
        "status=200, count=0, mensaje dice 'Red vacía'",
        f"status={r.status_code}, count={body.get('count')}, message={body.get('message')!r}",
        r.status_code == 200 and body.get("count") == 0 and "Red vacía" in body.get("message", ""),
    )

    for path, label in (("/explore/leche", "explorar"), ("/recommendations/leche", "recomendar")):
        r = requests.get(f"{BASE}{path}")
        check(
            f"GET {path} ({label} con red vacía)",
            "status=404, detail menciona 'leche' (no inventa resultados)",
            f"status={r.status_code}, detail={_detail(r)!r}",
            r.status_code == 404 and "leche" in _detail(r),
        )

    # ------------------------------------------------------------------
    section("B) CASO NORMAL: el analista carga, el encargado consulta")

    created = [requests.post(f"{BASE}/products", json={"id": i, "name": n}).status_code for i, n in PRODUCTS]
    check(
        "El analista registra 9 productos",
        "9 respuestas 201",
        f"{created.count(201)} respuestas 201",
        created.count(201) == 9,
    )
    created = [requests.post(f"{BASE}/relations", json={"a": a, "b": b, "weight": w}).status_code for a, b, w in RELATIONS]
    check(
        "El analista registra 6 compras conjuntas",
        "6 respuestas 201",
        f"{created.count(201)} respuestas 201",
        created.count(201) == 6,
    )

    nodes, edges = _network()
    check(
        "La red refleja lo cargado",
        "9 productos y 6 relaciones",
        f"{nodes} productos y {edges} relaciones",
        (nodes, edges) == (9, 6),
    )

    ex = requests.get(f"{BASE}/explore/leche", params={"depth": 2}).json()
    levels = {r["id"]: r["level"] for r in ex.get("reached", [])}
    check(
        "Exploración desde 'leche' (2 saltos)",
        "cafe y pan en nivel 1; azucar, jugo y mermelada en nivel 2",
        f"{dict(sorted(levels.items()))}",
        levels == {"cafe": 1, "pan": 1, "azucar": 2, "jugo": 2, "mermelada": 2},
    )

    rec = requests.get(f"{BASE}/recommendations/leche").json()
    ids = _rec_ids(rec)
    check(
        "Propuesta para 'leche'",
        "[cafe, pan, azucar, mermelada], status='ok'",
        f"ids={ids}, status={rec.get('status')!r}",
        ids == ["cafe", "pan", "azucar", "mermelada"] and rec.get("status") == "ok",
    )

    check(
        "Integración: la propuesta sale de lo explorado",
        "propuesta incluida en lo alcanzado; la diferencia es solo 'jugo' (vínculo débil)",
        f"fuera de la propuesta={sorted(set(levels) - set(ids))}",
        set(ids) <= set(levels) and set(levels) - set(ids) == {"jugo"},
    )

    comp = requests.get(f"{BASE}/components/leche").json()
    members = {p["id"] for p in comp.get("products", [])}
    check(
        "Integración: todo lo recomendado vive en el mismo grupo que 'leche'",
        "propuesta + 'leche' incluidas en el grupo; 'jabon' y 'sal' fuera",
        f"grupo={sorted(members)}",
        set(ids) | {"leche"} <= members and not ({"jabon", "sal"} & members),
    )

    recs = rec.get("recommendations", [])
    direct_ok = all(r["via"] == [] for r in recs if r["kind"] == "direct")
    indirect_ok = all(r["via"] for r in recs if r["kind"] == "indirect")
    check(
        "Cada recomendación trae razón; los indirectos nombran su puente",
        "reason no vacío en todas; via vacío en directos y con datos en indirectos",
        f"razones={sum(1 for r in recs if r['reason'])}/{len(recs)}, directos sin puente={direct_ok}, indirectos con puente={indirect_ok}",
        all(r["reason"] for r in recs) and direct_ok and indirect_ok,
    )

    level1 = {i for i, lv in levels.items() if lv == 1}
    via_ids = {v["id"] for r in recs if r["kind"] == "indirect" for v in r["via"]}
    check(
        "Integración: los productos puente son vecinos directos de 'leche'",
        "todo puente está en el nivel 1 de la exploración",
        f"puentes={sorted(via_ids)}, nivel 1={sorted(level1)}",
        bool(via_ids) and via_ids <= level1,
    )

    groups = requests.get(f"{BASE}/components").json()
    sizes = sorted(c["size"] for c in groups.get("components", []))
    check(
        "Grupos: comestibles, aseo y un producto suelto",
        "3 grupos de tamaños [1, 2, 6]",
        f"{groups.get('count')} grupos, tamaños={sizes}",
        groups.get("count") == 3 and sizes == [1, 2, 6],
    )

    # ------------------------------------------------------------------
    section("C) PRODUCTO AISLADO")

    r = requests.get(f"{BASE}/recommendations/sal")
    body = r.json()
    check(
        "GET /recommendations/sal (sin compras)",
        "status=200, status='isolated', lista vacía, mensaje nombra 'Sal'",
        f"status={r.status_code}, body.status={body.get('status')!r}, recs={body.get('recommendations')}, message={body.get('message')!r}",
        r.status_code == 200 and body.get("status") == "isolated"
        and body.get("recommendations") == [] and "Sal" in body.get("message", ""),
    )

    r = requests.get(f"{BASE}/explore/sal")
    body = r.json()
    check(
        "GET /explore/sal",
        "status=200, isolated=true, reached=[]",
        f"status={r.status_code}, isolated={body.get('isolated')}, reached={body.get('reached')}",
        r.status_code == 200 and body.get("isolated") is True and body.get("reached") == [],
    )

    r = requests.get(f"{BASE}/components/sal")
    body = r.json()
    check(
        "GET /components/sal",
        "status=200, size=1, isolated=true",
        f"status={r.status_code}, size={body.get('size')}, isolated={body.get('isolated')}",
        r.status_code == 200 and body.get("size") == 1 and body.get("isolated") is True,
    )

    # ------------------------------------------------------------------
    section("D) PRODUCTO INEXISTENTE")

    for path in ("/recommendations/fantasma", "/explore/fantasma", "/components/fantasma"):
        r = requests.get(f"{BASE}{path}")
        check(
            f"GET {path}",
            "status=404, detail menciona 'fantasma'",
            f"status={r.status_code}, detail={_detail(r)!r}",
            r.status_code == 404 and "fantasma" in _detail(r),
        )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "fantasma", "weight": 2.0})
    check(
        "Registrar una compra conjunta con un producto que no existe",
        "status=404, detail menciona 'fantasma'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "fantasma" in _detail(r),
    )

    # ------------------------------------------------------------------
    section("E) DATO INVALIDO (al cargar y al consultar)")

    def post(path: str, payload: dict) -> requests.Response:
        return requests.post(f"{BASE}{path}", json=payload)

    cases = [
        ("Producto con nombre vacío", post("/products", {"id": "x1", "name": ""}), 422),
        ("Producto con nombre solo de espacios", post("/products", {"id": "x2", "name": "   "}), 422),
        ("Producto con id repetido", post("/products", {"id": "leche", "name": "Otra leche"}), 409),
        ("Relación con peso 0", post("/relations", {"a": "leche", "b": "sal", "weight": 0}), 422),
        ("Relación con peso negativo", post("/relations", {"a": "leche", "b": "sal", "weight": -1}), 422),
        ("Relación con peso que no es número", post("/relations", {"a": "leche", "b": "sal", "weight": "abc"}), 422),
        ("Relación de un producto consigo mismo", post("/relations", {"a": "leche", "b": "leche", "weight": 1}), 422),
        ("Relación repetida (leche, pan)", post("/relations", {"a": "leche", "b": "pan", "weight": 1}), 409),
        ("Relación repetida al revés (pan, leche)", post("/relations", {"a": "pan", "b": "leche", "weight": 1}), 409),
    ]
    for label, resp, expected in cases:
        check(label, f"status={expected}", f"status={resp.status_code}", resp.status_code == expected)

    for path, param, value, why in (
        ("/explore/leche", "depth", "0", "profundidad menor a 1"),
        ("/explore/leche", "depth", "9", "profundidad sobre el tope"),
        ("/explore/leche", "depth", "dos", "profundidad que no es número"),
        ("/recommendations/leche", "limit", "0", "límite menor a 1"),
        ("/recommendations/leche", "limit", "11", "límite sobre el tope"),
        ("/recommendations/leche", "limit", "tres", "límite que no es número"),
    ):
        r = requests.get(f"{BASE}{path}", params={param: value})
        check(
            f"GET {path}?{param}={value} ({why})",
            "status=422",
            f"status={r.status_code}",
            r.status_code == 422,
        )

    nodes, edges = _network()
    again = _rec_ids(requests.get(f"{BASE}/recommendations/leche").json())
    check(
        "Los datos inválidos no alteran la red ni la propuesta",
        "9 productos, 6 relaciones y la misma propuesta de antes",
        f"{nodes} productos, {edges} relaciones, ids={again}",
        (nodes, edges) == (9, 6) and again == ["cafe", "pan", "azucar", "mermelada"],
    )

    # ------------------------------------------------------------------
    section("F) LOS CAMBIOS DE DATOS SE REFLEJAN EN LA PROPUESTA")

    r = requests.post(f"{BASE}/relations", json={"a": "sal", "b": "pan", "weight": 2.0})
    check(
        "El analista registra sal-pan (2.0)",
        "status=201",
        f"status={r.status_code}",
        r.status_code == 201,
    )

    body = requests.get(f"{BASE}/recommendations/sal").json()
    check(
        "'sal' deja de estar aislado y recibe propuesta",
        "status='ok', ids=[pan, leche, mermelada]",
        f"status={body.get('status')!r}, ids={_rec_ids(body)}",
        body.get("status") == "ok" and _rec_ids(body) == ["pan", "leche", "mermelada"],
    )

    body = requests.get(f"{BASE}/recommendations/leche", params={"limit": 10}).json()
    check(
        "'leche' ahora también propone 'sal' (indirecto por 'pan')",
        "ids=[cafe, pan, azucar, mermelada, sal]",
        f"ids={_rec_ids(body)}",
        _rec_ids(body) == ["cafe", "pan", "azucar", "mermelada", "sal"],
    )

    groups = requests.get(f"{BASE}/components").json()
    sizes = sorted(c["size"] for c in groups.get("components", []))
    check(
        "Los grupos se actualizan: 'sal' se une al de comestibles",
        "2 grupos de tamaños [2, 7]",
        f"{groups.get('count')} grupos, tamaños={sizes}",
        groups.get("count") == 2 and sizes == [2, 7],
    )


def main() -> int:
    section("SCRIPT DE ACEPTACION - F4 ComercioConecta")
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
