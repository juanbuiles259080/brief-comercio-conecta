"""Script de aceptación - Feature 3 ComercioConecta (propuesta comercial).

Cubre lo que pide el brief para F3 y la guía:
  - red vacía
  - escenario normal: orden, razón y fuerza de cada recomendación
  - regla de filtrado (un vínculo débil no genera recomendación indirecta)
  - red escasa y grupos separados (no se rellena ni se cruza de grupo)
  - producto aislado y producto inexistente
  - datos inválidos: límite fuera de rango o con formato incorrecto
  - la propuesta cambia cuando cambian los datos (SQL <-> grafo sincronizados)

Reutiliza el arranque de servidor y el formato de salida de `acceptance.py`.

Uso (desde backend/):
    python scripts/acceptance_f3.py
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
#
# Regla (core/recommend.py): directos primero; indirectos solo si
# min(peso1, peso2) >= 1.5. Para 'leche' se espera:
#   cafe (directo 3.0), pan (directo 2.5), azucar (indirecto 2.5 via cafe),
#   mermelada (indirecto 2.0 via pan). 'jugo' queda fuera (min = 1.0).
PRODUCTS = [
    ("leche", "Leche"), ("pan", "Pan"), ("mermelada", "Mermelada"), ("jugo", "Jugo"),
    ("cafe", "Cafe"), ("azucar", "Azucar"),
    ("jabon", "Jabon"), ("detergente", "Detergente"), ("sal", "Sal"),
]
RELATIONS = [
    ("leche", "pan", 2.5), ("pan", "mermelada", 2.0), ("pan", "jugo", 1.0),
    ("leche", "cafe", 3.0), ("cafe", "azucar", 2.5), ("jabon", "detergente", 1.5),
]


def _ids(body: dict) -> list[str]:
    return [r["product"]["id"] for r in body.get("recommendations", [])]


def _by_id(body: dict) -> dict[str, dict]:
    return {r["product"]["id"]: r for r in body.get("recommendations", [])}


def run_scenarios() -> None:
    section("A) RED VACIA")

    r = requests.get(f"{BASE}/recommendations/leche")
    check(
        "GET /recommendations/leche con red vacía",
        "status=404 (no hay productos), detail menciona 'leche'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "leche" in _detail(r),
    )

    for pid, name in PRODUCTS:
        requests.post(f"{BASE}/products", json={"id": pid, "name": name})
    for a, b, w in RELATIONS:
        requests.post(f"{BASE}/relations", json={"a": a, "b": b, "weight": w})

    section("B) ESCENARIO NORMAL: propuesta explicable para 'leche'")

    r = requests.get(f"{BASE}/recommendations/leche")
    body = r.json()
    check(
        "GET /recommendations/leche",
        "status=200, status='ok', orden [cafe, pan, azucar, mermelada]",
        f"status={r.status_code}, body.status={body.get('status')!r}, ids={_ids(body)}",
        r.status_code == 200 and body.get("status") == "ok"
        and _ids(body) == ["cafe", "pan", "azucar", "mermelada"],
    )

    check(
        "No se recomienda el propio producto ni duplicados",
        "'leche' ausente y sin ids repetidos",
        f"ids={_ids(body)}",
        "leche" not in _ids(body) and len(set(_ids(body))) == len(_ids(body)),
    )

    recs = _by_id(body)
    check(
        "Directos marcados como 'direct', indirectos como 'indirect'",
        "cafe/pan=direct, azucar/mermelada=indirect",
        f"{ {k: v['kind'] for k, v in recs.items()} }",
        recs.get("cafe", {}).get("kind") == "direct" and recs.get("pan", {}).get("kind") == "direct"
        and recs.get("azucar", {}).get("kind") == "indirect"
        and recs.get("mermelada", {}).get("kind") == "indirect",
    )

    check(
        "Fuerza: directo = peso; indirecto = eslabón más débil",
        "cafe=3.0, pan=2.5, azucar=2.5 (min 3.0/2.5), mermelada=2.0 (min 2.5/2.0)",
        f"{ {k: v['strength'] for k, v in recs.items()} }",
        recs.get("cafe", {}).get("strength") == 3.0 and recs.get("pan", {}).get("strength") == 2.5
        and recs.get("azucar", {}).get("strength") == 2.5
        and recs.get("mermelada", {}).get("strength") == 2.0,
    )

    check(
        "Etiqueta de fuerza legible para el negocio",
        "cafe='Casi siempre juntos', mermelada='Frecuente'",
        f"cafe={recs.get('cafe', {}).get('strength_label')!r}, "
        f"mermelada={recs.get('mermelada', {}).get('strength_label')!r}",
        recs.get("cafe", {}).get("strength_label") == "Casi siempre juntos"
        and recs.get("mermelada", {}).get("strength_label") == "Frecuente",
    )

    az = recs.get("azucar", {})
    check(
        "Razón de un indirecto nombra el producto puente",
        "via=[cafe] y la razón menciona 'Cafe' y 'Leche'",
        f"via={[v['id'] for v in az.get('via', [])]}, reason={az.get('reason')!r}",
        [v["id"] for v in az.get("via", [])] == ["cafe"]
        and "Cafe" in az.get("reason", "") and "Leche" in az.get("reason", ""),
    )

    check(
        "Razón de un directo menciona el producto de origen",
        "reason menciona 'Leche'",
        f"reason={recs.get('pan', {}).get('reason')!r}",
        "Leche" in recs.get("pan", {}).get("reason", ""),
    )

    check(
        "La respuesta trae la regla aplicada",
        "campo 'rule' no vacío",
        f"rule={body.get('rule', '')[:60]!r}...",
        bool(body.get("rule")),
    )

    r = requests.get(f"{BASE}/recommendations/leche", params={"limit": 2})
    body2 = r.json()
    check(
        "limit=2 recorta la lista conservando el orden",
        "ids=[cafe, pan], total_candidates=4",
        f"ids={_ids(body2)}, total_candidates={body2.get('total_candidates')}",
        r.status_code == 200 and _ids(body2) == ["cafe", "pan"] and body2.get("total_candidates") == 4,
    )

    section("C) FILTRO: un vínculo débil no genera recomendación")

    check(
        "'jugo' (pan-jugo=1.0) NO se recomienda desde 'leche'",
        "'jugo' ausente de la lista",
        f"ids={_ids(body)}",
        "jugo" not in _ids(body),
    )

    r = requests.get(f"{BASE}/recommendations/pan")
    bp = r.json()
    check(
        "'jugo' SÍ se recomienda desde 'pan' (relación directa, aunque débil)",
        "'jugo' presente como directo con etiqueta 'Ocasional'",
        f"jugo={_by_id(bp).get('jugo', {}).get('kind')}/{_by_id(bp).get('jugo', {}).get('strength_label')}",
        _by_id(bp).get("jugo", {}).get("kind") == "direct"
        and _by_id(bp).get("jugo", {}).get("strength_label") == "Ocasional",
    )

    section("D) RED ESCASA Y GRUPOS SEPARADOS")

    r = requests.get(f"{BASE}/recommendations/jabon")
    bj = r.json()
    check(
        "'jabon' solo tiene 'detergente' en su grupo",
        "ids=[detergente]; nada del grupo de comestibles",
        f"ids={_ids(bj)}",
        r.status_code == 200 and _ids(bj) == ["detergente"],
    )
    check(
        "Con pocos resultados el sistema no rellena y lo dice",
        "message indica que la lista no se completa con otros",
        f"message={bj.get('message')!r}",
        "no se completa" in bj.get("message", ""),
    )

    section("E) PRODUCTO AISLADO")

    r = requests.get(f"{BASE}/recommendations/sal")
    bs = r.json()
    check(
        "GET /recommendations/sal (sin relaciones)",
        "status=200, status='isolated', recommendations=[], message explica por qué",
        f"status={r.status_code}, body.status={bs.get('status')!r}, "
        f"recs={bs.get('recommendations')}, message={bs.get('message')!r}",
        r.status_code == 200 and bs.get("status") == "isolated"
        and bs.get("recommendations") == [] and "Sal" in bs.get("message", ""),
    )

    section("F) PRODUCTO INEXISTENTE")

    r = requests.get(f"{BASE}/recommendations/fantasma")
    check(
        "GET /recommendations/fantasma",
        "status=404, detail menciona 'fantasma'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "fantasma" in _detail(r),
    )

    section("G) DATOS INVALIDOS: límite")

    for value, why in (("0", "menor a 1"), ("11", "mayor al tope 10"), ("-1", "negativo"),
                       ("tres", "no es entero"), ("1.5", "decimal")):
        r = requests.get(f"{BASE}/recommendations/leche", params={"limit": value})
        check(
            f"GET /recommendations/leche?limit={value} ({why})",
            "status=422",
            f"status={r.status_code}",
            r.status_code == 422,
        )

    section("H) LA PROPUESTA SE ADAPTA A LOS DATOS (SQL <-> grafo sincronizados)")

    requests.post(f"{BASE}/relations", json={"a": "sal", "b": "pan", "weight": 2.0})
    r = requests.get(f"{BASE}/recommendations/sal")
    bs2 = r.json()
    check(
        "'sal' deja de estar aislado al registrar sal-pan (2.0)",
        "status='ok', ids=[pan, leche, mermelada] (jugo fuera: min 2.0/1.0)",
        f"status={bs2.get('status')!r}, ids={_ids(bs2)}",
        bs2.get("status") == "ok" and _ids(bs2) == ["pan", "leche", "mermelada"],
    )

    requests.post(f"{BASE}/products", json={"id": "te", "name": "Te"})
    requests.post(f"{BASE}/products", json={"id": "limon", "name": "Limon"})
    requests.post(f"{BASE}/relations", json={"a": "leche", "b": "te", "weight": 1.0})
    requests.post(f"{BASE}/relations", json={"a": "te", "b": "limon", "weight": 3.0})
    r = requests.get(f"{BASE}/recommendations/leche", params={"limit": 10})
    bl = r.json()
    check(
        "Directos van antes que indirectos aunque el directo sea más débil",
        "ids=[cafe, pan, te, azucar, mermelada, sal]; 'limon' fuera (puente te=1.0); "
        "'sal' entra como indirecto via pan (min 2.5/2.0)",
        f"ids={_ids(bl)}",
        _ids(bl) == ["cafe", "pan", "te", "azucar", "mermelada", "sal"],
    )


def main() -> int:
    section("SCRIPT DE ACEPTACION - F3 ComercioConecta")
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
