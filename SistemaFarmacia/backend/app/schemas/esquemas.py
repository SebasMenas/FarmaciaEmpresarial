from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import datetime, date
from typing import Optional, List, Any
from app.models.entidades import (
    RolUsuario, TipoProducto, IndicacionAmbiental, EstadoLote,
    EstadoTarea, EstadoVenta, EstadoReceta, CausaBloqueo
)

# --- ESQUEMAS DE AUTENTICACIÓN ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    rol: RolUsuario

# --- ESQUEMAS BASE (DOMINIO) ---
class UsuarioDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    nombre: str
    apellidos: str
    rut: str
    rol: RolUsuario
    credencial: Optional[str] = None
    activo: bool

class LaboratorioDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    certificado: bool

class ProductoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    tipo_producto: TipoProducto
    indicacion_ambiental: IndicacionAmbiental

class ProductoCatalogoDTO(BaseModel):
    """
    Esquema para el catálogo real de productos (GET /admin/productos),
    independiente de si el producto ya tiene lotes ingresados o no.
    Permite ver y reabastecer un producto incluso si su stock actual es 0.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    componente_activos: Optional[str] = None
    concentracion: Optional[str] = None
    tipo_producto: TipoProducto
    indicacion_ambiental: IndicacionAmbiental
    stock_total: int = Field(default=0, description="Suma de Lote.cantidad en estados operativos, inyectada por el DAO")

class ZonaAlmacenDTO(BaseModel):
    """
    Esquema para las 4 zonas físicas fijas del almacén (A, B refrigerado;
    C, D ambiente). Se usa tanto para listarlas en el selector del
    Auxiliar Mayor como anidada dentro de LoteMonitoreoDTO.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    tipo_ambiental: IndicacionAmbiental
    capacidad_maxima_unidades: int

# --- ESQUEMAS DE OPERACIÓN (NUEVOS) ---

class TareaDTO(BaseModel):
    """Esquema para la vista de agenda del Auxiliar Mayor."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    descripcion: str
    fecha: date
    completada: bool
    asignado_a: UsuarioDTO

# --- ESQUEMAS DE ENTRADA (MUTACIONES) ---

class TareaCreate(BaseModel):
    descripcion: str = Field(..., max_length=255, description="Instrucción de la tarea")
    asignado_a_id: int = Field(..., description="ID del empleado responsable")
    fecha: date = Field(..., description="Fecha de ejecución programada")

class TareaEstadoUpdate(BaseModel):
    completada: bool = Field(..., description="Estado del checklist manual")

class ZonaAlmacenUpdate(BaseModel):
    """El Admin solo recalibra la capacidad; las 4 zonas ya existen de antemano."""
    capacidad_maxima_unidades: int = Field(..., gt=0, description="Límite físico de la zona")

class ItemVentaDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lote_id: int
    cantidad: int

class VentaDTO(BaseModel):
    """Esquema para el carrito y facturación del Técnico."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo_venta: str
    id_cliente: str
    hora_ingreso: datetime
    estado: EstadoVenta
    requiere_receta: bool
    tipo_receta: Optional[str] = None
    descripcion_receta: Optional[str] = None
    items: List[ItemVentaDTO] = []

class VentaResumenDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    codigo_venta: str
    id_cliente: str

class InsumoRecetaRequeridoDTO(BaseModel):
    """Insumo real requerido por una receta, con su estado de reserva."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    producto_id: int
    cantidad_requerida: int
    cubierto: bool
    producto: ProductoDTO

class RecetaMagistralDTO(BaseModel):
    """Esquema para la cola FIFO del Auxiliar Diplomado."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    descripcion: str
    estado: EstadoReceta
    ticket_validacion: Optional[str] = None
    fecha_ingreso: datetime
    venta: VentaResumenDTO
    insumos_requeridos: List[InsumoRecetaRequeridoDTO] = []
    
    # Derivación de datos relacionales requeridos por el frontend
    @computed_field
    def numero_orden(self) -> str:
        return self.venta.codigo_venta

    @computed_field
    def id_cliente(self) -> str:
        return self.venta.id_cliente
    
class ZonaCapacidadDTO(BaseModel):
    """Esquema para el gráfico de capacidad por zona (4 barras: A, B, C, D)."""
    id: int
    codigo: str
    tipo_ambiental: IndicacionAmbiental
    capacidad_maxima_unidades: int
    ocupacion_actual: int = Field(default=0, description="Inyectado dinámicamente por el DAO")
    espacio_disponible: int = Field(default=0, description="Inyectado dinámicamente por el DAO")

# --- ESQUEMAS DE MONITOREO (MODIFICADOS) ---

class LoteMonitoreoDTO(BaseModel):
    """Esquema para la tabla de existencias y alertas de caducidad."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo_lote: str
    codigo_trazabilidad: str
    cantidad: int
    fecha_ingreso: datetime
    fecha_caducidad: date
    zona: Optional[ZonaAlmacenDTO] = None
    estado: EstadoLote
    causa_bloqueo: Optional[CausaBloqueo] = None
    producto: ProductoDTO
    laboratorio: LaboratorioDTO

    @computed_field
    def temperatura(self) -> str:
        """Satisface el requisito explícito de mostrar la temperatura física formateada."""
        if self.producto.indicacion_ambiental == IndicacionAmbiental.AMBIENTE:
            return "21°C (Ambiente)"
        return "4°C (Refrigerado)"

class LoteVentaDTO(BaseModel):
    """
    Esquema reducido para la vista de venta (carrito del Técnico y selección
    de insumos del Auxiliar Diplomado). Expone solo lo necesario para elegir
    un producto y cantidad; oculta ubicación física, código de trazabilidad
    y otros datos de gestión interna del almacén que no corresponden a estos roles.
    """
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo_lote: str
    cantidad: int
    fecha_caducidad: date
    estado: EstadoLote
    producto: ProductoDTO