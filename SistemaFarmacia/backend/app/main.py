from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.models.entidades import (
    Usuario, Laboratorio, Producto, Lote,
    Tarea, ZonaAlmacen, Venta, ItemVenta, RecetaMagistral,
    PedidoSolicitadoItem, InsumoRecetaRequerido, IndicacionAmbiental
)
from app.api import auth, monitoreo, test_endpoints, operaciones, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema Farmacias Sol",
    description="Backend para el control de lote, vencimientos y trazabilidad sanitaria - PMV",
    version="1.0.0"
)

@app.on_event("startup")
def sembrar_zonas_almacen_por_defecto():
    """
    Autogenera las 4 zonas físicas fijas (A, B refrigerado; C, D ambiente)
    con 1000 unidades de capacidad cada una, solo si la tabla está vacía.
    Evita que el Auxiliar Mayor tenga que crear zonas manualmente con
    riesgo de error de tipeo, y resuelve que capacidad_almacen/zonas_almacen
    quedara vacía sin que nadie la poblara explícitamente.
    """
    db: Session = SessionLocal()
    try:
        if db.query(ZonaAlmacen).first() is not None:
            return  # ya sembrado en un arranque anterior

        zonas_por_defecto = [
            ZonaAlmacen(codigo="A", tipo_ambiental=IndicacionAmbiental.REFRIGERADO, capacidad_maxima_unidades=1000),
            ZonaAlmacen(codigo="B", tipo_ambiental=IndicacionAmbiental.REFRIGERADO, capacidad_maxima_unidades=1000),
            ZonaAlmacen(codigo="C", tipo_ambiental=IndicacionAmbiental.AMBIENTE, capacidad_maxima_unidades=1000),
            ZonaAlmacen(codigo="D", tipo_ambiental=IndicacionAmbiental.AMBIENTE, capacidad_maxima_unidades=1000),
        ]
        db.add_all(zonas_por_defecto)
        db.commit()
    finally:
        db.close()

app.include_router(auth.router, prefix="/api")
app.include_router(monitoreo.router, prefix="/api")
app.include_router(operaciones.router, prefix="/api")
app.include_router(test_endpoints.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def raiz():
    return {"status": "Servidor Backend Operativo - Sistema Farmacias Sol"}