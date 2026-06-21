from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import List
import uuid

from app.db.database import get_db
from app.db.daos import UsuarioDAO, OperacionesDAO
from app.models.entidades import Lote, EstadoLote, IndicacionAmbiental, Venta, ItemVenta, RecetaMagistral, EstadoVenta, EstadoReceta
from app.schemas.esquemas import VentaDTO, RecetaMagistralDTO
from app.core.dependencias_rbac import requiere_auxiliar_mayor, requiere_auxiliar_diplomado, requiere_tecnico


def _reasignar_o_liberar_item(db: Session, item: "ItemVenta") -> str:
    """
    Lógica compartida de reasignación de lote, usada cuando un ítem de venta
    pierde stock disponible en su lote original (por ejemplo, porque una
    manufactura concurrente del Auxiliar Diplomado consumió el mismo lote).

    Intenta reasignar el ítem a otro lote DISPONIBLE del mismo producto con
    stock suficiente. Si no hay alternativa, retorna "SIN_STOCK" para que el
    llamador decida si elimina el ítem o cancela la venta completa.

    Retorna: "REASIGNADO" | "SIN_STOCK"
    """
    lote_original = item.lote
    alternativo = OperacionesDAO.buscar_lote_alternativo(
        db,
        producto_id=lote_original.producto_id,
        cantidad_requerida=item.cantidad,
        excluir_lote_id=lote_original.id
    )
    if alternativo:
        alternativo.cantidad -= item.cantidad
        if alternativo.cantidad == 0:
            alternativo.estado = EstadoLote.AGOTADO
        item.lote_id = alternativo.id
        return "REASIGNADO"
    return "SIN_STOCK"

router = APIRouter(prefix="/operaciones", tags=["Lógica de Operaciones (Fases 2 y 3)"])

# Función auxiliar interna para liberar bloqueos de manufactura expirados
def liberar_timeouts_reserva(db: Session):
    ahora = datetime.now(timezone.utc)
    lotes_expirados = db.query(Lote).filter(
        Lote.estado == EstadoLote.RESERVADO_MANUFACTURA,
        Lote.reservado_hasta < ahora
    ).all()
    for lote in lotes_expirados:
        lote.estado = EstadoLote.DISPONIBLE
        lote.reservado_hasta = None
    if lotes_expirados:
        db.commit()

class UbicacionPayload(BaseModel):
    ubicacion: str
    temperatura_zona: IndicacionAmbiental

class ManufacturaPayload(BaseModel):
    lote_id: int
    credencial_operacion: str

class AtenderClientePayload(BaseModel):
    id_cliente: str

class ItemCarritoPayload(BaseModel):
    lote_id: int
    cantidad: int = Field(..., gt=0)

class FacturarPayload(BaseModel):
    requiere_receta: bool
    tipo_receta: str | None = None
    descripcion_receta: str | None = None

@router.put("/almacenar/{lote_id}")
def almacenar_lote(lote_id: int, payload: UbicacionPayload, db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_mayor)):
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    if lote.producto.indicacion_ambiental != payload.temperatura_zona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={"codigo_error": "ERROR_AMBIENTAL", "mensaje": "La ubicación no cumple con la ficha técnica."}
        )
    lote.ubicacion_almacen = payload.ubicacion
    db.commit()
    return {"exito": True, "detalle": "Lote almacenado correctamente"}

