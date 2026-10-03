"""Script de aceptación - Feature 1 ComercioConecta.

Requisito duro de la guía (`03-guia-comun-estudiantes.md` -> "Pruebas de aceptación
sin frameworks adicionales"). Cubre: escenario normal, grafo vacío, nodo
inexistente, relación inexistente, datos inválidos. NO cubre "ciclo" porque el
grafo es no dirigido (ver `docs/decisiones.md`).

El script es autosuficiente: levanta su propio `uvicorn` contra una DB temporal,
corre los asserts, imprime ESCENARIO / ESPERADO / OBTENIDO / PASS|FAIL, y hace
`exit(1)` si algo falla.

Uso (desde backend/):
    python scripts/acceptance.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

# Fuerza UTF-8 en Windows (cp1252 por default) para evitar UnicodeEncodeError.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
BACKEND_DIR = Path(__file__).resolve().parent.parent

_results: list[tuple[str, str]] = []
_n = 0


def _print(status: str, label: str, expected: str, actual: str) -> None:
    global _n
    _n += 1
    _results.append((label, status))
    print(f"[{status}] #{_n:02d} {label}")
    print(f"         Esperado: {expected}")
    print(f"         Obtenido: {actual}")


def check(label: str, expected: str, actual: str, ok: bool) -> None:
    _print("PASS" if ok else "FAIL", label, expected, actual)


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _detail(resp: requests.Response) -> str:
    try:
        d = resp.json().get("detail", "")
        return d if isinstance(d, str) else str(d)
    except Exception:
        return resp.text


# ---------------------------------------------------------------------------
# Server spawn
# ---------------------------------------------------------------------------
def start_server() -> tuple[subprocess.Popen, Path]:
    tmp_db = Path(tempfile.mkdtemp()) / "acceptance.db"
    env = {
        **os.environ,
        "COMERCIO_DB_PATH": str(tmp_db),
        "COMERCIO_SKIP_SEED": "1",
    }
    cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--port", str(PORT),
        "--log-level", "warning",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Esperar health
    for _ in range(40):
        try:
            if requests.get(f"{BASE}/health", timeout=0.5).status_code == 200:
                return proc, tmp_db
        except requests.RequestException:
            pass
        time.sleep(0.3)
    proc.terminate()
    raise RuntimeError("uvicorn no arrancó en 12s")


def stop_server(proc: subprocess.Popen, tmp_db: Path) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    try:
        tmp_db.unlink()
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
def run_scenarios() -> None:
    section("A) RED VACIA (sin datos cargados)")

    r = requests.get(f"{BASE}/network")
    body = r.json()
    check(
        "GET /network devuelve estructura vacía",
        "status=200, {nodes: [], edges: []}",
        f"status={r.status_code}, nodes={body.get('nodes')}, edges={body.get('edges')}",
        r.status_code == 200 and body.get("nodes") == [] and body.get("edges") == [],
    )

    r = requests.get(f"{BASE}/products")
    check(
        "GET /products devuelve lista vacía",
        "status=200, body=[]",
        f"status={r.status_code}, body={r.json()}",
        r.status_code == 200 and r.json() == [],
    )

    r = requests.get(f"{BASE}/relations")
    check(
        "GET /relations devuelve lista vacía",
        "status=200, body=[]",
        f"status={r.status_code}, body={r.json()}",
        r.status_code == 200 and r.json() == [],
    )

    section("B) FLUJO NORMAL (crear productos y relación, consultar)")

    r = requests.post(f"{BASE}/products", json={"id": "leche", "name": "Leche"})
    check(
        "POST /products leche",
        "status=201, body.id='leche', body.name='Leche'",
        f"status={r.status_code}, body={r.json()}",
        r.status_code == 201 and r.json().get("id") == "leche" and r.json().get("name") == "Leche",
    )

    r = requests.post(f"{BASE}/products", json={"id": "pan", "name": "Pan"})
    check(
        "POST /products pan",
        "status=201, body.id='pan'",
        f"status={r.status_code}, body.id={r.json().get('id')}",
        r.status_code == 201 and r.json().get("id") == "pan",
    )

    r = requests.post(f"{BASE}/products", json={"id": "cafe", "name": "Cafe"})
    check(
        "POST /products cafe",
        "status=201",
        f"status={r.status_code}",
        r.status_code == 201,
    )

    # Normalización: entrada invertida -> salida con a < b
    r = requests.post(f"{BASE}/relations", json={"a": "pan", "b": "leche", "weight": 2.5})
    body = r.json()
    check(
        "POST /relations (pan, leche) -> normaliza como (leche, pan)",
        "status=201, body={a:'leche', b:'pan', weight:2.5}",
        f"status={r.status_code}, body={body}",
        r.status_code == 201 and body == {"a": "leche", "b": "pan", "weight": 2.5},
    )

    # Default weight
    r = requests.post(f"{BASE}/relations", json={"a": "cafe", "b": "leche"})
    body = r.json()
    check(
        "POST /relations sin weight -> default 1.0",
        "status=201, body.weight=1.0",
        f"status={r.status_code}, body.weight={body.get('weight')}",
        r.status_code == 201 and body.get("weight") == 1.0,
    )

    r = requests.get(f"{BASE}/products")
    ids = [p["id"] for p in r.json()]
    check(
        "GET /products devuelve 3 productos ordenados por id",
        "ids=['cafe','leche','pan']",
        f"ids={ids}",
        ids == ["cafe", "leche", "pan"],
    )

    r = requests.get(f"{BASE}/products/leche")
    check(
        "GET /products/leche",
        "status=200, body.id='leche'",
        f"status={r.status_code}, body.id={r.json().get('id')}",
        r.status_code == 200 and r.json().get("id") == "leche",
    )

    r = requests.get(f"{BASE}/network")
    body = r.json()
    check(
        "GET /network tras altas",
        "status=200, 3 nodos, 2 aristas",
        f"status={r.status_code}, {len(body['nodes'])} nodos, {len(body['edges'])} aristas",
        r.status_code == 200 and len(body["nodes"]) == 3 and len(body["edges"]) == 2,
    )

    section("C) DATOS INVALIDOS: productos")

    r = requests.post(f"{BASE}/products", json={"id": "leche", "name": "Otra"})
    check(
        "POST /products con id duplicado",
        "status=409, detail menciona 'already exists'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 409 and "already exists" in _detail(r),
    )

    r = requests.post(f"{BASE}/products", json={"id": "", "name": "x"})
    check(
        "POST /products con id vacío",
        "status=422 (Pydantic rechaza min_length)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(f"{BASE}/products", json={"id": "   ", "name": "x"})
    check(
        "POST /products con id solo whitespace",
        "status=422 (strip + min_length lo rechaza)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(f"{BASE}/products", json={"name": "sin id"})
    check(
        "POST /products sin campo 'id'",
        "status=422 (campo requerido)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    section("D) DATOS INVALIDOS: relaciones")

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "pan"})
    check(
        "POST /relations duplicada (misma pareja ya existe)",
        "status=409, detail menciona 'already exists'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 409 and "already exists" in _detail(r),
    )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "cafe", "weight": 0})
    check(
        "POST /relations peso = 0",
        "status=422 (Pydantic gt=0)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "cafe", "weight": -1.5})
    check(
        "POST /relations peso negativo",
        "status=422 (Pydantic gt=0)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "cafe", "weight": "mucho"})
    check(
        "POST /relations peso tipo string",
        "status=422 (Pydantic tipo float)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "leche"})
    check(
        "POST /relations self-loop (a == b)",
        "status=422 (model_validator rechaza)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    r = requests.post(
        f"{BASE}/relations",
        data="esto no es json",
        headers={"Content-Type": "application/json"},
    )
    check(
        "POST /relations con payload NO json",
        "status=422 (JSON mal formado)",
        f"status={r.status_code}",
        r.status_code == 422,
    )

    section("E) RECURSO INEXISTENTE")

    r = requests.get(f"{BASE}/products/no-existe")
    check(
        "GET /products/no-existe",
        "status=404, detail menciona 'does not exist'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "does not exist" in _detail(r),
    )

    r = requests.post(f"{BASE}/relations", json={"a": "fantasma", "b": "leche"})
    check(
        "POST /relations con producto 'a' inexistente",
        "status=404, detail menciona 'fantasma'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "fantasma" in _detail(r),
    )

    r = requests.post(f"{BASE}/relations", json={"a": "leche", "b": "zorro"})
    check(
        "POST /relations con producto 'b' inexistente",
        "status=404, detail menciona 'zorro'",
        f"status={r.status_code}, detail={_detail(r)!r}",
        r.status_code == 404 and "zorro" in _detail(r),
    )

    section("F) NOTA SOBRE 'CICLO'")
    print("  El grafo es no dirigido (ver docs/decisiones.md).")
    print("  La guía pide el caso 'ciclo' solo cuando el problema usa dependencias")
    print("  dirigidas; por lo tanto no aplica a esta feature.")


def main() -> int:
    section("SCRIPT DE ACEPTACION - F1 ComercioConecta")
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
