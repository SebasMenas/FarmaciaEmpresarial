from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import List
import uuid

from app.db.database import get_db
from app.db.daos import UsuarioDAO, OperacionesDAO, InventarioDAO
from app.models.entidades import Lote, EstadoLote, ZonaAlmacen, Venta, ItemVenta, RecetaMagistral, EstadoVenta, EstadoReceta, PedidoSolicitadoItem, InsumoRecetaRequerido, CausaBloqueo
from app.schemas.esquemas import VentaDTO, RecetaMagistralDTO
from app.core.dependencias_rbac import requiere_auxiliar_mayor, requiere_auxiliar_diplomado, requiere_tecnico
from app.testing.mock_cliente import MockCliente


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
    """
    Libera dos tipos de reserva expirada:
    1. Lotes bloqueados completos en RESERVADO_MANUFACTURA (flujo viejo,
       usado por /manufactura/iniciar con lote_id explícito).
    2. Insumos de receta cuya cantidad fue descontada del lote pero
       nunca llegó a validarse — se restituye la cantidad al lote y el
       insumo vuelve a quedar pendiente, para que otro intento de
       reserva (de esta u otra receta) pueda usarlo.
    """
    ahora = datetime.now(timezone.utc)

    lotes_expirados = db.query(Lote).filter(
        Lote.estado == EstadoLote.RESERVADO_MANUFACTURA,
        Lote.reservado_hasta < ahora
    ).all()
    for lote in lotes_expirados:
        lote.estado = EstadoLote.DISPONIBLE
        lote.reservado_hasta = None

    insumos_expirados = db.query(InsumoRecetaRequerido).filter(
        InsumoRecetaRequerido.cubierto.is_(True),
        InsumoRecetaRequerido.reservado_hasta < ahora,
        InsumoRecetaRequerido.lote_reservado_id.isnot(None)
    ).all()
    for insumo in insumos_expirados:
        lote = db.query(Lote).filter(Lote.id == insumo.lote_reservado_id).with_for_update().first()
        if lote:
            lote.cantidad += insumo.cantidad_requerida
            if lote.estado == EstadoLote.AGOTADO and lote.cantidad > 0:
                lote.estado = EstadoLote.DISPONIBLE
        insumo.cubierto = False
        insumo.lote_reservado_id = None
        insumo.reservado_hasta = None

    if lotes_expirados or insumos_expirados:
        db.commit()

class UbicacionPayload(BaseModel):
    zona_id: int
    confirmar: bool = False

class ManufacturaPayload(BaseModel):
    lote_id: int
    credencial_operacion: str

class ManufacturaPorProductoPayload(BaseModel):
    """
    Payload para reservar un insumo de manufactura sin que el Auxiliar
    Diplomado elija el lote específico: el backend resuelve
    automáticamente el primer lote DISPONIBLE con stock suficiente para
    ese producto, igual que en el carrito del Técnico.

    receta_id identifica de qué receta es este insumo, para validar que
    el producto realmente esté en su lista de insumos requeridos —no
    cualquier producto con stock sirve, solo el que la receta pide.
    """
    receta_id: int
    producto_id: int
    cantidad: int = Field(..., gt=0)
    credencial_operacion: str

class CredencialPayload(BaseModel):
    """Payload para verificar el código de empleado sin reservar nada."""
    credencial_operacion: str

class ItemCarritoPayload(BaseModel):
    lote_id: int
    cantidad: int = Field(..., gt=0)

class ItemPorProductoPayload(BaseModel):
    """
    Payload para confirmar un producto del pedido del cliente sin que el
    Técnico elija el lote: el backend resuelve automáticamente el primer
    lote DISPONIBLE con stock suficiente para ese producto.
    """
    producto_id: int
    cantidad: int = Field(..., gt=0)

