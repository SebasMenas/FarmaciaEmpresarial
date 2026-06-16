from typing import Optional
from sqlalchemy.orm import Session
from app.models.entidades import Usuario, Lote, Producto

class UsuarioDAO:
    @staticmethod
    def obtener_por_username(db: Session, username: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.username == username).first()

    @staticmethod
    def listar_empleados(db: Session):
        """Retorna todos los empleados registrados para la pantalla de Admin"""
        return db.query(Usuario).all()
    
    @staticmethod
    def crear_empleado(
        db: Session, 
        username: str, 
        password_hash: str, 
        nombre: str,
        apellidos: str,
        rut: str,
        rol: str, 
        credencial: str | None = None,
        activo: bool = True
    ) -> Usuario:
        nuevo_usuario = Usuario(
            username=username,
            password_hash=password_hash,
            nombre=nombre,
            apellidos=apellidos,
            rut=rut,
            rol=rol,
            credencial=credencial,
            activo=activo
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario

class InventarioDAO:
    @staticmethod
    def obtener_estado_almacenamiento(db: Session):
        """Retorna todos los lotes activos con sus relaciones para las pantallas de monitoreo"""
        return db.query(Lote).join(Lote.producto).join(Lote.laboratorio).all()

    @staticmethod
    def obtener_alertas_caducidad(db: Session, dias_limite: int = 30):
        """Retorna lotes cuya fecha de caducidad esté dentro del umbral para la pantalla del Auxiliar Mayor"""
        from datetime import date, timedelta
        fecha_limite = date.today() + timedelta(days=dias_limite)
        return db.query(Lote).filter(
            Lote.fecha_caducidad <= fecha_limite,
            Lote.cantidad > 0
        ).all()