# Brief de cliente — ComercioConecta

## Cliente y problema

ComercioConecta es una pyme que agrupa tiendas de barrio y quiere entender relaciones entre productos comprados juntos para proponer combinaciones comerciales razonables. Actualmente las recomendaciones salen de intuición y no pueden identificar grupos de productos relacionados.

## Usuarios

- **Analista comercial:** carga productos y relaciones de compra conjunta.
- **Encargado de ventas:** consulta productos relacionados y grupos comerciales.

## Alcance

Trabajen con datos sintéticos de productos y relaciones de co-compra. No implementen modelos de machine learning, perfiles personales, datos reales de clientes, precios dinámicos ni campañas automatizadas. Expliquen si la relación producto–producto es simétrica y qué podría representar su peso.

## Feature 1 — Red comercial inicial

### Valor de negocio
El analista registra productos y relaciones de compra conjunta que pueden consultarse.

### Debe permitir

- crear/listar productos y relaciones válidas;
- rechazar duplicados, productos inexistentes y pesos inválidos si los usan;
- mostrar la red por API e interfaz mínima;
- justificar si el grafo es dirigido o no dirigido y la representación elegida.

### Pistas, no receta

Una relación “se compran juntos” parece simétrica; una relación “se recomienda después de” puede no serlo. Elijan según el negocio y mantengan esa decisión consistente en toda la API.

## Feature 2 — Exploración de relaciones

### Valor de negocio
El encargado identifica productos relacionados desde uno de interés y distingue grupos desconectados.

### Debe permitir

- consultar productos alcanzables desde un producto mediante un recorrido propio;
- mostrar al menos una consulta de grupo o componente relacionado;
- manejar producto inexistente, producto aislado y red vacía;
- explicar qué nivel de relación tiene sentido para el usuario; no conviertan “todo el catálogo” en recomendación automática.

### Pistas, no receta

Usen una traza de BFS/DFS con un límite de profundidad que puedan justificar desde negocio. Investigen componentes conexos si desean explicar grupos independientes.

## Feature 3 — Propuesta comercial justificable

### Valor de negocio
El encargado recibe una propuesta de productos relacionados con una explicación basada en la red, no una lista aleatoria.

### Debe permitir

- definir una regla clara y documentada para priorizar o filtrar relaciones;
- usar información resultante de recorridos, conexiones o pesos que ustedes modelaron;
- devolver también la razón de la recomendación: relación directa, alcance limitado, fuerza de vínculo u otra regla explícita;
- evitar recomendar el mismo producto o elementos sin relación demostrable;
- demostrar escenarios con red escasa y grupos separados.

### Pistas, no receta

No es necesario usar IA ni machine learning. Lo valioso es convertir una regla de negocio explícita en una consulta de grafo verificable. Defiendan límites y sesgos de su regla.

## Feature 4 — Panel comercial demostrable

### Valor de negocio
El cliente explora relaciones y entiende por qué el sistema propone una combinación.

### Debe permitir

- integrar carga, exploración y propuesta comercial;
- visualizar conexiones o grupos de modo útil para explicar una consulta;
- adaptar el cambio de requisito docente;
- ejecutar aceptación de caso normal, producto aislado, producto inexistente, red vacía y dato inválido;
- entregar evidencia completa de feature.

## Criterio de éxito del cliente

En una demo, el analista registra relaciones, el encargado consulta un producto y recibe una propuesta explicable. Si no hay conexiones, el sistema lo comunica sin inventar recomendaciones.
