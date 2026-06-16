from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO
from app.schemas.esquemas import UsuarioDTO, LoteMonitoreoDTO
from app.core.dependencias_rbac import requiere_admin, requiere_auxiliar_mayor

router = APIRouter(prefix="/monitoreo", tags=["Monitoreo de Sistema"])

@router.get("/empleados", response_model=List[UsuarioDTO])
def obtener_empleados(db: Session = Depends(get_db), usuario = Depends(requiere_admin)):
    """Solo ejecutable por Facultativo/Admin. Incluye empleados activos e inactivos (Soft Delete)"""
    return UsuarioDAO.listar_empleados(db)

@router.get("/almacenamiento", response_model=List[LoteMonitoreoDTO])
def obtener_estado_almacenamiento(db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_mayor)):
    return InventarioDAO.obtener_estado_almacenamiento(db)

@router.get("/alertas-caducidad", response_model=List[LoteMonitoreoDTO])
def obtener_alertas_caducidad(db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_mayor)):
    return InventarioDAO.obtener_alertas_caducidad(db, dias_limite=30)