@router.put("/almacenar/{lote_id}")
def almacenar_lote(lote_id: int, payload: UbicacionPayload, db: Session = Depends(get_db), usuario = Depends(requiere_auxiliar_mayor)):
    """
    Asigna un lote a una de las 4 zonas físicas fijas. Valida primero que
    el tipo ambiental de la zona coincida con la ficha técnica del producto,
    y luego que haya espacio real disponible.

    Si no hay espacio, el lote queda BLOQUEADO (causa_bloqueo=SIN_ESPACIO_ZONA)
    en vez de simplemente rechazar la petición: queda en cola para liberarse
    automáticamente en cuanto una venta u otra salida de stock abra espacio
    en esa misma zona.
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    zona = db.query(ZonaAlmacen).filter(ZonaAlmacen.id == payload.zona_id).first()
    if not zona:
        raise HTTPException(status_code=404, detail="Zona de almacén no encontrada")

    if lote.producto.indicacion_ambiental != zona.tipo_ambiental:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"codigo_error": "ERROR_AMBIENTAL", "mensaje": "La zona no cumple con la ficha técnica del producto."}
        )

    if lote.zona_id == zona.id and not payload.confirmar:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "codigo_error": "LOTE_YA_EN_ZONA",
                "mensaje": f"El lote {lote.codigo_lote} ya está ubicado en la zona {zona.codigo}.",
                "zona": zona.codigo
            }
        )

    resultado = InventarioDAO.asignar_zona_lote(db, lote, zona)

    if resultado["asignado"]:
        return {
            "exito": True,
            "detalle": "Lote ya estaba en esta zona; no se modificó la capacidad." if resultado["ya_en_zona"] else "Lote almacenado correctamente",
            "zona": zona.codigo,
            "estado": resultado["lote"].estado
        }

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "codigo_error": "SIN_ESPACIO_ZONA",
            "mensaje": f"La zona {zona.codigo} no tiene espacio suficiente. El lote queda bloqueado y se liberará automáticamente cuando se libere espacio.",
            "zona": zona.codigo
        }
    )

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

        lote_a_usar = lote
        if not lote:
            # El lote original ya no existe en estado disponible (perdió la carrera de concurrencia).
            # Se requiere conocer el producto para buscar alternativa; sin el lote original no es posible.
            raise HTTPException(status_code=409, detail={"codigo_error": "LOTE_RESERVADO", "mensaje": "Lote agotado o retenido."})

        lote_a_usar.estado = EstadoLote.RESERVADO_MANUFACTURA
        lote_a_usar.reservado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()
        return {"exito": True, "codigo_lote": lote_a_usar.codigo_lote, "estado": lote_a_usar.estado}
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

@router.post("/validar-credencial-empleado")
def validar_credencial_empleado(payload: CredencialPayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_auxiliar_diplomado)):
    """
    Verifica el código de empleado del Auxiliar Diplomado contra su
    credencial real, sin reservar ningún insumo ni tocar ningún lote.
    Se usa al ingresar el código por primera vez, para que la pantalla
    se desbloquee solo cuando el código es realmente correcto, no solo
    cuando el campo no está vacío.
    """
    operador = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    if not operador or operador.credencial != payload.credencial_operacion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo_error": "FIRMA_INVALIDA", "mensaje": "Código de empleado inválido."}
        )
    return {"exito": True, "mensaje": "Código de empleado validado correctamente."}

@router.post("/manufactura/iniciar-por-producto")
def iniciar_manufactura_por_producto(payload: ManufacturaPorProductoPayload, db: Session = Depends(get_db), usuario_auth = Depends(requiere_auxiliar_diplomado)):
    """
    Reserva un insumo para manufactura sin que el Auxiliar Diplomado elija
    el lote: se resuelve automáticamente el primer lote DISPONIBLE de ese
    producto con stock suficiente, igual que en el carrito del Técnico.

    Antes de reservar nada, valida que el producto realmente esté en la
    lista de insumos requeridos de la receta indicada — si la receta pide
    paracetamol y se intenta reservar amoxicilina, se rechaza aquí mismo,
    sin importar si hay stock de amoxicilina disponible.
    """
    liberar_timeouts_reserva(db)
    operador = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    if not operador or operador.credencial != payload.credencial_operacion:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"codigo_error": "FIRMA_INVALIDA", "mensaje": "Código de empleado inválido."}
        )

    insumo_requerido = db.query(InsumoRecetaRequerido).filter(
        InsumoRecetaRequerido.receta_id == payload.receta_id,
        InsumoRecetaRequerido.producto_id == payload.producto_id,
        InsumoRecetaRequerido.cubierto.is_(False)
    ).first()

    if not insumo_requerido:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "codigo_error": "INSUMO_NO_REQUERIDO",
                "mensaje": "Este producto no forma parte de los insumos que la receta solicita (o ya fue cubierto)."
            }
        )

    try:
        lote_a_usar = db.query(Lote).filter(
            Lote.producto_id == payload.producto_id,
            Lote.estado == EstadoLote.DISPONIBLE,
            Lote.cantidad >= payload.cantidad
        ).order_by(Lote.fecha_caducidad.asc()).with_for_update(nowait=True).first()

        if not lote_a_usar:
            raise HTTPException(
                status_code=409,
                detail={"codigo_error": "SIN_STOCK_DISPONIBLE", "mensaje": "No hay lotes con stock suficiente para este producto."}
            )

        # Se descuenta la cantidad reservada del lote (igual que en una
        # venta), en vez de bloquear el lote completo. Así el resto del
        # stock del mismo lote sigue disponible para otras recetas o ventas
        # mientras esta reserva está pendiente de validación/dispensación.
        lote_a_usar.cantidad -= payload.cantidad
        if lote_a_usar.cantidad == 0:
            lote_a_usar.estado = EstadoLote.AGOTADO

        insumo_requerido.cubierto = True
        insumo_requerido.lote_reservado_id = lote_a_usar.id
        insumo_requerido.reservado_hasta = datetime.now(timezone.utc) + timedelta(minutes=15)

        db.commit()
        return {"exito": True, "codigo_lote": lote_a_usar.codigo_lote, "estado": lote_a_usar.estado}
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"codigo_error": "LOTE_BLOQUEADO", "mensaje": "El lote disponible está siendo operado en otra transacción."})

# --- FLUJO DE PANTALLA: TÉCNICO (VENTAS) ---

@router.post("/ventas/atender", response_model=VentaDTO, status_code=status.HTTP_201_CREATED)
def atender_cliente(db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Simula la llegada de un nuevo cliente con su pedido completo. El
    Técnico no asigna ningún ID ni redacta ninguna receta: todo viene
    generado por MockCliente, igual que en la vida real un cliente llega
    con su propia identidad y, si corresponde, su receta ya emitida por
    un doctor.

    Si el pedido trae receta, se crea la RecetaMagistral junto con sus
    InsumoRecetaRequerido reales desde este mismo momento (no se espera
    a facturar): así el Auxiliar Diplomado puede empezar a reservar
    insumos en paralelo a que el Técnico siga atendiendo al cliente.
    """
    tecnico = UsuarioDAO.obtener_por_username(db, usuario_auth["username"])
    if not tecnico:
        raise HTTPException(status_code=404, detail="Técnico no encontrado en los registros.")

    pedido = MockCliente.simular_pedido_cliente(db)
    if not pedido["exito"]:
        raise HTTPException(status_code=409, detail=pedido["detalle"])

    nueva_venta = OperacionesDAO.crear_venta_iniciada(db, tecnico.id, pedido["id_cliente"])

    # La receta (si el pedido la trae) se fija desde el inicio de la venta,
    # no se pregunta nunca al Técnico al momento de facturar.
    nueva_venta.requiere_receta = pedido["requiere_receta"]
    nueva_venta.tipo_receta = pedido["tipo_receta"]
    nueva_venta.descripcion_receta = pedido["descripcion_receta"]

    for item_pedido in pedido["productos_solicitados"]:
        db.add(PedidoSolicitadoItem(
            venta_id=nueva_venta.id,
            producto_id=item_pedido["producto_id"],
            cantidad_solicitada=item_pedido["cantidad"],
        ))

    if pedido["requiere_receta"] and pedido["insumos_receta"]:
        nueva_receta = RecetaMagistral(
            venta_id=nueva_venta.id,
            tipo=pedido["tipo_receta"],
            descripcion=pedido["descripcion_receta"],
            estado=EstadoReceta.EN_ESPERA
        )
        db.add(nueva_receta)
        db.flush()  # asigna nueva_receta.id sin cerrar la transacción

        for insumo in pedido["insumos_receta"]:
            db.add(InsumoRecetaRequerido(
                receta_id=nueva_receta.id,
                producto_id=insumo["producto_id"],
                cantidad_requerida=insumo["cantidad"],
            ))

    db.commit()
    db.refresh(nueva_venta)
    return nueva_venta