@router.post("/manufactura/iniciar")
def iniciar_manufactura(payload: ManufacturaPayload, db: Session = Depends(get_db), usuario_auth = Depends(requiere_auxiliar_diplomado)):
    liberar_timeouts_reserva(db)
    operador = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    if not operador or operador.credencial != payload.credencial_operacion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail={"codigo_error": "FIRMA_INVALIDA", "mensaje": "Credencial de operación inválida."}
        )
    try:
        lote = db.query(Lote).filter(Lote.id == payload.lote_id, Lote.estado == EstadoLote.DISPONIBLE).with_for_update(nowait=True).first()

        if not lote:
            # El lote original ya no existe en estado disponible (perdió la carrera de concurrencia).
            # Se requiere conocer el producto para buscar alternativa; sin el lote original no es posible.
            raise HTTPException(status_code=409, detail={"codigo_error": "LOTE_RESERVADO", "mensaje": "Lote agotado o retenido."})

        lote.estado = EstadoLote.RESERVADO_MANUFACTURA
        lote.reservado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()
        return {"exito": True, "codigo_lote": lote.codigo_lote, "estado": lote.estado}
    except OperationalError:
        db.rollback()
        # El lote estaba siendo usado por otra transacción (ej. el carrito del Técnico).
        # Se busca un lote alternativo del mismo producto antes de fallar definitivamente.
        lote_referencia = db.query(Lote).filter(Lote.id == payload.lote_id).first()
        if not lote_referencia:
            raise HTTPException(status_code=409, detail={"codigo_error": "LOTE_BLOQUEADO", "mensaje": "Receso transaccional bloqueado."})

        try:
            alternativo = OperacionesDAO.buscar_lote_alternativo(
                db,
                producto_id=lote_referencia.producto_id,
                cantidad_requerida=1,
                excluir_lote_id=lote_referencia.id
            )
            if not alternativo:
                raise HTTPException(
                    status_code=409,
                    detail={"codigo_error": "SIN_STOCK_ALTERNATIVO", "mensaje": "Lote bloqueado y sin alternativa disponible del mismo producto."}
                )
            alternativo.estado = EstadoLote.RESERVADO_MANUFACTURA
            alternativo.reservado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.commit()
            return {
                "exito": True,
                "codigo_lote": alternativo.codigo_lote,
                "estado": alternativo.estado,
                "lote_reasignado": True
            }
        except OperationalError:
            db.rollback()
            raise HTTPException(status_code=409, detail={"codigo_error": "LOTE_BLOQUEADO", "mensaje": "Receso transaccional bloqueado."})

# --- FLUJO DE PANTALLA: TÉCNICO (VENTAS) ---

