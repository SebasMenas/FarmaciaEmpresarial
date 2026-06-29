from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field
from datetime import date
from typing import List
import random
from app.db.database import get_db
from app.db.daos import UsuarioDAO, InventarioDAO, CatalogoDAO
from app.models.entidades import Usuario, RolUsuario, EstadoLote, Producto, Lote
from app.schemas.esquemas import ZonaAlmacenUpdate, ProductoCatalogoDTO, LaboratorioDTO
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
    El Admin solicita un producto nuevo indicando el nombre y la cantidad
    fija con la que ingresa al sistema. La ficha técnica (componente activo,
    concentración, tipo de producto e indicación ambiental) la determina el
    sistema; el primer lote del producto se crea automáticamente con esta
    cantidad inicial.
    """
    nombre: str = Field(..., min_length=1, max_length=150)
    cantidad_inicial: int = Field(..., gt=0, description="Cantidad fija con la que ingresa el primer lote del producto")
    fecha_caducidad: date

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
    operador_actual = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])

    if operador_actual and operador_actual.id == id:
        # Un admin no puede desactivarse ni cambiarse el rol a sí mismo desde
        # esta pantalla: si fuera el único admin del sistema, quedaría
        # bloqueado fuera de su propia vista sin forma de revertirlo.
        if payload.activo is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede desactivar su propia cuenta. Solicite a otro administrador que lo haga."
            )
        if payload.rol is not None and payload.rol != RolUsuario.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puede cambiar su propio rol de administrador."
            )

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
    Registra un producto nuevo en catálogo a partir del nombre solicitado,
    junto a su primer lote de ingreso con la cantidad fija indicada.
    La ficha técnica se resuelve automáticamente; el laboratorio proveedor
    reutiliza uno certificado existente en vez de crear uno nuevo cada vez.
    """
    existente = CatalogoDAO.obtener_producto_por_nombre(db, payload.nombre)
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un producto con ese nombre en el catálogo; use 'Reabastecer' en su lugar."
        )

    ficha = GeneradorDatos.resolver_ficha_tecnica(payload.nombre)

    nuevo_prod = Producto(
        nombre=payload.nombre,
        componente_activos=ficha["componente"],
        concentracion=ficha["concentracion"],
        tipo_producto=ficha["tipo"],
        indicacion_ambiental=ficha["ambiente"],
    )
    db.add(nuevo_prod)
    db.flush()  # asigna nuevo_prod.id sin cerrar la transacción

    laboratorio = CatalogoDAO.obtener_o_crear_laboratorio_certificado(db)

    num_aleatorio = random.randint(1000, 9999)
    primer_lote = Lote(
        codigo_lote=f"L-{num_aleatorio}",
        codigo_trazabilidad=f"TZ-{num_aleatorio}",
        producto_id=nuevo_prod.id,
        laboratorio_id=laboratorio.id,
        cantidad=payload.cantidad_inicial,
        fecha_caducidad=payload.fecha_caducidad,
        estado=EstadoLote.DISPONIBLE
    )
    db.add(primer_lote)

    try:
        db.commit()
        db.refresh(nuevo_prod)
        db.refresh(primer_lote)
        return {
            "exito": True,
            "producto_id": nuevo_prod.id,
            "lote_id": primer_lote.id,
            "codigo_lote": primer_lote.codigo_lote,
            "laboratorio": laboratorio.nombre,
            "ficha_tecnica_generada": {
                "componente_activos": nuevo_prod.componente_activos,
                "concentracion": nuevo_prod.concentracion,
                "tipo_producto": nuevo_prod.tipo_producto,
                "indicacion_ambiental": nuevo_prod.indicacion_ambiental,
            }
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad al registrar el producto y su lote inicial.")

@router.post("/lotes", status_code=status.HTTP_201_CREATED)
def registrar_lote_existente(payload: LoteCreate, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    """
    Registra el reabastecimiento de un producto ya existente en catálogo.
    Reutiliza un laboratorio certificado existente (en vez de crear uno
    nuevo en cada pedido); solo los códigos de lote/trazabilidad se generan,
    ya que identifican un ingreso físico específico y deben ser únicos.
    """
    producto = db.query(Producto).filter(Producto.id == payload.producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en el catálogo.")

    laboratorio = CatalogoDAO.obtener_o_crear_laboratorio_certificado(db)

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

@router.get("/productos", response_model=List[ProductoCatalogoDTO])
def listar_catalogo_productos(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    """
    Catálogo real de productos, independiente de si ya tienen lotes
    ingresados o no. Necesario para que 'Reabastecer' pueda ofrecer
    cualquier producto registrado, incluso uno sin stock actual.
    """
    return CatalogoDAO.listar_productos(db)

@router.get("/laboratorios", response_model=List[LaboratorioDTO])
def listar_catalogo_laboratorios(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_admin)):
    return CatalogoDAO.listar_laboratorios(db)
    
@router.put("/zonas/{zona_id}/capacidad", status_code=status.HTTP_200_OK)
def recalibrar_capacidad_zona(
    zona_id: int,
    payload: ZonaAlmacenUpdate,
    db: Session = Depends(get_db),
    usuario_auth: dict = Depends(requiere_admin)
):
    """
    Recalibra el techo de capacidad física de una de las 4 zonas fijas
    (A, B, C, D). Las zonas mismas no se crean ni eliminan desde aquí:
    se autogeneran al arrancar el sistema para evitar que el Auxiliar
    Mayor cree zonas arbitrarias con error de tipeo.
    """
    zona = InventarioDAO.actualizar_capacidad_zona(db, zona_id, payload.capacidad_maxima_unidades)
    if not zona:
        raise HTTPException(status_code=404, detail="Zona de almacén no encontrada.")
    return {"exito": True, "codigo_zona": zona.codigo, "nueva_capacidad": zona.capacidad_maxima_unidades}