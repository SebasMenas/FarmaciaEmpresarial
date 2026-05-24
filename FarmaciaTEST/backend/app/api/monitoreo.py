from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO
from app.schemas.esquemas import UsuarioDTO, LoteMonitoreoDTO

router = APIRouter(prefix="/monitoreo", tags=["Monitoreo de Sistema"])

@router.get("/empleados", response_model=List[UsuarioDTO])
def obtener_empleados(db: Session = Depends(get_db)):
    """Ruta destinada a la pantalla del Administrador para el control de personal"""
    return UsuarioDAO.listar_empleados(db)

@router.get("/almacenamiento", response_model=List[LoteMonitoreoDTO])
def obtener_estado_almacenamiento(db: Session = Depends(get_db)):
    """Ruta destinada al Administrador y Auxiliar Mayor para visualizar la capacidad e inventario"""
    return InventarioDAO.obtener_estado_almacenamiento(db)

@router.get("/alertas-caducidad", response_model=List[LoteMonitoreoDTO])
def obtener_alertas_caducidad(db: Session = Depends(get_db)):
    """Ruta destinada a la pantalla del Auxiliar Mayor para control de vencimientos próximos"""
    # Filtra por defecto los productos que vencen en los próximos 30 días
    return InventarioDAO.obtener_alertas_caducidad(db, dias_limite=30)