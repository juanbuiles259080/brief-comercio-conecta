# Decisiones de diseño — ComercioConecta

> Documento vivo. Cada decisión queda aquí con fecha, alternativas consideradas y por qué.

## F1 — Red comercial inicial

### Grafo: no dirigido con pesos opcionales
**Fecha**: 2026-10-01.

La relación "se compran juntos" es **simétrica** por naturaleza del negocio, así que el grafo es **no dirigido**. Si en F3 queremos matizar fuerza del vínculo, usamos el **peso** de la arista (default `1.0`, validación `> 0`), no el sentido.

**Alternativas descartadas**:
- *Dirigido*: más flexible para F3 ("X se recomienda después de Y") pero obliga a detectar ciclos y a cubrir ese caso en el script de aceptación desde F1. Más complejidad sin valor claro para la pyme en esta etapa.

**Implicancia operativa**: no hay caso "ciclo" en el script de aceptación F1 — esa prueba solo aplica a grafos dirigidos según la guía.

### Representación interna: lista de adyacencia propia
Estructura: `dict[str, dict[str, float]]` — por cada nodo, un dict `vecino → peso`.

**Por qué**:
- O(1) para `add_edge` y para iterar vecinos.
- Grafo esperado esparcido (pocas relaciones por producto).
- Se extiende natural a BFS/DFS (F2) y componentes conexos (F2).
- Permite almacenar peso directamente sin estructura paralela.

**Doble almacenamiento** de cada arista (`_adj[a][b]` y `_adj[b][a]`): costo 2× memoria aristas, beneficio `has_edge` y `neighbors` en O(1) sin desambiguar sentido. Para evitar duplicados en `edges()`, iteramos y emitimos solo cuando `a < b`.

**NetworkX**: prohibido para la lógica, por regla de la guía. Solo podría entrar en F4 para visualización.

### Persistencia: SQLite con módulo `sqlite3` crudo
Archivo `backend/data/comercio.db`, no versionado. El Graph vive **en RAM** y se **hidrata al startup** leyendo las tablas.

**Patrón de mutación consistente** (vía API):
```
1. Validar en Pydantic (422 si rompe formato)
2. Precheckear existencia (NodeMissing → 404 con detalle preciso)
3. Insertar en SQL   ← fuente de verdad, dispara CHECK/FK
4. Actualizar Graph en RAM
```
Si falla el paso 3, Graph nunca se modifica (orden "SQL-first, Graph-second"). Si fallara entre 3 y 4 (desincronización), un restart rehidrataría desde SQL.

**Esquema**:
```sql
CREATE TABLE products (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE relations (
  a      TEXT NOT NULL,
  b      TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  PRIMARY KEY (a, b),
  FOREIGN KEY (a) REFERENCES products(id),
  FOREIGN KEY (b) REFERENCES products(id),
  CHECK (weight > 0),
  CHECK (a < b)      -- normalización no dirigida
);
```

**`PRAGMA foreign_keys = ON`** se setea por conexión — SQLite las ignora por default.

**Normalización** `a = min(x,y), b = max(x,y)` al insertar relación: evita que `(leche, pan)` y `(pan, leche)` queden como filas distintas. El CHECK bloquea insertar `a == b` o `a > b`.

**Alternativas descartadas**:
- *JSON en disco*: más simple pero perdemos integridad referencial y chequeos de SQL.
- *SQLAlchemy*: ORM maduro pero suma dependencia + curva (sesiones, declarative base). Con 2 tablas no se justifica.
- *Solo en memoria*: cada restart borra datos — riesgoso en demos.

### Validación en capas (422 vs 400/404/409)
Dos tipos de "entrada mala" se distinguen deliberadamente:

| Capa | Status | Qué chequea | Ejemplo |
|---|---|---|---|
| **Pydantic** | **422** | Formato / tipos / rangos declarativos | `weight: 0`, `id: ""`, falta campo, JSON mal armado |
| **Dominio** | **400 / 404 / 409** | Reglas de negocio sobre payload válido | Producto no existe, relación duplicada, self-loop detectado post-strip |

El exception handler único en `main.py` mapea `GraphError` → HTTP, así los routers no tienen `try/except`.

### Seed automático al primer arranque
`seed.sql` tiene 25 productos y 41 relaciones representando una tienda de barrio real. **Dos componentes conexos** por diseño:
- **Comestibles** (22 productos) — mayoría de la red.
- **Higiene** (3 productos: jabon, papel_higienico, detergente) — desconectado del resto, útil para demostrar `componentes` en F2.

