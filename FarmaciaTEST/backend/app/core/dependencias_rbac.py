from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.entidades import RolUsuario

# Instancia que FastAPI usa para extraer el token del header "Authorization: Bearer ..."
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Se inyecta oauth2_scheme como dependencia de token
def verificar_token(token: str = Depends(oauth2_scheme)): 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str | None = payload.get("sub")
        rol: str | None = payload.get("rol")
        
  
        #Si alguno es None, el token esta corrupto o manipulado.
        if username is None or rol is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de acceso no válidas o token corrupto",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {"username": username, "rol": rol}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError: # Captura cualquier otro error de firma o decodificación
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma del token inválida",
            headers={"WWW-Authenticate": "Bearer"}
        )

def requiere_admin(usuario: dict = Depends(verificar_token)):
    if usuario.get("rol") != RolUsuario.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Privilegios insuficientes (Requiere ADMIN)"
        )
    return usuario

def requiere_auxiliar_mayor(usuario: dict = Depends(verificar_token)):
    roles_permitidos = [RolUsuario.ADMIN.value, RolUsuario.AUX_MAYOR.value]
    if usuario.get("rol") not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Privilegios insuficientes (Requiere Auxiliar Mayor o superior)"
        )
    return usuario

def requiere_auxiliar_diplomado(usuario: dict = Depends(verificar_token)):
    # Asumiendo que el ADMIN tambien puede supervisar esta vista
    roles_permitidos = [RolUsuario.ADMIN.value, RolUsuario.AUX_DIPLOMADO.value]
    if usuario.get("rol") not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Privilegios insuficientes (Requiere Auxiliar Diplomado)"
        )
    return usuario

def requiere_tecnico(usuario: dict = Depends(verificar_token)):
    # Como todos los roles autenticados son igual o superiores a Tecnico en jerarqia,
    # simplemente validamos que el token sea correcto devolviendo el usuario.
    return usuario