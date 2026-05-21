from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.schemas.usuario import PasswordUpdate, UsuarioCreate
from app.core.security import Security

class UsuarioDAO:
    def __init__(self, db: Session):
        self.db = db

    def obtener_por_username(self, username: str):
        return self.db.query(Usuario).filter(Usuario.username == username).first()
    
    def obtener_doctores(self):
        """Consulta SQLAlchemy para traer solo a los usuarios con rol DOCTOR"""
        return self.db.query(Usuario).filter(Usuario.rol == "DOCTOR").all()
    
    def crear_usuario(self, usuario_in: UsuarioCreate):
        # Hashea la contraseña antes de crear el modelo de SQLAlchemy
        password_segura = Security.generar_hash(usuario_in.password)
        
        # Mapea el Schema (Pydantic) al Modelo (SQLAlchemy)
        db_usuario = Usuario(
            username=usuario_in.username,
            password_hash=password_segura,
            nombre=usuario_in.nombre,
            apellidos=usuario_in.apellidos,
            rut=usuario_in.rut,
            sexo=usuario_in.sexo,
            rol=usuario_in.rol
        )
        
        self.db.add(db_usuario)
        self.db.commit()
        self.db.refresh(db_usuario)
        return db_usuario
    
    def obtener_usuarios_por_rol(self, rol: str):
        """Consulta SQLAlchemy para traer usuarios filtrados por su rol (PACIENTE, DOCTOR, etc.)"""
        return self.db.query(Usuario).filter(Usuario.rol == rol.upper()).all()
    
    def cambiar_password(self, usuario_id: int, passwords: PasswordUpdate):

        usuario = self.db.query(Usuario).filter(Usuario.id == usuario_id).first()

        if not usuario:
            raise ValueError("Usuario no encontrado.")
        
        elif not Security.verificar_password(passwords.password_actual, usuario.password_hash):
            raise ValueError("La contraseña actual no es correcta.")

        usuario.password_hash = Security.generar_hash(passwords.password_nueva)
        self.db.commit()
        
        return True
        