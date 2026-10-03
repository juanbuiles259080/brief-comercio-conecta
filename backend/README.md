# Backend — ComercioConecta

API REST sobre FastAPI con grafo propio y persistencia SQLite (módulo estándar `sqlite3`).

## Correr

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs OpenAPI (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Estructura

```
app/
├── main.py            Entrypoint FastAPI + CORS + registro de routers
├── config.py          Paths y constantes
├── schemas.py         DTOs Pydantic (ProductIn/Out, RelationIn/Out, NetworkOut)
├── api/               Routers HTTP
│   ├── products.py
│   ├── relations.py
│   └── network.py
├── core/              Lógica del dominio
│   ├── graph.py       Clase Graph propia (adjacency list)
│   └── errors.py      Excepciones de dominio
└── repository/        Acceso a SQLite
    ├── db.py
    ├── products_repo.py
    └── relations_repo.py

data/
├── comercio.db        (generado, no versionado)
└── seed.sql           Datos sintéticos iniciales

scripts/
└── acceptance.py      Script de aceptación F1
```

## Script de aceptación

```powershell
python scripts/acceptance.py
```

Debe ejecutarse con el backend ya corriendo en `http://localhost:8000`. Imprime cada escenario, lo esperado, lo obtenido y `PASS` / `FAIL`.
