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

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    username = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash = mapped_column(String(255), nullable=False)
    nombre = mapped_column(String(100), nullable=False)
    apellidos = mapped_column(String(100), nullable=False)
    rut = mapped_column(String(12), unique=True, nullable=False, index=True)
    rol = mapped_column(Enum(RolUsuario), nullable=False)
    credencial = mapped_column(String(100), unique=True, nullable=True)
    activo = mapped_column(Boolean, default=True, nullable=False) # Implementacion Soft Delete

class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre = mapped_column(String(100), unique=True, nullable=False)
    certificado = mapped_column(Boolean, default=True, nullable=False)
    lotes = relationship("Lote", back_populates="laboratorio", passive_deletes="all")

class Producto(Base):
    __tablename__ = "productos"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre = mapped_column(String(150), nullable=False, index=True)
    componente_activos = mapped_column(String(150), nullable=True)
    concentracion = mapped_column(String(50), nullable=True)
    tipo_producto = mapped_column(Enum(TipoProducto), nullable=False)
    indicacion_ambiental = mapped_column(Enum(IndicacionAmbiental), nullable=False)
    stock_min = mapped_column(Integer, default=0, nullable=False)
    stock_max = mapped_column(Integer, nullable=False)
    lotes = relationship("Lote", back_populates="producto", passive_deletes="all")

class Lote(Base):
    __tablename__ = "lotes"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_lote = mapped_column(String(50), unique=True, nullable=False, index=True)
    codigo_trazabilidad = mapped_column(String(100), unique=True, nullable=False, index=True)
    producto_id = mapped_column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    laboratorio_id = mapped_column(Integer, ForeignKey("laboratorios.id", ondelete="RESTRICT"), nullable=False)
    cantidad = mapped_column(Integer, nullable=False)
    fecha_ingreso = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_caducidad = mapped_column(Date, nullable=False)
    ubicacion_almacen = mapped_column(String(100), nullable=True)
    estado = mapped_column(Enum(EstadoLote), default=EstadoLote.DISPONIBLE, nullable=False)
    reservado_hasta = mapped_column(DateTime(timezone=True), nullable=True)

    producto = relationship("Producto", back_populates="lotes")
    laboratorio = relationship("Laboratorio", back_populates="lotes")

    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="check_cantidad_positiva"),
    )

# --- ENTIDADES DE SOPORTE LOGÍSTICO ---

class CapacidadAlmacen(Base):
    __tablename__ = "capacidad_almacen"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    zona = mapped_column(Enum(IndicacionAmbiental), unique=True, nullable=False)
    capacidad_maxima_unidades = mapped_column(Integer, nullable=False)

class EstadoTarea(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADA = "COMPLETADA"

class Tarea(Base):
    __tablename__ = "tareas"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    descripcion = mapped_column(String(255), nullable=False)
    asignado_a_id = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    fecha = mapped_column(Date, nullable=False, index=True)
    completada = mapped_column(Boolean, default=False, nullable=False)

    asignado_a = relationship("Usuario")

# --- ENTIDADES TRANSACCIONALES (VENTA Y MANUFACTURA) ---

class EstadoVenta(str, enum.Enum):
    INICIADA = "INICIADA"
    COMPLETADA = "COMPLETADA"

class Venta(Base):
    __tablename__ = "ventas"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_venta = mapped_column(String(50), unique=True, nullable=False, index=True)
    tecnico_id = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    id_cliente = mapped_column(String(50), nullable=False)
    hora_ingreso = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    estado = mapped_column(Enum(EstadoVenta), default=EstadoVenta.INICIADA, nullable=False)
    requiere_receta = mapped_column(Boolean, default=False, nullable=False)
    tipo_receta = mapped_column(String(20), nullable=True)

    tecnico = relationship("Usuario")
    items = relationship("ItemVenta", back_populates="venta", cascade="all, delete-orphan")

class ItemVenta(Base):
    __tablename__ = "items_venta"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id = mapped_column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    lote_id = mapped_column(Integer, ForeignKey("lotes.id", ondelete="RESTRICT"), nullable=False)
    cantidad = mapped_column(Integer, nullable=False)

    venta = relationship("Venta", back_populates="items")
    lote = relationship("Lote")

class EstadoReceta(str, enum.Enum):
    EN_ESPERA = "EN_ESPERA"
    EN_ELABORACION = "EN_ELABORACION"
    VALIDADA = "VALIDADA"
    DISPENSADA = "DISPENSADA"
    DESCARTADA = "DESCARTADA"

class RecetaMagistral(Base):
    __tablename__ = "recetas_magistrales"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id = mapped_column(Integer, ForeignKey("ventas.id", ondelete="RESTRICT"), nullable=False)
    auxiliar_id = mapped_column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    tipo = mapped_column(String(20), nullable=False)
    descripcion = mapped_column(String(255), nullable=False)
    estado = mapped_column(Enum(EstadoReceta), default=EstadoReceta.EN_ESPERA, nullable=False)
    ticket_validacion = mapped_column(String(255), nullable=True)
    fecha_ingreso = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    venta = relationship("Venta")
    auxiliar = relationship("Usuario")