# Guión del Pitch — F3 ComercioConecta

> 7 minutos de demo + 3 minutos de preguntas (según la guía).
> Antes de arrancar: backend en `localhost:8000`, frontend en `localhost:5173`, una terminal libre para el script, y la **traza a mano** (sección "Traza en pizarra") lista en un slide o en papel.
> **Completar antes de presentar:** quién hace el pitch y el nombre del tag/release de F3.

## Minuto a minuto

### 0:00 – 0:45 — Problema de negocio y usuario

**Mostrar**: la pantalla principal de Recomendaciones (sin elegir producto).

**Decir**:
> "El encargado de ventas de una tienda de barrio quiere sugerirle algo más al cliente que ya lleva leche. Hoy lo hace por intuición. F1 nos dio la base de productos y compras conjuntas, y F2 nos permitió explorar relaciones. **F3 le entrega al encargado una lista corta de productos, cada uno con la razón de por qué se propone.** Y cuando no hay datos suficientes, el sistema lo dice en vez de inventar."

### 0:45 – 1:45 — Modelado y regla (decisión de grafo)

**Mostrar**: `backend/app/core/recommend.py`, el bloque de comentarios de la regla.

**Decir**:
> "El modelo viene de F1: grafo no dirigido, nodos son productos, aristas son compras conjuntas y el peso es la fuerza del vínculo, de 1.0 ocasional a 3.0 casi siempre juntos. Para F3 definimos una regla de cuatro pasos:
> **Uno**: los candidatos son los productos alcanzables con el BFS de F2 hasta 2 saltos. A 3 saltos ya cubre casi todo el catálogo, deja de ser una relación demostrable.
> **Dos**: la fuerza de un directo es su peso; la de un indirecto es el eslabón más débil de la cadena, el mínimo entre los dos pesos.
> **Tres**: un indirecto solo entra si esa fuerza es al menos 1.5, es decir, ambos vínculos frecuentes.
> **Cuatro**: se ordenan primero los directos y luego los indirectos, y dentro de cada grupo por fuerza. Nunca se completa la lista con productos sin relación."

### 1:45 – 2:45 — Traza en pizarra (algoritmo)

**Mostrar**: la red de 9 productos de `acceptance_f3.py` dibujada, y la traza.

**Decir**:
> "Hagamos la traza desde `leche`. El BFS saca `leche` y descubre `cafe` y `pan`. Saca `cafe` y descubre `azucar`. Saca `pan` y descubre `jugo` y `mermelada`.
> Directos: `cafe` con 3.0 y `pan` con 2.5. Indirectos: `azucar` por `cafe`, mínimo entre 3.0 y 2.5, da 2.5. `mermelada` por `pan`, mínimo entre 2.5 y 2.0, da 2.0. **`jugo` se descarta**: su puente `pan` lo une con 1.0, así que el mínimo es 1.0, menor que 1.5.
> Resultado final: `cafe`, `pan`, `azucar`, `mermelada`."

### 2:45 – 5:15 — DEMO EN VIVO

**Pasar al navegador** en http://localhost:5173.

**(2:45-3:30) Caso normal — Leche entera**:
> Escribir "Leche" en el selector y elegirla.
>
> "Recibimos cinco sugerencias. Fíjense en la razón de cada una: la directa dice 'se compra junto con Leche entera casi siempre'. La indirecta, `Azúcar`, dice 'no se registra junto con Leche, pero sí con Café molido, que la acompaña casi siempre'. La razón sale del mismo cálculo que ordena la lista, no es un texto aparte."
>
> Clic en "Ver más recomendaciones" y abrir "¿Cómo se eligen estas recomendaciones?".

**(3:30-4:00) Red escasa — Cerveza lager**:
> "Cerveza solo se relaciona con agua. El sistema devuelve una recomendación y el mensaje dice explícitamente que no completa la lista con otros productos."

