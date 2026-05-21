from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencias import obtener_usuario_actual
from app.db.database import get_db
from app.db.usuario_dao import UsuarioDAO
from app.schemas.usuario import PasswordUpdate, UsuarioCreate, UsuarioResponse
from app.api.dependencias import requerir_admin

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
@router.get("/doctores", response_model=List[UsuarioResponse])
def listar_doctores(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual) # Cualquier usuario con token válido puede verlos
):
    """
    Endpoint PROTEGIDO. Devuelve la lista de todos los doctores.
    """
    dao = UsuarioDAO(db)
    return dao.obtener_doctores()

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(
    usuario_in: UsuarioCreate, 
    db: Session = Depends(get_db),
    usuario_operador: dict = Depends(obtener_usuario_actual) 
):
    """
    Endpoint con lógica de permisos:
    - ADMIN: Puede registrar cualquier rol.
    - DOCTOR: Solo puede registrar PACIENTES.
    - PACIENTE: No tiene acceso a este endpoint.
    """
    dao = UsuarioDAO(db)
    rol_operador = str(usuario_operador.get("rol", "")).upper()
    nuevo_rol_solicitado = usuario_in.rol.strip().upper()

    #Validacion
    if rol_operador == "DOCTOR":
        if nuevo_rol_solicitado != "PACIENTE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Como Doctor, solo tienes permiso para registrar nuevos Pacientes."
            )
    elif rol_operador == "ADMIN":
        pass # El admin puede crear cualquier rol
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para registrar usuarios."
        )
    
    if dao.obtener_por_username(usuario_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario (RUT) ya está registrado."
        )
    
    usuario_in.rol = nuevo_rol_solicitado
    return dao.crear_usuario(usuario_in)

@router.get("/pacientes", response_model=List[UsuarioResponse])
def listar_pacientes(
    db: Session = Depends(get_db),
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    """
    Devuelve la lista de todos los usuarios con rol PACIENTE.
    Cualquier usuario autenticado puede consultarlos (necesario para el Doctor).
    """
    dao = UsuarioDAO(db)
    return dao.obtener_usuarios_por_rol("PACIENTE")

@router.patch("/me/password")
def actualizar_mi_password(
        datos_pwd: PasswordUpdate,
        db: Session = Depends(get_db),
        usuario_actual: dict = Depends(obtener_usuario_actual)
):
    dao = UsuarioDAO(db)
    try:
        dao.cambiar_password(usuario_actual["id"], datos_pwd)
        return {"mensaje": "Contraseña actualizada exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))