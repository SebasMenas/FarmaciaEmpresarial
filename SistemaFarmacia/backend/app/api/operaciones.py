from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from app.db.database import get_db
from app.models.entidades import Lote, EstadoLote, IndicacionAmbiental, Usuario, RolUsuario
from app.core.dependencias_rbac import requiere_auxiliar_mayor, requiere_auxiliar_diplomado

router = APIRouter(prefix="/operaciones", tags=["Lógica de Operaciones (Fases 2 y 3)"])

class UbicacionPayload(BaseModel):
    ubicacion: str
    temperatura_zona: IndicacionAmbiental

@router.put("/almacenar/{lote_id}")
def almacenar_lote(lote_id: int, payload: UbicacionPayload, db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_mayor)):
    """Fase 2: Condicionamiento ambiental. Evita ubicar productos erróneamente."""
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    # Condicionamiento ambiental
    if lote.producto.indicacion_ambiental != payload.temperatura_zona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"codigo_error": "ERROR_AMBIENTAL", "mensaje": "La ubicación no cumple con la ficha técnica del producto."}
        )
    
    lote.ubicacion_almacen = payload.ubicacion
    db.commit()
    return {"exito": True, "detalle": "Lote almacenado correctamente"}

class ManufacturaPayload(BaseModel):
    lote_id: int
    credencial_supervisor: str

@router.post("/manufactura/iniciar")
def iniciar_manufactura(payload: ManufacturaPayload, db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_diplomado)):
    """Fase 3: Validación RBAC Activa y Bloqueo Pesimista."""
    supervisor = db.query(Usuario).filter(Usuario.credencial == payload.credencial_supervisor, Usuario.rol == RolUsuario.ADMIN, Usuario.activo == True).first()
    if not supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail={"codigo_error": "FIRMA_INVALIDA", "mensaje": "Token de supervisor facultativo inválido o ausente."}
        )
    
    try:
        # Control de Concurrencia
        lote = db.query(Lote).filter(
            Lote.id == payload.lote_id, 
            Lote.estado == EstadoLote.DISPONIBLE
        ).with_for_update(nowait=True).first()
        
        if not lote:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail={"codigo_error": "LOTE_RESERVADO", "mensaje": "Lote agotado o en uso por otra transacción comercial."}
            )
        
        # Transición de Estado y Timeout
        lote.estado = EstadoLote.RESERVADO_MANUFACTURA
        lote.reservado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()
        
        return {"exito": True, "codigo_lote": lote.codigo_lote, "estado": lote.estado}
        
    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail={"codigo_error": "LOTE_BLOQUEADO", "mensaje": "El recurso se encuentra bloqueado transaccionalmente."}
        )