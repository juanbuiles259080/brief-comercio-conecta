# Plan de avance — ComercioConecta

**Estado**: F1 en curso.
**Hoy**: 2026-10-01.
**Entrega F1**: 2026-10-13 (martes).

## Decisiones cerradas (ver `docs/decisiones.md`)

- Backend: FastAPI + Python 3.12+
- Frontend: Vite + React + TypeScript + Tailwind
- Grafo: lista de adyacencia propia, **no dirigido**, pesos opcionales (default 1.0, > 0)
- Persistencia: SQLite con módulo `sqlite3` crudo (sin ORM)
- Equipo: 3 integrantes (autorizado por docente)
- Reparto: Dev A (core+datos), Dev B (API+aceptación), Dev C (front+docs)

---

## F1 — Red comercial inicial

### Setup (día 1)
- [x] **T1** — Repo local inicializado (`main` + `develop`), `.gitignore`, template de PR, estructura base de carpetas ✅ 2026-10-01
- [x] **T2** — Backend scaffold: `.venv`, FastAPI "hello" con CORS, `requirements.txt`, `main.py` ✅ 2026-10-01
- [x] **T3** — Frontend scaffold: Vite + React + TS + Tailwind v4 (compila OK) ✅ 2026-10-01
- [x] **T4** — Datos sintéticos: 25 productos y 41 relaciones en `backend/data/seed.sql` ✅ 2026-10-01
  - [x] Grupo higiene (`jabon`, `papel_higienico`, `detergente`) desconectado del resto — queda listo para "componentes" en F2
  - [x] Pesos variados (1.0-3.0) representando "fuerza del vínculo" — queda listo para F3
  - [x] Todas las relaciones ya normalizadas (`a < b`) para pasar el CHECK de SQL

### Core del grafo (días 2-3)
- [x] **T5** — Clase `Graph` propia en `core/graph.py` (adjacency list) ✅ 2026-10-01
  - [x] `add_node`, `remove_node`, `has_node`, `nodes()`
  - [x] `add_edge`, `remove_edge`, `has_edge`, `neighbors`, `edges()`
  - [x] Simetría del no dirigido: guardo arista en ambos sentidos; `edges()` emite una sola vez con `a < b`
  - [x] Traza manual ejecutable: `python -m app.core.graph` (bloque `__main__`)
- [x] **T6** — Excepciones de dominio en `core/errors.py` ✅ 2026-10-01
  - [x] `GraphError` (base), `NodeExists`, `NodeMissing`, `EdgeExists`, `InvalidWeight`, `SelfLoop`
- [x] **T7** — Repository SQLite en `repository/` ✅ 2026-10-01
  - [x] `db.py` — `get_connection` (foreign_keys ON, row_factory Row) + `init_schema` idempotente
  - [x] `products_repo.py` — `insert` / `get` / `list_all` / `exists`, mapea `IntegrityError → NodeExists`
  - [x] `relations_repo.py` — `insert` con normalización `a<b` + `list_all`, mapea FK/PK/CHECK a errores de dominio
  - [x] `repository/hydrate_graph(conn)` reconstruye Graph en RAM leyendo ambas tablas
  - [x] `main.py` con lifespan: `get_connection → init_schema → hydrate_graph → app.state`

### API (días 3-5)
- [x] **T8** — Schemas Pydantic en `app/schemas.py` ✅ 2026-10-01
  - [x] `_StrippedBase` con `str_strip_whitespace=True` (trimma antes de validar)
  - [x] `ProductIn` (id/name con `min_length=1`, `max_length` razonables), `ProductOut`
  - [x] `RelationIn` (weight default 1.0, `gt=0`, `model_validator` rechaza self-loop post-strip), `RelationOut`
  - [x] `NodeInfo`, `EdgeInfo`, `NetworkOut`
