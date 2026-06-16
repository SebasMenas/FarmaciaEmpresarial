from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.db.daos import UsuarioDAO
from app.models.entidades import Usuario, RolUsuario
from app.core.dependencias_rbac import requiere_admin
from app.core.security import Security

router = APIRouter(prefix="/admin", tags=["Administración"])

class EmpleadoCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=50)
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., description="Nombre real del empleado")
    apellidos: str = Field(..., description="Apellidos del empleado")
    rut: str = Field(..., description="Rol Único Tributario")
    rol: RolUsuario 
    credencial: str | None = Field(default=None, description="Código de supervisor (Opcional)")
    activo: bool = True

@router.post("/empleados", status_code=status.HTTP_201_CREATED)
def registrar_empleado(
    payload: EmpleadoCreate,
    db: Session = Depends(get_db),
    admin_user: Usuario = Depends(requiere_admin)
):
    usuario_existente = UsuarioDAO.obtener_por_username(db, payload.username)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya se encuentra registrado."
        )
    
    hashed_pwd = Security.obtener_password_hash(payload.password)
    
    try:
        nuevo_empleado = UsuarioDAO.crear_empleado(
            db=db,
            username=payload.username,
            password_hash=hashed_pwd,
            nombre=payload.nombre,
            apellidos=payload.apellidos,
            rut=payload.rut,
            rol=payload.rol,
            credencial=payload.credencial,
            activo=payload.activo
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de integridad: Posible duplicidad de RUT o restricción en base de datos."
        )
        
    return {
        "exito": True, 
        "mensaje": "Empleado registrado correctamente", 
        "id_empleado": nuevo_empleado.id
    }