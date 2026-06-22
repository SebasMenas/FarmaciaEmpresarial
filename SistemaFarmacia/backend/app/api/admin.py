from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from datetime import date
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO
from app.models.entidades import Usuario, RolUsuario, EstadoLote, TipoProducto, IndicacionAmbiental, Producto, Lote
from app.schemas.esquemas import CapacidadAlmacenUpdate
from app.core.dependencias_rbac import requiere_admin
from app.core.security import Security

router = APIRouter(prefix="/admin", tags=["Administración"])

class EmpleadoCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=50)
    password: str = Field(..., min_length=6)
    nombre: str = Field(..., description="Nombre real del empleado")
    apellidos: str = Field(..., description="Apellidos del empleado")
    rut: str = Field(..., description="Rol Único Tributario")
    rol: RolUsuario 
    credencial: str | None = Field(default=None, description="PIN de operación para Auxiliar Diplomado")
    activo: bool = True

class EmpleadoUpdate(BaseModel):
    nombre: str | None = None
    apellidos: str | None = None
    rol: RolUsuario | None = None
    credencial: str | None = None
    activo: bool | None = None

class EstadoLoteUpdate(BaseModel):
    estado: EstadoLote

class ProductoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    componente_activos: str | None = Field(default=None, max_length=150)
    concentracion: str | None = Field(default=None, max_length=50)
    tipo_producto: TipoProducto
    indicacion_ambiental: IndicacionAmbiental
    stock_min: int = Field(default=0, ge=0)
    stock_max: int = Field(..., gt=0)

class LoteCreate(BaseModel):
    codigo_lote: str = Field(..., max_length=50)
    codigo_trazabilidad: str = Field(..., max_length=100)
    producto_id: int
    laboratorio_id: int
    cantidad: int = Field(..., ge=0)
    fecha_caducidad: date

@router.post("/empleados", status_code=status.HTTP_201_CREATED)
def registrar_empleado(payload: EmpleadoCreate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    usuario_existente = UsuarioDAO.obtener_por_username(db, payload.username)
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya se encuentra registrado.")
    
    hashed_pwd = Security.obtener_password_hash(payload.password)
    try:
        nuevo_empleado = UsuarioDAO.crear_empleado(
            db=db, username=payload.username, password_hash=hashed_pwd, nombre=payload.nombre,
            apellidos=payload.apellidos, rut=payload.rut, rol=payload.rol, credencial=payload.credencial, activo=payload.activo
        )
        return {"exito": True, "id_empleado": nuevo_empleado.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de integridad: Duplicidad de RUT.")

@router.put("/empleados/{id}", status_code=status.HTTP_200_OK)
def editar_empleado(id: int, payload: EmpleadoUpdate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    
    """Permite modificar los atributos de un empleado desde la interfaz de administración."""
    usuario_actualizado = UsuarioDAO.actualizar_empleado(db, id, payload.model_dump(exclude_none=True))
    if not usuario_actualizado:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    return {"exito": True, "mensaje": "Empleado actualizado correctamente"}

@router.put("/lotes/{id}/estado", status_code=status.HTTP_200_OK)
def cambiar_estado_existencia(id: int, payload: EstadoLoteUpdate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    """Modifica manualmente el estado de un lote (ej: Forzar No Disponible / Bloqueado)."""
    lote = InventarioDAO.cambiar_estado_lote(db, id, payload.estado)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    return {"exito": True, "nuevo_estado": lote.estado}

@router.post("/productos", status_code=status.HTTP_201_CREATED)
def registrar_producto(payload: ProductoCreate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    nuevo_prod = Producto(**payload.model_dump())
    db.add(nuevo_prod)
    try:
        db.commit()
        db.refresh(nuevo_prod)
        return {"exito": True, "producto_id": nuevo_prod.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en los datos del producto.")

@router.post("/lotes", status_code=status.HTTP_201_CREATED)
def registrar_lote_existente(payload: LoteCreate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    nuevo_lote = Lote(**payload.model_dump())
    db.add(nuevo_lote)
    try:
        db.commit()
        db.refresh(nuevo_lote)
        return {"exito": True, "lote_id": nuevo_lote.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Código de lote o trazabilidad duplicado.")
    
@router.post("/capacidad", status_code=status.HTTP_200_OK)
def configurar_capacidad_almacen(
    payload: CapacidadAlmacenUpdate, 
    db: Session = Depends(get_db), 
    usuario_auth: dict = Depends(requiere_admin)
):
    """Define o calibra el límite volumétrico por zona ambiental."""
    registro = InventarioDAO.upsert_capacidad_zona(db, payload.zona, payload.capacidad_maxima_unidades)
    return {"exito": True, "zona": registro.zona, "nueva_capacidad": registro.capacidad_maxima_unidades}