@router.get("/ventas/{id}/pedido")
def obtener_pedido_solicitado(id: int, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Devuelve lo que el cliente pidió originalmente al ser atendido (antes
    de que el Técnico lo confirme contra inventario real), para que la
    pantalla pueda mostrarle qué debe ir agregando al carrito.
    """
    venta = db.query(Venta).filter(Venta.id == id).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada.")

    lineas = db.query(PedidoSolicitadoItem).filter(PedidoSolicitadoItem.venta_id == id).all()
    return {
        "id_cliente": venta.id_cliente,
        "requiere_receta": venta.requiere_receta,
        "tipo_receta": venta.tipo_receta,
        "descripcion_receta": venta.descripcion_receta,
        "productos_solicitados": [
            {
                "producto_id": linea.producto_id,
                "nombre": linea.producto.nombre,
                "cantidad_solicitada": linea.cantidad_solicitada,
                "cubierto": linea.cubierto,
            }
            for linea in lineas
        ]
    }

@router.post("/ventas/{id}/items/por-producto", status_code=status.HTTP_201_CREATED)
def agregar_producto_pedido(id: int, payload: ItemPorProductoPayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Confirma un producto del pedido del cliente sin que el Técnico elija
    el lote: se resuelve automáticamente el primer lote DISPONIBLE de ese
    producto con stock suficiente. Marca la línea correspondiente del
    pedido original como cubierta.
    """
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Orden de venta no activa.")

    try:
        lote_a_usar = db.query(Lote).filter(
            Lote.producto_id == payload.producto_id,
            Lote.estado == EstadoLote.DISPONIBLE,
            Lote.cantidad >= payload.cantidad
        ).order_by(Lote.fecha_caducidad.asc()).with_for_update(nowait=True).first()

        if not lote_a_usar:
            raise HTTPException(
                status_code=409,
                detail={"codigo_error": "SIN_STOCK_DISPONIBLE", "mensaje": "No hay lotes con stock suficiente para este producto."}
            )

        lote_a_usar.cantidad -= payload.cantidad
        if lote_a_usar.cantidad == 0:
            lote_a_usar.estado = EstadoLote.AGOTADO

        nuevo_item = ItemVenta(venta_id=venta.id, lote_id=lote_a_usar.id, cantidad=payload.cantidad)
        db.add(nuevo_item)

        linea_pedido = db.query(PedidoSolicitadoItem).filter(
            PedidoSolicitadoItem.venta_id == venta.id,
            PedidoSolicitadoItem.producto_id == payload.producto_id,
            PedidoSolicitadoItem.cubierto.is_(False)
        ).first()
        if linea_pedido:
            linea_pedido.cubierto = True

        db.commit()

        InventarioDAO.liberar_lotes_bloqueados_por_espacio(db)

        return {
            "exito": True,
            "mensaje": "Producto agregado al carrito y stock deducido",
            "lote_utilizado": lote_a_usar.codigo_lote
        }
    except OperationalError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El lote disponible está siendo operado en otra transacción.")

@router.post("/ventas/{id}/items", status_code=status.HTTP_201_CREATED)
def agregar_item_carrito(id: int, payload: ItemCarritoPayload, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Orden de venta no activa.")

    try:
        # Bloqueo a nivel de fila sobre el lote solicitado explícitamente
        lote = db.query(Lote).filter(Lote.id == payload.lote_id, Lote.estado == EstadoLote.DISPONIBLE).with_for_update(nowait=True).first()

        lote_a_usar = lote
        # Si el lote pedido no existe, no está disponible, o no tiene stock suficiente,
        # se busca automáticamente un lote alternativo del mismo producto antes de fallar.
        if not lote or lote.cantidad < payload.cantidad:
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

        lote_a_usar.cantidad -= payload.cantidad
        if lote_a_usar.cantidad == 0:
            lote_a_usar.estado = EstadoLote.AGOTADO

        nuevo_item = ItemVenta(venta_id=venta.id, lote_id=lote_a_usar.id, cantidad=payload.cantidad)
        db.add(nuevo_item)
        db.commit()

        # El stock recién reducido puede haber abierto espacio en la zona
        # física de este lote; se reintenta liberar lotes que esperaban turno.
        InventarioDAO.liberar_lotes_bloqueados_por_espacio(db)

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
def finalizar_facturacion(id: int, db: Session = Depends(get_db), usuario_auth: dict = Depends(requiere_tecnico)):
    """
    Cierra la venta. No recibe ningún dato sobre receta: requiere_receta,
    tipo_receta y descripcion_receta ya quedaron fijados en la Venta desde
    que el cliente fue atendido — el Técnico nunca decide ni pregunta esto
    al momento de facturar. La RecetaMagistral (si corresponde) y sus
    insumos reales ya se crearon en ese mismo momento, no aquí.
    """
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada o ya procesada.")

    # El stock físico ya fue deducido en la inserción del carrito.
    venta.estado = EstadoVenta.COMPLETADA

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
            InventarioDAO.liberar_lotes_bloqueados_por_espacio(db)
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

    Si la venta ya derivó una RecetaMagistral, no se elimina físicamente
    (la FK venta_id es RESTRICT, así que el DELETE fallaría). En ese caso
    se descarta la receta y se vacía/cierra la venta sin borrar el registro,
    preservando la trazabilidad del intento fallido.
    """
    venta = db.query(Venta).filter(Venta.id == id, Venta.estado == EstadoVenta.INICIADA).first()
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada o ya procesada.")

    receta_asociada = db.query(RecetaMagistral).filter(RecetaMagistral.venta_id == venta.id).first()

    # Se capturan los IDs de lote afectados ANTES de borrar los items,
    # ya que venta.items quedará vacío tras los db.delete(item) de abajo.
    lotes_afectados_ids = {item.lote_id for item in venta.items}

    for item in venta.items:
        lote = db.query(Lote).filter(Lote.id == item.lote_id).with_for_update().first()
        if lote:
            lote.cantidad += item.cantidad
            if lote.estado == EstadoLote.AGOTADO and lote.cantidad > 0:
                lote.estado = EstadoLote.DISPONIBLE

    for item in list(venta.items):
        db.delete(item)

    db.flush()

    # La restitución de stock puede, en un caso borde, hacer que el propio
    # lote afectado exceda ahora la capacidad de su zona (si esa zona se
    # llenó con otros lotes mientras este estaba parcialmente vendido).
    # Se revalida cada lote restituido contra su zona antes de comitear.
    for lote_id_restituido in lotes_afectados_ids:
        lote_revalidado = db.query(Lote).filter(Lote.id == lote_id_restituido).first()
        if lote_revalidado and lote_revalidado.zona_id and lote_revalidado.estado != EstadoLote.BLOQUEADO:
            ocupacion = InventarioDAO.calcular_ocupacion_zona(db, lote_revalidado.zona_id)
            zona = db.query(ZonaAlmacen).filter(ZonaAlmacen.id == lote_revalidado.zona_id).first()
            if zona and ocupacion > zona.capacidad_maxima_unidades:
                lote_revalidado.estado = EstadoLote.BLOQUEADO
                lote_revalidado.causa_bloqueo = CausaBloqueo.SIN_ESPACIO_ZONA

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

    insumos_pendientes = [insumo for insumo in receta.insumos_requeridos if not insumo.cubierto]
    if insumos_pendientes:
        nombres_pendientes = ", ".join(insumo.producto.nombre for insumo in insumos_pendientes)
        raise HTTPException(
            status_code=400,
            detail={
                "codigo_error": "INSUMOS_INCOMPLETOS",
                "mensaje": f"Faltan insumos por reservar antes de validar: {nombres_pendientes}."
            }
        )

    try:
        # Validación sanitaria del lote reservado para cada insumo real de la receta.
        for insumo in receta.insumos_requeridos:
            lote_reservado = insumo.lote_reservado
            if lote_reservado and lote_reservado.estado in [EstadoLote.RETIRADO, EstadoLote.BLOQUEADO, EstadoLote.CUARENTENA]:
                receta.estado = EstadoReceta.DESCARTADA
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail={"codigo_error": "INSUMO_RECHAZADO", "mensaje": f"El insumo {insumo.producto.nombre} no cumple el estado sanitario requerido. Receta descartada."}
                )

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

        # Una vez validada, la reserva ya no expira por timeout: se limpia
        # reservado_hasta para que liberar_timeouts_reserva nunca revierta
        # un insumo que ya pasó el control sanitario.
        for insumo in receta.insumos_requeridos:
            insumo.reservado_hasta = None

        receta.estado = EstadoReceta.EN_ELABORACION
        receta.ticket_validacion = f"TCK-{uuid.uuid4().hex[:10].upper()}"
        db.commit()

        # Si hubo alguna reasignación dentro del loop, el stock de algún lote
        # alternativo se redujo; se reintenta liberar lotes en espera de zona.
        InventarioDAO.liberar_lotes_bloqueados_por_espacio(db)

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