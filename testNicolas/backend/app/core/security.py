import bcrypt
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

# Configuraciones desde el .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # El token durará 1 hora

class Security:
    @staticmethod
    def generar_hash(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')

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
        """Genera un token JWT firmado."""
        a_copiar = datos.copy()
        expiracion = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        a_copiar.update({"exp": expiracion})
        
        # Firmar el token con la SECRET_KEY
        token_jwt = jwt.encode(a_copiar, SECRET_KEY, algorithm=ALGORITHM)
        return token_jwt