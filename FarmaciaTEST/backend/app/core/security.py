import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # El token expira en 1 hora

class Security:
    @staticmethod
    def verificar_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    @staticmethod
    def crear_token_acceso(datos: dict) -> str:
        a_copiar = datos.copy()
        expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        a_copiar.update({"exp": expiracion})
        
        # Genera el JWT uniendo Header, Payload y Firma
        token_jwt = jwt.encode(a_copiar, SECRET_KEY, algorithm=ALGORITHM)
        return token_jwt
    
    @staticmethod
    def obtener_password_hash(password: str) -> str:

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')