- [x] **T9** — Router productos (`api/products.py`) ✅ 2026-10-01
  - [x] `POST /products` → 201 happy / 409 duplicado / 422 formato (Pydantic)
  - [x] `GET /products` → lista ordenada por id
  - [x] `GET /products/{id}` → 200 / 404
  - [x] `api/deps.py` con `get_conn` / `get_graph` (reutilizable por T10/T11)
  - [x] Exception handler único en `main.py` mapea `GraphError → HTTPException` (reutilizable)
  - [x] Verificado: SQL y Graph quedan sincronizados por API (health muestra conteos correctos post-POST)
- [x] **T10** — Router relaciones (`api/relations.py`) ✅ 2026-10-01
  - [x] `POST /relations` → 201 / 404 nodo faltante (preciso: dice cuál) / 409 duplicada (reconoce invertida) / 422 peso ≤0 (Pydantic) / 422 self-loop (Pydantic post-strip)
  - [x] `GET /relations` → lista ordenada y normalizada (`a < b`)
  - [x] Precheck de existencia por producto → el 404 identifica exactamente cuál falta
  - [x] Verificado: SQL + Graph sincronizados tras POSTs mixtos (normal + invertidos)
- [x] **T11** — Router network (`api/network.py`) ✅ 2026-10-01
  - [x] `GET /network` → `{nodes:[{id,name}], edges:[{a,b,weight}]}`
  - [x] Nodos vienen del `Graph` en RAM + nombres se joinean desde `products_repo.list_all`
  - [x] Aristas vienen de `graph.edges()` (ya normalizadas `a < b`)
  - [x] Verificado: red vacía devuelve `{nodes:[], edges:[]}` sin ruido
- [x] **T12** — Carga automática del `seed.sql` al startup si las tablas están vacías ✅ 2026-10-01
  - [x] `db.is_empty(conn)` + `db.load_seed(conn)`
  - [x] Lifespan: `init_schema → is_empty? load_seed → hydrate_graph`
  - [x] Verificado: arranque 1 carga 25/41; arranque 2 sin tocar nada (no duplica)

### Aceptación (día 6)
- [x] **T13** — `backend/scripts/acceptance.py` ✅ 2026-10-01 — **24/24 PASS**
  - [x] Autosuficiente: levanta su propio `uvicorn` con DB temporal + `COMERCIO_SKIP_SEED=1`
  - [x] A) Red vacía (3 asserts): `/network`, `/products`, `/relations` todos devuelven estructura vacía
  - [x] B) Flujo normal (8 asserts): crear productos, relación (invertida → normalizada), peso default, GETs
  - [x] C) Datos inválidos productos (4 asserts): duplicado, id vacío, whitespace, campo faltante
  - [x] D) Datos inválidos relaciones (6 asserts): duplicada, peso 0/negativo/string, self-loop, JSON mal formado
  - [x] E) Recursos inexistentes (3 asserts): producto, 'a' en relación, 'b' en relación
  - [x] F) Caso "ciclo" documentado como no aplicable (grafo no dirigido)
  - [x] Imprime `ESCENARIO / ESPERADO / OBTENIDO / PASS|FAIL` + resumen + `exit(1)` si falla
  - [x] UTF-8 forzado en stdout para que corra limpio en PowerShell

### Frontend (días 6-9)
- [x] **T14** — `src/api/client.ts` + `src/types/domain.ts` tipados contra los endpoints ✅ 2026-10-01
  - [x] `types/domain.ts` espeja los schemas Pydantic (Product, Relation, Network, etc.)
  - [x] `api/client.ts` con wrapper `call<T>()`, base URL vía `VITE_API_URL` (default localhost:8000)
  - [x] `ApiError` extiende Error (fields explícitos por `erasableSyntaxOnly`)
  - [x] `formatDetail` maneja tanto 404/409 (string) como 422 (array Pydantic)
- [x] **T15** — `ProductsPanel` — tabla con GET + form POST + manejo de 409/400 ✅ 2026-10-01
  - [x] Hook `useProducts()` con `products, loading, error, reload, create`
  - [x] Form con validación HTML + submit async + loading state ("Agregando...")
  - [x] Error inline (409 duplicado, 422 formato) debajo del form
  - [x] Tabla con empty state ("Sin productos aun")
  - [x] Styling Tailwind decente (card, tabla con zebra sutil, botón negro)
