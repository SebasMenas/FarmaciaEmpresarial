from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from datetime import date
import random
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO
from app.models.entidades import Usuario, RolUsuario, EstadoLote, Producto, Lote, Laboratorio
from app.schemas.esquemas import CapacidadAlmacenUpdate
from app.core.dependencias_rbac import requiere_admin
from app.core.security import Security
from app.testing.generador_datos import GeneradorDatos

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
    """
    El Admin solicita un producto nuevo indicando solo el nombre.
    La ficha técnica (componente activo, concentración, tipo de
    producto e indicación ambiental) la determina el sistema, igual
    que ocurre con un producto real: esos datos vienen del fabricante,
    no los inventa quien hace el pedido de abastecimiento.
    """
    nombre: str = Field(..., min_length=1, max_length=150)
    stock_min: int = Field(default=0, ge=0)
    stock_max: int = Field(..., gt=0)

class LoteCreate(BaseModel):
    """
    El Admin solicita reabastecimiento indicando QUÉ producto necesita,
    en QUÉ cantidad y para CUÁNDO vence. El laboratorio proveedor, el
    código de lote y el código de trazabilidad no los decide el Admin:
    en la vida real los asigna el laboratorio externo al despachar el
    pedido, así que aquí se generan automáticamente (mismo patrón que
    usa MockLaboratorio al simular un ingreso real).
    """
    producto_id: int
    cantidad: int = Field(..., gt=0)
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
    """
    Registra un producto nuevo en catálogo a partir del nombre solicitado.
    La ficha técnica (componente activo, concentración, tipo de producto
    e indicación ambiental) se resuelve automáticamente.
    """
    ficha = GeneradorDatos.resolver_ficha_tecnica(payload.nombre)

    nuevo_prod = Producto(
        nombre=payload.nombre,
        componente_activos=ficha["componente"],
        concentracion=ficha["concentracion"],
        tipo_producto=ficha["tipo"],
        indicacion_ambiental=ficha["ambiente"],
        stock_min=payload.stock_min,
        stock_max=payload.stock_max,
    )
    db.add(nuevo_prod)
    try:
        db.commit()
        db.refresh(nuevo_prod)
        return {
            "exito": True,
            "producto_id": nuevo_prod.id,
            "ficha_tecnica_generada": {
                "componente_activos": nuevo_prod.componente_activos,
                "concentracion": nuevo_prod.concentracion,
                "tipo_producto": nuevo_prod.tipo_producto,
                "indicacion_ambiental": nuevo_prod.indicacion_ambiental,
            }
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad en los datos del producto.")

@router.post("/lotes", status_code=status.HTTP_201_CREATED)
def registrar_lote_existente(payload: LoteCreate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    """
    Registra el reabastecimiento de un producto ya existente en catálogo.
    El laboratorio que despacha el pedido y los códigos de lote/trazabilidad
    se generan automáticamente (no son datos que el Admin deba inventar);
    esto evita además colisiones con las columnas unique de la tabla lotes.
    """
    producto = db.query(Producto).filter(Producto.id == payload.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en el catálogo.")

    nombre_lab = f"Laboratorio Bio_{random.randint(100, 999)}"
    laboratorio = Laboratorio(nombre=nombre_lab, certificado=True)
    db.add(laboratorio)
    db.flush()  # asigna laboratorio.id sin cerrar la transacción

    num_aleatorio = random.randint(1000, 9999)
    nuevo_lote = Lote(
        codigo_lote=f"L-{num_aleatorio}",
        codigo_trazabilidad=f"TZ-{num_aleatorio}",
        producto_id=producto.id,
        laboratorio_id=laboratorio.id,
        cantidad=payload.cantidad,
        fecha_caducidad=payload.fecha_caducidad,
        estado=EstadoLote.DISPONIBLE
    )
    db.add(nuevo_lote)
    try:
        db.commit()
        db.refresh(nuevo_lote)
        return {
            "exito": True,
            "lote_id": nuevo_lote.id,
            "codigo_lote": nuevo_lote.codigo_lote,
            "codigo_trazabilidad": nuevo_lote.codigo_trazabilidad,
            "laboratorio": laboratorio.nombre
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Colisión al generar el código de lote o trazabilidad; reintente la solicitud.")
    
@router.post("/capacidad", status_code=status.HTTP_200_OK)
def configurar_capacidad_almacen(
    payload: CapacidadAlmacenUpdate, 
    db: Session = Depends(get_db), 
    usuario_auth: dict = Depends(requiere_admin)
):
    """Define o calibra el límite volumétrico por zona ambiental."""
    registro = InventarioDAO.upsert_capacidad_zona(db, payload.zona, payload.capacidad_maxima_unidades)
    return {"exito": True, "zona": registro.zona, "nueva_capacidad": registro.capacidad_maxima_unidades}