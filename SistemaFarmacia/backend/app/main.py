from fastapi import FastAPI
from app.db.database import engine, Base
from app.models.entidades import Usuario, Laboratorio, Producto, Lote
from app.api import auth, monitoreo, test_endpoints, operaciones, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema Farmacias Sol",
    description="Backend para el control de lote, vencimientos y trazabilidad sanitaria - PMV",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api")
app.include_router(monitoreo.router, prefix="/api")
app.include_router(operaciones.router, prefix="/api")
app.include_router(test_endpoints.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def raiz():
    return {"status": "Servidor Backend Operativo - Sistema Farmacias Sol"}