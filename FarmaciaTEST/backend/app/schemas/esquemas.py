from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional
from app.models.entidades import RolUsuario, TipoProducto, IndicacionAmbiental, EstadoLote

# Esquemas de Autenticacion
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    rol: RolUsuario

# Esquemas de lectura para Monitoreo (Frontend)
class UsuarioDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str
    nombre: str
    apellidos: str
    rut: str
    rol: RolUsuario
    credencial: Optional[str] = None

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

class LoteMonitoreoDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    codigo_lote: str
    codigo_trazabilidad: str
    cantidad: int
    fecha_ingreso: datetime
    fecha_caducidad: date
    ubicacion_almacen: Optional[str] = None
    estado: EstadoLote
    producto: ProductoDTO
    laboratorio: LaboratorioDTO