from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.usuario_dao import UsuarioDAO
from app.core.security import Security

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Verifica credenciales y devuelve un Token JWT.
    OAuth2PasswordRequestForm espera los campos 'username' y 'password'.
    """
    dao = UsuarioDAO(db)
    usuario = dao.obtener_por_username(form_data.username)
    
    # Verificar si el usuario existe
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos"
        )
    
    # Verificar si la contraseña coincide con el hash
    if not Security.verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos"
        )
    
    # Crear el Token con la información del usuario (id y rol)
    token = Security.crear_token_acceso(
        datos={"sub": usuario.username, "rol": usuario.rol, "id": usuario.id}
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "nombre": usuario.nombre,
            "rol": usuario.rol
        }
    }