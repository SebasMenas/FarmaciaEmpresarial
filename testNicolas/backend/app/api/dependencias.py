from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.security import SECRET_KEY, ALGORITHM

# Ruta endpoint de logins
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    """
    Verifica que el token sea válido y no haya expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        usuario_id: int = payload.get("id")
        
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
            
        # Retorna datos del usuarios extraidos del token
        return {"username": username, "rol": rol, "id": usuario_id}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="El token ha expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

def requerir_admin(usuario_actual: dict = Depends(obtener_usuario_actual)):
    """
    Filtro para verificar que el rol de usuario sea "ADMIN"
    """
    if usuario_actual.get("rol") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Privilegios insuficientes. Solo un administrador puede realizar esta acción."
        )
    return usuario_actual

def requerir_rol_agendamiento(usuario_actual: dict = Depends(obtener_usuario_actual)):
    """
    Filtro que impide a los Administradores agendar citas.
    """
    rol_normalizado = str(usuario_actual.get("rol", "")).strip().upper()
    
    if rol_normalizado == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Operación denegada. Los administradores solo tienen permisos de lectura sobre las citas."
        )
    
    return usuario_actual