# Guión del Pitch — F1 ComercioConecta

> 7 minutos de demo + 3 minutos de preguntas (según la guía).
> Antes de arrancar: backend corriendo en `localhost:8000`, frontend en `localhost:5173`, 3 terminales listas, 2 pestañas del navegador abiertas.

## Minuto a minuto

### 0:00 – 0:45 — Problema de negocio y usuario (Punto 1)

**Mostrar**: README en GitHub o slide con 2 bullets.

**Decir**:
> "ComercioConecta es una pyme que agrupa tiendas de barrio. Hoy las recomendaciones salen de intuición — nadie puede identificar qué productos se compran juntos. Hay dos usuarios: el **analista comercial** carga productos y relaciones de co-compra, y el **encargado de ventas** después consulta la red para armar propuestas. **F1 cubre el lado del analista** — tener la base de datos de relaciones curada y lista para que F2 y F3 agreguen valor al encargado."

### 0:45 – 2:00 — Modelado (Punto 2)

**Mostrar**: `backend/app/core/graph.py` abierto en VS Code.

**Decir**:
> "Modelamos como grafo no dirigido con pesos opcionales. Nodos son productos con id y nombre. Aristas son relaciones de co-compra observadas. No dirigido porque la co-compra es simétrica — si leche y pan aparecen juntos, es la misma observación da vuelta. Los pesos (default 1.0, validación mayor a 0) representan la fuerza del vínculo: 1.0 ocasional, 3.0 casi siempre juntos. La representación interna es lista de adyacencia propia, un diccionario de diccionarios. Guardamos cada arista en los dos sentidos para que `has_edge` y `neighbors` sean O(1). Sin NetworkX para los algoritmos, por regla de la guía."

### 2:00 – 5:00 — DEMO EN VIVO (Punto 5 integrado)

**Pasar al navegador** en http://localhost:5173.

**(2:00-2:30) Mostrar la red cargada**:
> "Al arrancar el backend se cargan 25 productos y 41 relaciones del seed. Los 3 paneles muestran la misma información desde distintos ángulos: Productos como tabla, Relaciones como pares con peso, y Red agrupada por producto con sus vecinos como chips."
>
> "Fíjense que `jabon`, `papel_higienico` y `detergente` solo se relacionan entre ellos — ningún comestible. Son un componente desconectado que modelamos a propósito para que F2 pueda demostrar componentes conexos sin agregar datos."

**(2:30-3:30) Agregar un producto**:
> Agregar: id `mani`, nombre `Mani salado` → Agregar.
>
> "Los 3 paneles se actualizaron automáticamente. Esto se logra con un contador compartido que fuerza re-fetch — 20 líneas de orquestación en el frontend."

**(3:30-4:30) Agregar una relación + caso borde**:
> Agregar relación `mani` + `cerveza`, peso 2.0 → 201.
>
> "La red muestra `mani` con `cerveza` como vecino y viceversa — porque es no dirigido."
>
> **Caso borde — duplicado invertido**: Intentar crear `cerveza + mani` → 409 "Edge already exists".
>
> "El sistema detectó el duplicado aunque los productos están en orden invertido. Esto es por normalización `a < b` que aplicamos antes de guardar en SQL."

**(4:30-5:00) Otros casos borde** (mencionar sin ejecutar):
> "Cubiertos también: peso 0 o negativo → 422 Pydantic. Self-loop → 422. Producto inexistente al crear relación → 404 con el id específico del faltante. Red vacía → `{nodes:[], edges:[]}` sin crashear."

### 5:00 – 5:45 — Algoritmo + complejidad (Puntos 3 y 4)

**Mostrar**: `graph.py` o tabla de complejidad.

**Decir**:
> "F1 no requiere algoritmos de recorrido — eso llega en F2 con BFS, DFS y componentes conexos. Lo que sí hay en F1 son dos operaciones propias de grafo: la normalización `a < b` al insertar y la sincronización SQL ↔ Graph en RAM con patrón 'SQL-first, Graph-second'."
>
> "Complejidad: lista de adyacencia es O(V+E) memoria. `add_edge`, `has_edge`, `neighbors` son O(1). `edges()` es O(V+E). Para 25 nodos y 41 aristas todo es instantáneo. Descartamos matriz 25×25 porque desperdicia memoria con 95% ceros, y lista de aristas plana porque `neighbors` sería O(E)."

### 5:45 – 6:45 — Script de aceptación en vivo (Punto 6a)

**Pasar a la terminal libre**:
```powershell
cd backend
python scripts/acceptance.py
```

Mientras corre:
> "Este script es un requisito duro de la guía. Levanta su propio uvicorn contra una base de datos temporal, corre 24 escenarios cubriendo todos los casos que exige la guía, imprime 'escenario / esperado / obtenido / pass-fail' por cada uno, y hace `exit 1` si algo falla. Se puede integrar a CI."

Cuando aparece **24/24 PASS**:
> "24 de 24 asserts pasados. Cubre red vacía, flujo normal, datos inválidos de productos y relaciones, recursos inexistentes, y una nota explicando por qué el caso 'ciclo' no aplica."

### 6:45 – 7:00 — Contribuciones del equipo (Punto 6b)

**Pasar al navegador** → https://github.com/juanbuiles259080/brief-comercio-conecta/graphs/contributors

