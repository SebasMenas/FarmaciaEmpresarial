from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.daos import UsuarioDAO
from app.schemas.esquemas import TokenResponse
from app.core.security import Security

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(solicitud: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = UsuarioDAO.obtener_por_username(db, solicitud.username)
    if not usuario or not Security.verificar_password(solicitud.password, str(usuario.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    datos_token = {"sub": usuario.username, "id": usuario.id, "rol": usuario.rol}
    token = Security.crear_token_acceso(datos_token)
    
    return {"access_token": token, "token_type": "bearer", "rol": usuario.rol}