**(4:00-4:25) Grupos separados — Jabón de tocador**:
> "Jabón solo muestra Papel higiénico y Detergente. Ningún comestible: son otro grupo, no hay camino entre ellos y por eso no hay recomendación."

**(4:25-5:15) Los datos cambian la propuesta**:
> Ir a Catálogo y agregar un producto nuevo (por ejemplo, "Maní salado"). Mostrar que ahora Recomendaciones lo trata como producto sin relaciones: aparece el mensaje claro de "todavía no hay datos". Registrar una compra conjunta con Cerveza lager (frecuencia Frecuente) y volver a consultar.
>
> "El producto pasó de no tener recomendaciones a tenerlas, sin reiniciar nada. El grafo en RAM y la base SQLite se mantienen sincronizados."

*(Opcional, si sobra tiempo: abrir "Vista técnica" en el pie y mostrar el grafo y la traza del BFS.)*

### 5:15 – 5:45 — Complejidad

**Decir**:
> "El BFS está acotado al radio 2, así que solo toca los nodos y aristas cercanos al origen. Calcular los puentes recorre los vecinos de los vecinos del origen, O(suma de grados) y como máximo O(E). Para esta red es instantáneo, y la lista de adyacencia de F1 hace que `neighbors` y `has_edge` sean O(1)."

### 5:45 – 6:30 — Script de aceptación en vivo

**Pasar a la terminal libre**:
```powershell
cd backend
python scripts/acceptance_f3.py
```

Mientras corre:
> "Levanta su propio servidor con una base temporal y vacía. Imprime escenario, esperado, obtenido y pass o fail, y termina con error si algo falla."

Cuando aparezca el resumen, **23/23 PASS**:
> "Cubre red vacía, caso normal con el orden y la razón de cada recomendación, el filtro de vínculos débiles, red escasa y grupos separados, producto aislado, inexistente, límite inválido y el cambio de datos."

### 6:30 – 7:00 — Contribuciones del equipo

**Pasar al navegador** → página de contribuidores del repositorio.

**Decir** (ajustar a lo que cada uno hizo realmente):
> "[Quién] diseñó la regla y el núcleo; [quién] hizo el endpoint y el script de aceptación; [quién] rehízo la interfaz. Cada aporte está en su pull request. La bitácora de IA de F3 en `docs/bitacora-ia-f3.md` documenta qué propuso la IA, qué aceptamos o rechazamos y cómo lo verificamos."

---

## Preguntas (3 min) — anticipar

### 1. "¿Por qué el umbral es 1.5?"
> Es el primer escalón de "frecuente" en la escala de pesos del seed. Con 1.0, que es "esperable", casi cualquier par de productos de la red quedaría conectado y la lista dejaría de discriminar. Lo justificamos con el seed: no está calibrado con datos reales.

### 2. "¿Por qué directos antes que indirectos y no un puntaje combinado?"
> Con un puntaje único un indirecto de 1.5 podría superar a un directo de 1.0, y el encargado no podría explicar por qué se propone algo que no se compra junto antes de algo que sí. Ordenar por grupo mantiene la explicación en una frase.

### 3. "¿Por qué el mínimo y no el promedio o el producto de los pesos?"
> Una cadena es tan fuerte como su eslabón más débil. Si pan-jugo es ocasional, no importa que leche-pan sea casi siempre: la relación leche-jugo sigue siendo débil. El promedio taparía ese eslabón flojo.

### 4. "¿Por qué solo 2 saltos?"
> En el seed, a 3 saltos el recorrido ya alcanza entre 58 % y 79 % del catálogo. Recomendar eso es casi "todo el catálogo", justo lo que el brief pide evitar.

### 5. "¿Qué pasa con empates?"
> Hay un orden determinista: grupo (directo o indirecto), fuerza, cantidad de puentes que respaldan y, al final, el id. Así el resultado se puede reproducir a mano.

### 6. "¿Qué sesgos o límites tiene la regla?"
> Sesgo de popularidad: lo que ya se vende junto se sigue recomendando y los productos nuevos quedan fuera, es el arranque en frío. Solo usa co-compra: no considera precio, margen, inventario ni temporada. Y es simétrica, porque el grafo es no dirigido. Está documentado en `docs/decisiones.md`.

