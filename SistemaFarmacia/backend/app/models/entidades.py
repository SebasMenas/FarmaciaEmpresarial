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

class CausaBloqueo(str, enum.Enum):
    """
    Distingue por qué un lote está en estado BLOQUEADO, ya que ese estado
    se usa tanto para sospecha de defecto sanitario (bloqueo manual, no se
    libera automáticamente) como para falta de espacio físico en la zona
    de almacén asignada (bloqueo logístico, se libera solo cuando una
    venta u otra salida de stock abre espacio en esa zona).
    """
    SIN_ESPACIO_ZONA = "SIN_ESPACIO_ZONA"
    SOSPECHA_DEFECTO = "SOSPECHA_DEFECTO"

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
    nombre = mapped_column(String(150), nullable=False, index=True, unique=True)
    componente_activos = mapped_column(String(150), nullable=True)
    concentracion = mapped_column(String(50), nullable=True)
    tipo_producto = mapped_column(Enum(TipoProducto), nullable=False)
    indicacion_ambiental = mapped_column(Enum(IndicacionAmbiental), nullable=False)
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
    zona_id = mapped_column(Integer, ForeignKey("zonas_almacen.id", ondelete="SET NULL"), nullable=True)
    estado = mapped_column(Enum(EstadoLote), default=EstadoLote.DISPONIBLE, nullable=False)
    causa_bloqueo = mapped_column(Enum(CausaBloqueo), nullable=True)
    reservado_hasta = mapped_column(DateTime(timezone=True), nullable=True)

    producto = relationship("Producto", back_populates="lotes")
    laboratorio = relationship("Laboratorio", back_populates="lotes")
    zona = relationship("ZonaAlmacen", back_populates="lotes")

    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="check_cantidad_positiva"),
    )

# --- ENTIDADES DE SOPORTE LOGÍSTICO ---

class ZonaAlmacen(Base):
    """
    Catálogo cerrado de zonas físicas reales del almacén. Reemplaza el
    antiguo esquema de 'zona = IndicacionAmbiental' (solo 2 valores
    compartidos) por 4 ubicaciones concretas que el Auxiliar Mayor elige
    de una lista fija, evitando que escriba texto libre con errores de
    tipeo que generarían zonas duplicadas o inconsistentes.

    Se autogeneran al arrancar el sistema (A y B para REFRIGERADO,
    C y D para AMBIENTE, 1000 unidades de capacidad cada una por defecto),
    y el Admin puede recalibrar la capacidad de cada una manualmente.
    """
    __tablename__ = "zonas_almacen"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo = mapped_column(String(5), unique=True, nullable=False)  # "A", "B", "C", "D"
    tipo_ambiental = mapped_column(Enum(IndicacionAmbiental), nullable=False)
    capacidad_maxima_unidades = mapped_column(Integer, nullable=False, default=1000)

    lotes = relationship("Lote", back_populates="zona")

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
    # Estos tres campos llegan ya definidos desde el pedido del cliente
    # (simulado por MockCliente), nunca los redacta el Técnico.
    requiere_receta = mapped_column(Boolean, default=False, nullable=False)
    tipo_receta = mapped_column(String(20), nullable=True)
    descripcion_receta = mapped_column(String(255), nullable=True)

    tecnico = relationship("Usuario")
    items = relationship("ItemVenta", back_populates="venta", cascade="all, delete-orphan")
    pedido_solicitado = relationship("PedidoSolicitadoItem", back_populates="venta", cascade="all, delete-orphan")

class ItemVenta(Base):
    __tablename__ = "items_venta"
    
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id = mapped_column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    lote_id = mapped_column(Integer, ForeignKey("lotes.id", ondelete="RESTRICT"), nullable=False)
    cantidad = mapped_column(Integer, nullable=False)

    venta = relationship("Venta", back_populates="items")
    lote = relationship("Lote")

class PedidoSolicitadoItem(Base):
    """
    Registra lo que el cliente pidió originalmente (vía MockCliente), antes
    de que el Técnico lo confirme contra inventario real en ItemVenta.
    Es lo que la tabla de "pedido del cliente" muestra en la pantalla del
    Técnico; ItemVenta es lo que efectivamente se facturó, que puede
    diferir si algún producto se agotó entre el pedido y el cobro.
    """
    __tablename__ = "pedido_solicitado_items"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    venta_id = mapped_column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_id = mapped_column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad_solicitada = mapped_column(Integer, nullable=False)
    cubierto = mapped_column(Boolean, default=False, nullable=False)

    venta = relationship("Venta", back_populates="pedido_solicitado")
    producto = relationship("Producto")

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
    insumos_requeridos = relationship("InsumoRecetaRequerido", back_populates="receta", cascade="all, delete-orphan")

class InsumoRecetaRequerido(Base):
    """
    Lista real de productos que la receta necesita, elegidos siempre entre
    medicamentos que existen en el catálogo (nunca inventados). Reemplaza
    la antigua descripción de texto libre como única fuente de verdad:
    ahora reservar/validar/dispensar comparan contra esta lista, no solo
    contra el estado sanitario del lote que el Auxiliar elija.

    - Receta NORMAL: 1+ insumos que se dispensan tal cual, sin combinar.
    - Receta MAGISTRAL: 2+ insumos que se combinan en un producto nuevo
      simulado (no se crea ninguna fila real en Producto para el resultado).
    """
    __tablename__ = "insumos_receta_requeridos"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    receta_id = mapped_column(Integer, ForeignKey("recetas_magistrales.id", ondelete="CASCADE"), nullable=False)
    producto_id = mapped_column(Integer, ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False)
    cantidad_requerida = mapped_column(Integer, nullable=False, default=1)
    lote_reservado_id = mapped_column(Integer, ForeignKey("lotes.id", ondelete="SET NULL"), nullable=True)
    cubierto = mapped_column(Boolean, default=False, nullable=False)
    reservado_hasta = mapped_column(DateTime(timezone=True), nullable=True)

    receta = relationship("RecetaMagistral", back_populates="insumos_requeridos")
    producto = relationship("Producto")
    lote_reservado = relationship("Lote")