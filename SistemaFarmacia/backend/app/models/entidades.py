import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, DateTime, Date, CheckConstraint, func
from sqlalchemy.orm import relationship, mapped_column
from app.db.database import Base

class RolUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    AUX_MAYOR = "AUX_MAYOR"
    AUX_DIPLOMADO = "AUX_DIPLOMADO"
    TECNICO = "TECNICO"

class TipoProducto(str, enum.Enum):
    MEDICAMENTO = "MEDICAMENTO"
    INSUMO_MEDICO = "INSUMO_MEDICO"
    COSMETICO = "COSMETICO"

class IndicacionAmbiental(str, enum.Enum):
    AMBIENTE = "AMBIENTE"
    REFRIGERADO = "REFRIGERADO"

class EstadoLote(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    PROXIMO_A_VENCER = "PROXIMO_A_VENCER"
    RESERVADO_VENTA = "RESERVADO_VENTA"
    RESERVADO_MANUFACTURA = "RESERVADO_MANUFACTURA"
    BLOQUEADO = "BLOQUEADO"
    CUARENTENA = "CUARENTENA"
    RETIRADO = "RETIRADO"
    AGOTADO = "AGOTADO"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    rut = Column(String(12), unique=True, nullable=False, index=True)
    rol = Column(Enum(RolUsuario), nullable=False)
    credencial = Column(String(100), unique=True, nullable=True)
    activo = Column(Boolean, default=True, nullable=False) # Implementacion Soft Delete

class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    certificado = Column(Boolean, default=True, nullable=False)
    lotes = relationship("Lote", back_populates="laboratorio", passive_deletes="all")

class Producto(Base):
    __tablename__ = "productos"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False, index=True)
    componente_activos = Column(String(150), nullable=True)
    concentracion = Column(String(50), nullable=True)
    tipo_producto = Column(Enum(TipoProducto), nullable=False)
    indicacion_ambiental = Column(Enum(IndicacionAmbiental), nullable=False)
    stock_min = Column(Integer, default=0, nullable=False)
    stock_max = Column(Integer, nullable=False)
    lotes = relationship("Lote", back_populates="producto", passive_deletes="all")

class Lote(Base):
    __tablename__ = "lotes"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_lote = mapped_column(String(50), unique=True, nullable=False, index=True)
    codigo_trazabilidad = mapped_column(String(100), unique=True, nullable=False, index=True)
    producto_id = mapped_column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    laboratorio_id = mapped_column(Integer, ForeignKey("laboratorios.id", ondelete="RESTRICT"), nullable=False)
    cantidad = mapped_column(Integer, nullable=False)
    fecha_ingreso = mapped_column(DateTime, server_default=func.now(), nullable=False)
    fecha_caducidad = mapped_column(Date, nullable=False)
    ubicacion_almacen = mapped_column(String(100), nullable=True)
    estado = mapped_column(Enum(EstadoLote), default=EstadoLote.DISPONIBLE, nullable=False)
    reservado_hasta = mapped_column(DateTime, nullable=True) # Implementacion Timeout de Concurrencia

    producto = relationship("Producto", back_populates="lotes")
    laboratorio = relationship("Laboratorio", back_populates="lotes")

    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="check_cantidad_positiva"),
    )