@router.post("/ventas/atender", response_model=VentaDTO, status_code=status.HTTP_201_CREATED)
def atender_cliente(payload: AtenderClientePayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    tecnico = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado en los registros.")
    
    nueva_venta = OperacionesDAO.crear_venta_iniciada(db, tecnico.id, payload.id_cliente)
    return nueva_venta

@router.post("/ventas/{id}/items", status_code=status.HTTP_201_CREATED)
def agregar_item_carrito(id: int, payload: ItemCarritoPayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Orden de venta no activa.")

    try:
        # Bloqueo a nivel de fila sobre el lote solicitado explícitamente
        lote = db.query(Lote).filter(Lote.id == payload.lote_id, Lote.estado == EstadoLote.DISPONIBLE).with_for_update(nowait=True).first()

        if lote and lote.cantidad >= payload.cantidad:
            lote_a_usar = lote
        else:
            producto_id_referencia = lote.producto_id if lote else None
            if producto_id_referencia is None:
                raise HTTPException(status_code=404, detail="Lote no encontrado para determinar producto alternativo.")

            lote_a_usar = OperacionesDAO.buscar_lote_alternativo(
                db,
                producto_id=producto_id_referencia,
                cantidad_requerida=payload.cantidad,
                excluir_lote_id=payload.lote_id
            )
            if not lote_a_usar:
                raise HTTPException(
                    status_code=409,
                    detail={"codigo_error": "SIN_STOCK_ALTERNATIVO", "mensaje": "Sin stock suficiente en este ni otros lotes del producto."}
                )

        assert lote_a_usar is not None

        lote_a_usar.cantidad -= payload.cantidad
        if lote_a_usar.cantidad == 0:
            lote_a_usar.estado = EstadoLote.AGOTADO

        nuevo_item = ItemVenta(venta_id=venta.id, lote_id=lote_a_usar.id, cantidad=payload.cantidad)
        db.add(nuevo_item)
        db.commit()
        
        reasignado = lote_a_usar.id != payload.lote_id
        return {
            "exito": True,
            "mensaje": "Producto indexado al carro de compras y stock deducido",
            "lote_reasignado": reasignado,
            "lote_utilizado": lote_a_usar.codigo_lote
        }
    
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El lote seleccionado está siendo operado en otra transacción.")

@router.post("/ventas/{id}/factura")
def finalizar_facturacion(id: int, payload: FacturarPayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada o ya procesada.")
    
    # El stock físico ya fue deducido en la inserción del carrito.
    # Se procesa únicamente el cambio de estado y la generación de recetas.
    venta.estado = EstadoVenta.COMPLETADA
    venta.requiere_receta = payload.requiere_receta
    venta.tipo_receta = payload.tipo_receta

    if payload.requiere_receta:
        if not payload.tipo_receta or not payload.descripcion_receta:
            raise HTTPException(status_code=400, detail="Faltan metadatos de la receta médica.")
        
        nueva_receta = RecetaMagistral(
            venta_id=venta.id,
            tipo=payload.tipo_receta,
            descripcion=payload.descripcion_receta,
            estado=EstadoReceta.EN_ESPERA
        )
        db.add(nueva_receta)
    
    db.commit()
    return {"exito": True, "estado_venta": venta.estado, "derivado_a_recetas": venta.requiere_receta}

@router.post("/ventas/{id}/items/{item_id}/resolver-falta-stock")
def resolver_falta_stock_item(id: int, item_id: int, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Maneja la pérdida de stock sobre un ítem ya agregado al carrito, típicamente
    disparado cuando el Auxiliar Diplomado reservó el mismo lote para manufactura
    entre que el Técnico lo seleccionó y completó la compra.

    Regla de resolución (igual para Técnico y Auxiliar Diplomado):
    1. Intenta reasignar el ítem a otro lote disponible del mismo producto.
    2. Si no hay alternativa y es el único ítem de la venta -> cancela la venta
       completa (y descarta la receta derivada, si existía).
    3. Si no hay alternativa pero existen otros ítems -> elimina solo este ítem,
       la venta continúa con el resto.
    """
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada o ya procesada.")

    item = db.query(ItemVenta).filter(ItemVenta.id == item_id, ItemVenta.venta_id == venta.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado en esta venta.")

    try:
        resultado = _reasignar_o_liberar_item(db, item)

        if resultado == "REASIGNADO":
            db.commit()
            return {"exito": True, "accion": "REASIGNADO", "mensaje": "Ítem reasignado a un lote alternativo del mismo producto."}

        # SIN_STOCK: decidir entre cancelar venta completa o eliminar solo el ítem
        total_items = len(venta.items)

        if total_items == 1:
            receta_asociada = db.query(RecetaMagistral).filter(RecetaMagistral.venta_id == venta.id).first()
            if receta_asociada:
                receta_asociada.estado = EstadoReceta.DESCARTADA
            venta.estado = EstadoVenta.COMPLETADA
            db.delete(item)
            db.commit()
            return {
                "exito": True,
                "accion": "VENTA_CANCELADA",
                "mensaje": "Sin stock alternativo y era el único producto. Venta cancelada y receta derivada descartada (si existía)."
            }
        else:
            db.delete(item)
            db.commit()
            return {
                "exito": True,
                "accion": "ITEM_ELIMINADO",
                "mensaje": "Sin stock alternativo. El producto fue retirado de la venta; el resto de la compra continúa."
            }
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El lote alternativo está siendo operado en otra transacción.")

@router.post("/ventas/{id}/cancelar")
def cancelar_venta(id: int, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Revierte la transacción y restituye el stock físico al inventario disponible.

    Si la venta ya derivó una RecetaMagistral, no se elimina físicamente. En ese caso
    se descarta la receta y se vacía/cierra la venta sin borrar el registro,
    preservando la trazabilidad del intento fallido.
    """
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada o ya procesada.")

    receta_asociada = db.query(RecetaMagistral).filter(RecetaMagistral.venta_id == venta.id).first()

    for item in venta.items:
        lote = db.query(Lote).filter(Lote.id == item.lote_id).with_for_update().first()
        if lote:
            lote.cantidad += item.cantidad
            if lote.estado == EstadoLote.AGOTADO and lote.cantidad > 0:
                lote.estado = EstadoLote.DISPONIBLE

    for item in list(venta.items):
        db.delete(item)

    if receta_asociada:
        # No se puede eliminar la venta mientras la receta la referencie (FK RESTRICT).
        # Se descarta la receta y se cierra la venta como cancelada, sin borrar el registro.
        receta_asociada.estado = EstadoReceta.DESCARTADA
        venta.estado = EstadoVenta.COMPLETADA
        venta.requiere_receta = False
        db.commit()
        return {"exito": True, "mensaje": "Stock restituido y receta derivada descartada. Venta cerrada como cancelada (no eliminable por trazabilidad)."}

    db.delete(venta)
    db.commit()
    return {"exito": True, "mensaje": "Transacción abortada y stock restituido."}
# --- FLUJO DE PANTALLA: AUXILIAR DIPLOMADO (RECETAS) ---

@router.get("/recetas/cola", response_model=List[RecetaMagistralDTO])
def obtener_cola_fifo_recetas(db: Session = Depends(get_db), usuario_auth = Depends(requiere_auxiliar_diplomado)):
    return OperacionesDAO.obtener_cola_recetas(db)

@router.post("/recetas/{id}/generar-ticket")
def generar_ticket_validacion(id: int, db: Session = Depends(get_db), usuario_auth = Depends(requiere_auxiliar_diplomado)):
    receta = db.query(RecetaMagistral).filter(RecetaMagistral.id == id, RecetaMagistral.estado == EstadoReceta.EN_ESPERA).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no apta para validación o ya procesada.")

    try:
        for item in receta.venta.items:
            if item.lote.estado in [EstadoLote.RETIRADO, EstadoLote.BLOQUEADO, EstadoLote.CUARENTENA]:
                # Antes de descartar la receta, se intenta reasignar el ítem afectado
                # a otro lote disponible del mismo producto (misma regla que en Venta).
                resultado = _reasignar_o_liberar_item(db, item)

                if resultado == "REASIGNADO":
                    continue

                # SIN_STOCK: aplica la misma regla de único producto vs. múltiples productos
                total_items = len(receta.venta.items)
                if total_items == 1:
                    receta.estado = EstadoReceta.DESCARTADA
                    db.commit()
                    raise HTTPException(
                        status_code=400,
                        detail={"codigo_error": "INSUMO_RECHAZADO", "mensaje": "Insumo sin estado sanitario válido y sin alternativa de stock. Receta descartada."}
                    )
                else:
                    db.delete(item)
                    db.commit()
                    raise HTTPException(
                        status_code=400,
                        detail={"codigo_error": "INSUMO_ELIMINADO", "mensaje": "Insumo sin estado sanitario válido y sin alternativa. Se eliminó solo ese componente; revise la receta antes de continuar."}
                    )

        receta.estado = EstadoReceta.EN_ELABORACION
        receta.ticket_validacion = f"TCK-{uuid.uuid4().hex[:10].upper()}"
        db.commit()
        return {"exito": True, "ticket": receta.ticket_validacion, "nuevo_estado": receta.estado}
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Insumo de la receta siendo operado en otra transacción.")

@router.post("/recetas/{id}/dispensar")
def dispensar_ciclo_receta(id: int, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_diplomado)):
    receta = db.query(RecetaMagistral).filter(RecetaMagistral.id == id, RecetaMagistral.estado == EstadoReceta.EN_ELABORACION).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no se encuentra en fase de elaboración.")
    
    auxiliar = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    if not auxiliar:
        raise HTTPException(status_code=404, detail="Auxiliar no encontrado.")
        
    receta.auxiliar_id = auxiliar.id
    receta.estado = EstadoReceta.DISPENSADA
    db.commit()
    return {"exito": True, "estado": receta.estado}