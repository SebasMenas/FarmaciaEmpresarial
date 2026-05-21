from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.cita_dao import CitaDAO
from app.schemas.cita import CitaResponse, CitaCreate
from app.api.dependencias import obtener_usuario_actual, requerir_rol_agendamiento
from datetime import date
from typing import List

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.get("/dia/{fecha}", response_model=List[CitaResponse])
def listar_citas_por_dia(
    fecha: date, 
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    dao = CitaDAO(db)
    rol = str(usuario_actual.get("rol", "")).upper()
    user_id = usuario_actual.get("id")

    if rol == "PACIENTE":
        return dao.obtener_citas_por_paciente(fecha, paciente_id=user_id)
    if rol == "DOCTOR":
        return dao.obtener_citas_por_fecha(fecha, docente_id=usuario_actual["id"])
    
    elif rol == "PACIENTE":
        return dao.obtener_citas_por_paciente(fecha, paciente_id=usuario_actual["id"])
    return dao.obtener_citas_por_fecha(fecha)

@router.post("/", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
def agendar_cita(
    cita_in: CitaCreate,
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(requerir_rol_agendamiento) 
):
    """Crea una nueva cita. Bloqueado para Administradores."""
    dao = CitaDAO(db)
    try:
        return dao.crear_cita(cita_in, usuario_actual["id"], usuario_actual["rol"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.patch("/{cita_id}/cancelar")
def cancelar_cita_endpoint(
    cita_id: int, 
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    Endpoint para realizar la cancelación lógica de una cita.
    Cambia el estado de la cita a 0.
    """
    dao = CitaDAO(db)
    try:
        dao.cancelar_cita(cita_id)
        return {"mensaje": "Cita cancelada exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=str(e)
        )