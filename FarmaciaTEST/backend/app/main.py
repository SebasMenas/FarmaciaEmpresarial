from fastapi import FastAPI
from app.db.database import engine, Base
from app.models.entidades import Usuario, Laboratorio, Producto, Lote # metadata para que SQLAlchemy reconozca las tablas a construir
from app.api import auth, monitoreo, test_endpoints


# Fuerza la creación de esquemas y tablas si no existen en Neon
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema Farmacias Sol",
    description="Backend para el control de lote, vencimientos y trazabilidad sanitaria - PMV",
    version="1.0.0"
)

# Rutas
app.include_router(auth.router, prefix="/api")
app.include_router(monitoreo.router, prefix="/api")
app.include_router(test_endpoints.router, prefix ="/api")

@app.get("/")
def raiz():
    return {"status": "Servidor Backend Operativo"}