El lifespan ejecuta `load_seed()` solo si `is_empty(conn)` → arranques posteriores no duplican.
`INSERT OR IGNORE` en el SQL hace la carga idempotente también si se re-ejecuta manualmente.

Variables de entorno para tests y producción:
- `COMERCIO_DB_PATH` → override del path de la DB (usado por el script de aceptación).
- `COMERCIO_SKIP_SEED=1` → desactiva la carga del seed (idem).

## Stack

- **Backend**: Python 3.12+ (verificado 3.14.4), FastAPI, `uvicorn[standard]`, Pydantic v2. Solo librerías estándar para el grafo y SQLite.
- **Frontend**: Vite + React + TypeScript + Tailwind v4. Visualización con `react-force-graph-2d` (agregada en PR #4 por Cristian).
- **HTTP**: `fetch` tipado desde el front; `requests` desde Python para el script de aceptación.
- **CORS**: habilitado para `http://localhost:5173` y `http://localhost:5174` en dev. El cliente evita mandar `Content-Type: application/json` en GETs para no disparar preflight innecesario.

### Orquestación del frontend: `refreshTick` compartido
Los tres hooks (`useProducts`, `useRelations`, `useNetwork`) aceptan un parámetro `refreshTick: number` y lo incluyen en el `useEffect`. `App.tsx` mantiene `tick` + `bump()`; cada panel llama `onChange={bump}` tras mutar.

**Resultado**: cualquier mutación en cualquier panel refresca los **tres** (y el `GraphViz` si está habilitado) sin lifting state ni context. ~20 líneas de orquestación.

**Alternativas descartadas**:
- *Lifting state a App*: necesita re-escribir las APIs de los paneles para recibir todo por props. Más código.
- *React Context*: pensado para "muchos consumidores que raramente cambian". Nuestro caso es "pocos consumidores que cambian seguido". Overkill.
- *TanStack Query*: fetching + cache + invalidation listos. Mejor para una app con muchos endpoints; para F1 con 3 agrega una dependencia pesada.

### Script de aceptación: autosuficiente
`backend/scripts/acceptance.py` spawnea su propio `uvicorn` con `COMERCIO_DB_PATH=<tmp>` + `COMERCIO_SKIP_SEED=1`. Al terminar mata el proceso y borra la DB temporal.

Esto permite:
- Correr sin un servidor dev ya levantado.
- Garantizar estado "red vacía" al inicio (sin esto el seed poblaría la DB).
- No contaminar `backend/data/comercio.db`.

**Output UTF-8 forzado** (`sys.stdout.reconfigure(encoding='utf-8')`) para que PowerShell no crashee con caracteres fuera de cp1252.

## Decisiones menores que valen notar

- **`erasableSyntaxOnly` en tsconfig** (Vite moderno) prohibe el shorthand `constructor(public x: ...)`. Rescrito con fields explícitos.
- **`isinstance(True, int)` es `True`** en Python, así que `Graph.add_edge(..., weight=True)` requiere `isinstance(weight, bool)` **antes** de `isinstance(weight, (int, float))`.
- **`str_strip_whitespace=True`** en el `_StrippedBase` de Pydantic corre **antes** del `min_length` y del `model_validator`. Resultado: `RelationIn(a="x", b="  x  ")` se rechaza como self-loop.
- **Timestamp SQLite en UTC**: `CURRENT_TIMESTAMP` devuelve UTC string, no local. El frontend muestra el string tal cual (F1 no formatea). Documentar en el pitch si alguien pregunta por qué dice `2026-10-02 02:36` cuando el usuario estaba trabajando "a las 9 de la noche del 1".

## Incidente notable del workflow Git (PR #3 → PR #4)

El PR #3 (`feature/f1-frontend-improve` → `develop`) se mergeó sobre un commit base que **no tenía** la carpeta `frontend/`. Resultado: develop quedó sin frontend aunque el PR decía exitoso.

Se detectó al correr `git ls-tree origin/develop` y notar que `frontend/` no estaba. La rama `feature/f1-frontend-improve` sí tenía los archivos correctos (tras 2 commits de fix posteriores al merge original). El PR #4 trajo esos commits a develop y restauró el frontend.

**Lección**: siempre basar las ramas feature en el HEAD actualizado de `develop`, nunca en commits viejos. Verificar `git fetch origin && git rebase origin/develop` antes de empezar a trabajar.
