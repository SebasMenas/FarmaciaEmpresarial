from fastapi import FastAPI
from app.db.database import engine, Base
from app.models import usuario, cita
from app.api import rutas_usuarios
from app.api import rutas_auth
from app.api import rutas_citas

app = FastAPI(
    title="API CESFAM",
    description="Backend para gestión de citas médicas",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

# --- REGISTRO DE RUTAS ---
app.include_router(rutas_usuarios.router, prefix="/api")
app.include_router(rutas_auth.router, prefix="/api")
app.include_router(rutas_citas.router, prefix="/api")

@app.get("/")
def estado_servidor():
    return {"mensaje": "El servidor FastAPI está en línea."}