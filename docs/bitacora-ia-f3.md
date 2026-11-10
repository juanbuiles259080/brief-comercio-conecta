# Bitácora de uso de IA — Feature 3

> **BORRADOR para completar.** La columna "Acepté o rechacé y por qué" y "Cómo lo verifiqué" son decisiones y pruebas **de ustedes**: revisen cada fila, corrijan lo que no coincida con lo que realmente hicieron y completen lo que falte antes de entregar.

| Decisión o pieza | Herramienta/objetivo de IA | Propuesta recibida | Acepté o rechacé y por qué | Cómo la verifiqué |
|---|---|---|---|---|
| Regla de recomendación (directos + indirectos con umbral) | Proponer una regla explicable sobre el BFS de F2 | Directos primero; indirectos a 2 saltos con fuerza `min(w1, w2) >= 1.5`; nunca rellenar | _Completar_ | Traza manual `python -m app.core.recommend` + escenarios B-D de `acceptance_f3.py` |
| Orden por grupo (no puntaje único) | Alternativas de ordenamiento | Tier directo/indirecto y luego fuerza, respaldo, id | _Completar_ | Escenario H: un directo débil queda antes que un indirecto fuerte |
| Umbral 1.5 | Justificar un valor | Primer escalón "frecuente" de la escala del seed | _Completar_ | Probar con el seed (`leche`, `arroz`, `agua`, `cerveza`) y ver que la lista discrimina |
| Endpoint `GET /recommendations/{id}` | Generar router, schemas y mensajes | Router con `limit` 1-10, `reason` y `rule` | _Completar_ | `acceptance_f3.py` (casos normal, aislado, inexistente, límite inválido) |
| Script `acceptance_f3.py` | Generar escenarios | Red de prueba + 8 secciones | _Completar_ | Ejecutarlo y comparar cada ESPERADO con una traza a mano |
| Rediseño de la interfaz | Vista centrada en recomendaciones, catálogo en lenguaje de negocio, grafo en vista técnica | Tres vistas y componentes nuevos | _Completar_ | `npm run build`, `npm run lint` y recorrer los casos en el navegador |