**Decir**:
> "El equipo de 3 integrantes contribuyó efectivamente: Juan en backend, setup y aceptación; Fabian en frontend inicial; Cristian en la mejora del visualizador. 4 pull requests mergeados, cada uno con su diff y propósito claro. La bitácora de IA en `docs/bitacora-ia-f1.md` documenta cada decisión asistida por IA con el formato que exige la guía."

---

## Preguntas (3 min) — anticipar

### 1. "¿Por qué no NetworkX?"
> La guía lo prohíbe para algoritmos — solo lo permite para visualización. Para F1 no hay viz gráfica (es F4). Implementar la clase Graph desde cero es parte del aprendizaje y nos da control fino sobre la complejidad.

### 2. "¿Por qué SQLite y no Postgres/Mongo?"
> SQLite nos da integridad referencial, CHECK constraints, y una API estándar con 0 dependencias — es parte de Python. Para una pyme con decenas de miles de productos funciona perfecto. Si F4 pide escalabilidad, migrar a Postgres toca una sola capa de nuestro código.

### 3. "¿Qué pasa si matan uvicorn?"
> El grafo en RAM se pierde pero SQLite persiste. Al relanzar, `hydrate_graph(conn)` reconstruye el grafo leyendo las tablas.

### 4. "¿Por qué cada arista 2 veces en RAM?"
> Costo 2× memoria, beneficio O(1) para `has_edge` y `neighbors`. Para F2 que itera vecinos miles de veces en BFS, es correcto.

### 5. "¿Cómo detectan duplicados invertidos?"
> Normalización `a < b` antes de insertar en SQL. Hay un `CHECK (a < b)` en el schema que lo garantiza aunque alguien se saltee nuestro código.

### 6. "¿Qué pasa si envían `weight: 'alto'`?"
> Pydantic rechaza con 422 "Input should be a valid number".

### 7. "¿El Graph se protege solo si Pydantic no estuviera?"
> Sí. `Graph.add_edge` valida que el peso sea número mayor a 0, que no sea booleano (porque `True` es subclase de `int` en Python), que no haya self-loop, y que los nodos existan. Defensa en profundidad.

### 8. "¿El frontend puede funcionar sin backend?"
> No, es rebanada vertical real. Si matás el backend, los paneles muestran "Error de red" con el detalle. No es un mock.

### 9. "¿Qué quedó preparado para F2?"
> La clase `Graph` ya tiene `neighbors()` — bloque básico de BFS/DFS. El seed tiene 2 componentes conexos para demostrar componentes. La arquitectura separa core/repository/API, así F2 solo toca `core` para los algoritmos.

### 10. "¿Cómo usaron la IA responsablemente?"
> La IA generó código, nosotros revisamos y verificamos. Documentado en `docs/bitacora-ia-f1.md` con el formato que exige la guía: qué pedimos, qué propuso, qué aceptamos o rechazamos y por qué, y cómo lo verificamos. Rechazamos propuestas que violaban la guía (ej. NetworkX).

---

## Guión del video (≤ 3 min)

### 0:00 – 0:20 — Intro
> "ComercioConecta — microproducto para que una pyme de tiendas de barrio registre y explore co-compras de productos. Equipo de 3, F1 completa."

### 0:20 – 1:30 — Demo visual (grabar pantalla en http://localhost:5173)
- Los 3 paneles cargados con 25/41 (10 seg)
- Agregar un producto, ver los 3 paneles actualizarse (20 seg)
- Agregar relación, ver aparecer el vecino en Red (15 seg)
- Duplicar invertida → mostrar error 409 inline (15 seg)

### 1:30 – 2:00 — Casos borde (Swagger o UI)
- Peso 0 → 422
- Self-loop → 422
- Producto inexistente → 404

### 2:00 – 2:40 — Script de aceptación
Grabar terminal con `python scripts/acceptance.py` → mostrar **24/24 PASS**.

### 2:40 – 3:00 — Cierre
> "Backend FastAPI con grafo propio no dirigido con pesos. Persistencia SQLite. Frontend React + TS + Tailwind. 24/24 asserts. Preparado para F2 y F3."

---

## Checklist antes de salir a presentar

- [ ] Backend corriendo (`uvicorn app.main:app --reload` en terminal 1)
- [ ] Frontend corriendo (`npm run dev` en terminal 2)
- [ ] Terminal 3 libre para el script de aceptación
- [ ] Navegador abierto en http://localhost:5173 con los 3 paneles cargados
- [ ] Pestañas secundarias listas: GitHub repo, Swagger `/docs`, `graph.py` en VS Code
- [ ] Haber corrido el script de aceptación una vez para confirmar 24/24 antes del pitch
- [ ] Video grabado y subido a Drive/YouTube (link en la entrega)
- [ ] Tag `v0.1-f1` creado en GitHub

## Qué NO decir (errores comunes)

- No digas "usamos NetworkX" — está prohibido. Error grave aunque sea sin querer.
- No digas "usamos un ORM" — es `sqlite3` crudo.
- No prometas features de F2-F4 como si ya estuvieran. Decí "preparamos la base para eso".
- No digas "lo hizo la IA" sin matizar. Decí "generamos con asistencia de IA, revisamos y verificamos manualmente, está documentado en la bitácora".
