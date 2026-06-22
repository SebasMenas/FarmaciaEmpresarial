from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO, MonitoreoDAO
from app.schemas.esquemas import UsuarioDTO, LoteMonitoreoDTO, CapacidadAlmacenDTO, TareaDTO, TareaCreate, TareaEstadoUpdate, LoteVentaDTO
from app.models.entidades import Usuario
from app.core.dependencias_rbac import requiere_auxiliar_mayor, verificar_token, requiere_acceso_catalogo_venta

router = APIRouter(prefix="/monitoreo", tags=["Monitoreo de Sistema"])

@router.get("/empleados", response_model=List[UsuarioDTO])
def obtener_empleados(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_mayor)):
    """Solo ejecutable por Facultativo/Admin. Incluye empleados activos e inactivos (Soft Delete)"""
    return UsuarioDAO.listar_empleados(db)

@router.get("/almacenamiento", response_model=List[LoteMonitoreoDTO])
def obtener_estado_almacenamiento(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_mayor)):
    return InventarioDAO.obtener_estado_almacenamiento(db)

@router.get("/productos-disponibles", response_model=List[LoteVentaDTO])
def obtener_productos_disponibles(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_acceso_catalogo_venta)):
    return InventarioDAO.obtener_disponibles_para_venta(db)

@router.get("/alertas-caducidad", response_model=List[LoteMonitoreoDTO])
def obtener_alertas_caducidad(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_mayor)):
    return InventarioDAO.obtener_alertas_caducidad(db, dias_limite=30)

@router.get("/capacidad", response_model=List[CapacidadAlmacenDTO])
def obtener_capacidad_volumetrica(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_mayor)):
    """Retorna la agregación porcentual de capacidad instalada versus ocupación actual por zona ambiental."""
    return InventarioDAO.calcular_capacidad_por_zona(db)

@router.get("/tareas", response_model=List[TareaDTO])
def obtener_agenda_calendario(
    fecha: date = Query(..., description="Criterio de búsqueda cronológica (YYYY-MM-DD)"),
    db: Session = Depends(get_db), 
    usuario_auth: dict = Depends(requiere_auxiliar_mayor)
):
    """Consulta las tareas y checklists asignados a la fuerza laboral operativa según fecha calendario."""
    return MonitoreoDAO.obtener_tareas_por_fecha(db, fecha)

@router.post("/tareas", response_model=TareaDTO, status_code=status.HTTP_201_CREATED)
def agendar_tarea(
    payload: TareaCreate, 
    db: Session = Depends(get_db), 
    usuario_auth: dict = Depends(requiere_auxiliar_mayor)
):
    """Permite al Auxiliar Mayor delegar instrucciones operativas."""
    usuario_asignado = db.query(Usuario).filter(Usuario.id == payload.asignado_a_id).first()
    if not usuario_asignado:
        raise HTTPException(status_code=404, detail="El ID del empleado asignado no existe.")
    
    return MonitoreoDAO.crear_tarea(db, payload.descripcion, payload.asignado_a_id, payload.fecha)

@router.patch("/tareas/{id}/estado", response_model=TareaDTO)
def actualizar_checklist_tarea(
    id: int, 
    payload: TareaEstadoUpdate, 
    db: Session = Depends(get_db), 
    usuario_auth: dict = Depends(verificar_token) # Nivel de acceso base (Cualquier empleado)
):
    """Permite al personal marcar una instrucción como completada o pendiente."""
    tarea = MonitoreoDAO.actualizar_estado_tarea(db, id, payload.completada)
    if not tarea:
        raise HTTPException(status_code=404, detail="Registro de tarea no encontrado en la agenda.")
    return tarea