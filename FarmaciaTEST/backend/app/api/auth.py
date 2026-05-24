from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.daos import UsuarioDAO
from app.schemas.esquemas import LoginRequest, TokenResponse
from app.core.security import Security

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(solicitud: LoginRequest, db: Session = Depends(get_db)):
    # Buscar usuario en la base de datos
    usuario = UsuarioDAO.obtener_por_username(db, solicitud.username)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas")
    
    # Verificar hash de la contraseña
    if not Security.verificar_password(solicitud.password, str(usuario.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas")
    
    # Generar el Payload del token con ID y Rol
    datos_token = {
        "sub": usuario.username,
        "id": usuario.id,
        "rol": usuario.rol
    }
    
    token = Security.crear_token_acceso(datos_token)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol
    }