- [x] **T16** — `RelationsPanel` — tabla + form (selects de productos existentes) + errores ✅ 2026-10-01
  - [x] Hook `useRelations(refreshTick)` + comparte `useProducts(refreshTick)` para poblar los selects
  - [x] Form: select A, select B, input weight (number, step 0.1), botón "Crear relación"
  - [x] Validación cliente: `canSubmit = a && b && a !== b` + chequeo de peso > 0 en handleSubmit
  - [x] Errores inline (409 duplicada, 404 nodo, 422 self-loop, local "peso <=0")
  - [x] Tabla con id + nombre de producto + peso formateado a 1 decimal
- [x] **T17** — `NetworkPanel` — lista agrupada "Producto → [vecinos]" consumiendo `/network` ✅ 2026-10-01
  - [x] Hook `useNetwork(refreshTick)`
  - [x] Builder de adyacencia en cliente (`Map<id, Neighbor[]>`) con nombres joineados
  - [x] Cards por producto con sus vecinos como chips, ordenados por peso desc
  - [x] Casos: red vacía ("agregá productos..."), producto aislado ("aislado" en vez de contador)
- [x] **T18** — `Dashboard` que compone los 3 paneles + styling Tailwind decente ✅ 2026-10-01
  - [x] `App.tsx` orquesta: `refreshTick` + `bump()` compartidos → mutación en cualquier panel refresca los 3
  - [x] Layout: contenedor `max-w-5xl` centrado, cards apiladas con `space-y-6`, header con título y descripción
  - [x] Build pasa limpio: 23 módulos, 12.7 KB CSS, 231 KB JS

### Cierre (días 10-12)
- [x] **T19** — README raíz: propósito, cómo correr back+front, endpoints, decisiones, equipo ✅ 2026-10-01
  - [x] Screenshot `docs/f1-ui-full.png` embebido
  - [x] Tabla completa de endpoints con status codes
  - [x] Sección de script de aceptación con comando
  - [x] Decisiones clave resumidas (link al detallado en `docs/decisiones.md`)
- [x] **T20** — `docs/decisiones.md` completado ✅ 2026-10-01
  - [x] Grafo (dirección, representación, doble almacenamiento)
  - [x] Persistencia (patrón SQL-first, esquema con CHECKs, env vars)
  - [x] Validación en capas (422 vs 400/404/409)
  - [x] Orquestación frontend (`refreshTick`, alternativas descartadas: lifting/Context/TanStack)
  - [x] Decisiones menores con contexto (bool en pesos, erasableSyntaxOnly, UTC en SQLite)
- [x] **T21** — `docs/bitacora-ia-f1.md` llenada ✅ 2026-10-01
  - [x] 10 entradas cubriendo cada tarea mayor (arquitectura, scaffold, Graph, repo, schemas, routers, seed, aceptación, frontend, docs)
  - [x] Reflexión final sobre uso responsable de IA
- [ ] **T22** — Video ≤3 min: happy path + un caso borde *(requiere grabar con el equipo)*
- [ ] **T23** — Pitch (7 min demo + 3 preguntas) ensayado una vez *(requiere ensayo con el equipo)*
- [ ] **T24** — Tag `v0.1-f1`, PR final a `main`, revisión de commits por integrante *(requiere repo remoto en GitHub)*

---

## F2 — Exploración de relaciones *(bloqueado hasta cerrar F1)*
## F3 — Propuesta comercial justificable *(idem)*
## F4 — Panel comercial demostrable *(idem)*

---

## Convenciones

- **Ramas**: `f1/<slug>` por tarea → PR → review de otro integrante → merge a `develop`. `main` solo recibe el release de feature.
- **Commits**: mensaje imperativo corto. Si cierra una tarea, incluir `(T#)` al final.
- **Antes de abrir PR**: correr `python scripts/acceptance.py` y pegar la salida en el PR (cuando T13 esté).
- **Bitácora IA**: se actualiza al mergear cada PR, no al final.