### 7. "¿Qué pasa con un producto nuevo sin compras?"
> Se trata como aislado: la API responde 200 con lista vacía y un mensaje que lo explica, y la interfaz lo comunica sin inventar nada.

### 8. "¿Y si dos productos son de grupos distintos?"
> No hay camino entre ellos, así que nunca se recomiendan entre sí. Es el caso de higiene contra comestibles en el seed.

### 9. "¿Por qué la interfaz ya no muestra el grafo?"
> Por recomendación del docente: el usuario final, un encargado de ventas, no necesita entender grafos, solo recibir recomendaciones con su razón. Conservamos grafo, traza y grupos en una vista técnica para el equipo.

### 10. "¿Cómo usaron la IA responsablemente?"
> La IA propuso la regla y generó código; nosotros la trazamos a mano con la red de nueve productos, la comparamos con el script de aceptación y ajustamos cosas. Todo está en `docs/bitacora-ia-f3.md`. *(Apóyate en lo que de verdad hicieron, y menciona un ejemplo concreto de algo que revisaron o cambiaron.)*

### 11. "¿Qué cambiaría con un grafo dirigido?"
> Podríamos modelar "se recomienda después de". Costaría detectar ciclos y cubrir ese caso en la aceptación, y para esta pyme no hay valor claro todavía. La decisión está en `docs/decisiones.md` desde F1.

---

## Guión del video (≤ 3 min)

### 0:00 – 0:20 — Intro
> "ComercioConecta, Feature 3: una propuesta comercial con razón para cada producto recomendado."

### 0:20 – 1:40 — Demo visual (grabar en http://localhost:5173)
- Leche entera → sugerencias y razones, abrir "¿Cómo se eligen?" (30 seg)
- Cerveza lager → una sola recomendación y el mensaje de que no se rellena (15 seg)
- Jabón de tocador → solo su grupo (15 seg)
- Catálogo: producto nuevo → sin datos; registrar compra conjunta → aparece la recomendación (20 seg)

### 1:40 – 2:10 — Regla y traza
- Slide con la red de 9 productos y la traza desde `leche` (30 seg)

### 2:10 – 2:45 — Script de aceptación
Grabar la terminal con `python scripts/acceptance_f3.py` y mostrar el resumen.

### 2:45 – 3:00 — Cierre
> "Regla clara, razón por producto y sin inventar relaciones. Backend FastAPI con grafo propio, frontend React."

---

## Checklist antes de salir a presentar

- [ ] Backend corriendo (`uvicorn app.main:app --reload`)
- [ ] Frontend corriendo (`npm run dev`)
- [ ] Terminal libre para `python scripts/acceptance_f3.py`
- [x] Script corrido: 23/23 PASS (volver a correrlo antes de presentar)
- [ ] Haber trazado a mano `leche` en la red de 9 productos
- [ ] Seed limpio (si probaste cosas antes, borra `backend/data/comercio.db` para que vuelva a cargar el seed)
- [ ] Pestañas listas: `recommend.py` en VS Code, Swagger `/docs`, contribuidores del repositorio
- [ ] `docs/bitacora-ia-f3.md` completada con lo que realmente hicieron
- [ ] Video grabado y subido (link en la entrega)
- [ ] Tag de F3 creado en GitHub

## Qué NO decir (errores comunes)

- No digas "usamos NetworkX" para la regla: está prohibido para algoritmos.
- No digas que el umbral 1.5 sale de datos reales: es una decisión justificada con el seed.
- No prometas la Feature 4 como si ya estuviera. Di "dejamos la base para integrar todo".
- No digas "lo hizo la IA" sin matizar. Di "generamos con asistencia de IA, trazamos a mano y verificamos con el script; está en la bitácora".
- No afirmes un resultado del script sin haberlo corrido ese mismo día.
