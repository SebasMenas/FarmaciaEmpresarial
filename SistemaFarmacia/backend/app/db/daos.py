from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, defer
from sqlalchemy import func, case
from datetime import date, timedelta
import random
from app.models.entidades import (
    Usuario, Lote, Producto, Laboratorio, ZonaAlmacen,
    Tarea, Venta, ItemVenta, RecetaMagistral,
    EstadoLote, EstadoReceta, EstadoVenta, IndicacionAmbiental, CausaBloqueo
)

class UsuarioDAO:
    @staticmethod
    def obtener_por_username(db: Session, username: str) -> Optional[Usuario]:
        return db.query(Usuario).filter(Usuario.username == username).first()

    @staticmethod
    def listar_empleados(db: Session) -> List[Usuario]:
        """Aplica defer para omitir el volcado del hash a memoria a nivel de ORM."""
        return db.query(Usuario).options(defer(Usuario.password_hash)).all()
    
    @staticmethod
    def crear_empleado(
        db: Session, username: str, password_hash: str, nombre: str,
        apellidos: str, rut: str, rol: str, credencial: str | None = None, activo: bool = True
    ) -> Usuario:
        nuevo_usuario = Usuario(
            username=username, password_hash=password_hash, nombre=nombre,
            apellidos=apellidos, rut=rut, rol=rol, credencial=credencial, activo=activo
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario

    @staticmethod
    def actualizar_empleado(db: Session, usuario_id: int, datos_actualizacion: dict) -> Optional[Usuario]:
        """Modifica los atributos de un empleado existente (Fase de Administración)."""
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            return None
        
        for key, value in datos_actualizacion.items():
            if hasattr(usuario, key) and value is not None:
                setattr(usuario, key, value)
                
        db.commit()
        db.refresh(usuario)
        return usuario

class CatalogoDAO:
    """
    Capa de acceso para el catálogo de Producto y Laboratorio, independiente
    del estado físico del inventario. Permite consultar/reabastecer un
    producto incluso si todavía no tiene ningún lote ingresado, y reutilizar
    laboratorios certificados existentes en vez de crear uno por cada pedido.
    """

    @staticmethod
    def listar_productos(db: Session) -> List[Dict[str, Any]]:
        """
        Devuelve cada producto del catálogo junto a su stock total agregado
        (suma de Lote.cantidad en estados operativos). Usa LEFT JOIN para que
        productos sin ningún lote todavía aparezcan igual, con stock_total=0.
        """
        estados_operativos = [
            EstadoLote.DISPONIBLE, EstadoLote.PROXIMO_A_VENCER,
            EstadoLote.RESERVADO_VENTA, EstadoLote.RESERVADO_MANUFACTURA
        ]
        filas = db.query(
            Producto,
            func.coalesce(
                func.sum(
                    case((Lote.estado.in_(estados_operativos), Lote.cantidad), else_=0)
                ), 0
            ).label("stock_total")
        ).outerjoin(Lote, Lote.producto_id == Producto.id).group_by(Producto.id).all()

        resultados = []
        for producto, stock_total in filas:
            resultados.append({
                "id": producto.id,
                "nombre": producto.nombre,
                "componente_activos": producto.componente_activos,
                "concentracion": producto.concentracion,
                "tipo_producto": producto.tipo_producto,
                "indicacion_ambiental": producto.indicacion_ambiental,
                "stock_total": int(stock_total),
            })
        return resultados

    @staticmethod
    def obtener_producto_por_nombre(db: Session, nombre: str) -> Optional[Producto]:
        return db.query(Producto).filter(func.lower(Producto.nombre) == nombre.strip().lower()).first()

    @staticmethod
    def listar_laboratorios(db: Session) -> List[Laboratorio]:
        return db.query(Laboratorio).all()

    @staticmethod
    def obtener_o_crear_laboratorio_certificado(db: Session) -> Laboratorio:
        """
        Reutiliza un laboratorio certificado ya existente en vez de crear
        uno nuevo en cada solicitud de reabastecimiento. Solo crea uno
        nuevo si la tabla está completamente vacía (primer arranque del
        sistema), evitando que 'laboratorios' crezca sin control.
        """
        laboratorio = db.query(Laboratorio).filter(Laboratorio.certificado == True).first()
        if laboratorio:
            return laboratorio

        nuevo = Laboratorio(nombre=f"Laboratorio Bio_{random.randint(100, 999)}", certificado=True)
        db.add(nuevo)
        db.flush()
        return nuevo


class InventarioDAO:
    @staticmethod
    def obtener_estado_almacenamiento(db: Session) -> List[Lote]:
        return db.query(Lote).join(Lote.producto).join(Lote.laboratorio).all()

    @staticmethod
    def obtener_disponibles_para_venta(db: Session) -> List[Lote]:
        """
        Catálogo restringido para la pantalla de venta (carrito del Técnico y
        selección de insumos del Auxiliar Diplomado). Solo expone lotes con
        stock real y estado DISPONIBLE; oculta lotes retirados, en cuarentena,
        bloqueados o ya reservados por otra operación.
        """
        return db.query(Lote).join(Lote.producto).filter(
            Lote.estado == EstadoLote.DISPONIBLE,
            Lote.cantidad > 0
        ).all()
    
    @staticmethod
    def obtener_alertas_caducidad(db: Session, dias_limite: int = 30) -> List[Lote]:
        """Aplica exclusión estricta de estados inactivos o mermas."""
        fecha_limite = date.today() + timedelta(days=dias_limite)
        estados_validos = [EstadoLote.DISPONIBLE, EstadoLote.PROXIMO_A_VENCER]
        
        return db.query(Lote).filter(
            Lote.fecha_caducidad <= fecha_limite,
            Lote.cantidad > 0,
            Lote.estado.in_(estados_validos)
        ).all()

    @staticmethod
    def cambiar_estado_lote(db: Session, lote_id: int, nuevo_estado: EstadoLote) -> Optional[Lote]:
        lote = db.query(Lote).filter(Lote.id == lote_id).first()
        if lote:
            lote.estado = nuevo_estado
            db.commit()
            db.refresh(lote)
        return lote

    @staticmethod
    def calcular_capacidad_por_zona(db: Session) -> List[Dict[str, Any]]:
        """Calcula la ocupación real de cada una de las 4 zonas físicas."""
        zonas = db.query(ZonaAlmacen).order_by(ZonaAlmacen.codigo).all()

        estados_operativos = [
            EstadoLote.DISPONIBLE, EstadoLote.PROXIMO_A_VENCER,
            EstadoLote.RESERVADO_VENTA, EstadoLote.RESERVADO_MANUFACTURA,
            EstadoLote.CUARENTENA, EstadoLote.BLOQUEADO
        ]
        ocupacion = db.query(
            Lote.zona_id,
            func.sum(Lote.cantidad).label("total_unidades")
        ).filter(
            Lote.zona_id.isnot(None),
            Lote.estado.in_(estados_operativos)
        ).group_by(Lote.zona_id).all()

        mapa_ocupacion = {zona_id: total or 0 for zona_id, total in ocupacion}

        resultados = []
        for zona in zonas:
            ocupacion_actual = mapa_ocupacion.get(zona.id, 0)
            resultados.append({
                "id": zona.id,
                "codigo": zona.codigo,
                "tipo_ambiental": zona.tipo_ambiental,
                "capacidad_maxima_unidades": zona.capacidad_maxima_unidades,
                "ocupacion_actual": ocupacion_actual,
                "espacio_disponible": max(0, zona.capacidad_maxima_unidades - ocupacion_actual),
            })
        return resultados

    @staticmethod
    def listar_zonas(db: Session) -> List[ZonaAlmacen]:
        return db.query(ZonaAlmacen).order_by(ZonaAlmacen.codigo).all()

    @staticmethod
    def actualizar_capacidad_zona(db: Session, zona_id: int, capacidad: int) -> Optional[ZonaAlmacen]:
        """Recalibra el techo de capacidad física de una zona ya existente."""
        zona = db.query(ZonaAlmacen).filter(ZonaAlmacen.id == zona_id).first()
        if not zona:
            return None
        zona.capacidad_maxima_unidades = capacidad
        db.commit()
        db.refresh(zona)
        return zona

    @staticmethod
    def calcular_ocupacion_zona(db: Session, zona_id: int, excluir_lote_id: int | None = None) -> int:
        """
        Suma la cantidad de todos los lotes operativos asignados a una zona.

        excluir_lote_id permite calcular "cuánto ocupan los DEMÁS lotes",
        necesario cuando se está validando si el propio lote (que ya tiene
        esa zona asignada) cabe al reasignarlo: sin excluirlo, su propia
        cantidad se contaría dos veces y generaría capacidad falsa.
        """
        estados_operativos = [
            EstadoLote.DISPONIBLE, EstadoLote.PROXIMO_A_VENCER,
            EstadoLote.RESERVADO_VENTA, EstadoLote.RESERVADO_MANUFACTURA,
            EstadoLote.CUARENTENA, EstadoLote.BLOQUEADO
        ]
        query = db.query(func.sum(Lote.cantidad)).filter(
            Lote.zona_id == zona_id,
            Lote.estado.in_(estados_operativos)
        )
        if excluir_lote_id is not None:
            query = query.filter(Lote.id != excluir_lote_id)
        total = query.scalar()
        return total or 0

    @staticmethod
    def asignar_zona_lote(db: Session, lote: Lote, zona: ZonaAlmacen) -> Dict[str, Any]:
        """
        Intenta asignar un lote a una zona física, validando que haya espacio.
        Si cabe, el lote queda DISPONIBLE en esa zona. Si no cabe, el lote
        queda BLOQUEADO con causa_bloqueo=SIN_ESPACIO_ZONA, registrando la
        zona deseada para que el mecanismo de liberación automática lo
        reintente cuando una venta u otra salida abra espacio.

        Si el lote YA está en esa misma zona, retorna {"ya_en_zona": True}
        sin tocar nada — evita sumar su propia cantidad dos veces a la
        ocupación calculada (capacidad falsa) y evita un movimiento sin
        efecto real. El llamador (endpoint) decide si avisa al usuario.

        Retorna {"asignado": bool, "lote": Lote, "ya_en_zona": bool}.
        """
        if lote.zona_id == zona.id:
            return {"asignado": True, "lote": lote, "ya_en_zona": True}

        # Se excluye el propio lote del cálculo de ocupación: si venía de
        # otra zona, su cantidad no debe contarse en la zona destino hasta
        # que la asignación se confirme.
        ocupacion_actual = InventarioDAO.calcular_ocupacion_zona(db, zona.id, excluir_lote_id=lote.id)

        if ocupacion_actual + lote.cantidad <= zona.capacidad_maxima_unidades:
            lote.zona_id = zona.id
            lote.estado = EstadoLote.DISPONIBLE
            lote.causa_bloqueo = None
            db.commit()
            db.refresh(lote)
            return {"asignado": True, "lote": lote, "ya_en_zona": False}

        lote.zona_id = zona.id  # se registra la zona deseada para el reintento automático
        lote.estado = EstadoLote.BLOQUEADO
        lote.causa_bloqueo = CausaBloqueo.SIN_ESPACIO_ZONA
        db.commit()
        db.refresh(lote)
        return {"asignado": False, "lote": lote, "ya_en_zona": False}

    @staticmethod
    def liberar_lotes_bloqueados_por_espacio(db: Session) -> List[Lote]:
        """
        Revisa los lotes BLOQUEADOS por falta de espacio (no por sospecha de
        defecto sanitario) y los pasa a DISPONIBLE si, tras una venta u otra
        salida de stock, ya hay espacio suficiente en su zona pendiente.

        Se debe llamar tras cualquier operación que reduzca Lote.cantidad
        (factura de venta, manufactura, cancelación con reposición, etc.).
        Procesa en orden de fecha_ingreso (FIFO) para no favorecer lotes
        más nuevos sobre los que esperan hace más tiempo.
        """
        pendientes = db.query(Lote).filter(
            Lote.estado == EstadoLote.BLOQUEADO,
            Lote.causa_bloqueo == CausaBloqueo.SIN_ESPACIO_ZONA,
            Lote.zona_id.isnot(None)
        ).order_by(Lote.fecha_ingreso.asc()).all()

        liberados = []
        for lote in pendientes:
            ocupacion_actual = InventarioDAO.calcular_ocupacion_zona(db, lote.zona_id)
            # calcular_ocupacion_zona ya incluye este lote bloqueado en la suma
            # (BLOQUEADO está en estados_operativos), así que se compara
            # directamente contra la capacidad sin sumarlo de nuevo.
            zona = db.query(ZonaAlmacen).filter(ZonaAlmacen.id == lote.zona_id).first()
            if zona and ocupacion_actual <= zona.capacidad_maxima_unidades:
                lote.estado = EstadoLote.DISPONIBLE
                lote.causa_bloqueo = None
                liberados.append(lote)

        if liberados:
            db.commit()
        return liberados


class MonitoreoDAO:
    @staticmethod
    def obtener_tareas_por_fecha(db: Session, fecha_consulta: date) -> List[Tarea]:
        return db.query(Tarea).filter(Tarea.fecha == fecha_consulta).all()
        
    @staticmethod
    def crear_tarea(db: Session, descripcion: str, asignado_a_id: int, fecha: date) -> Tarea:
        nueva_tarea = Tarea(descripcion=descripcion, asignado_a_id=asignado_a_id, fecha=fecha)
        db.add(nueva_tarea)
        db.commit()
        db.refresh(nueva_tarea)
        return nueva_tarea

    @staticmethod
    def actualizar_estado_tarea(db: Session, tarea_id: int, completada: bool) -> Optional[Tarea]:
        tarea = db.query(Tarea).filter(Tarea.id == tarea_id).first()
        if tarea:
            tarea.completada = completada
            db.commit()
            db.refresh(tarea)
        return tarea

class OperacionesDAO:
    @staticmethod
    def buscar_lote_alternativo(db: Session, producto_id: int, cantidad_requerida: int, excluir_lote_id: int):
        """
        Busca un lote DISPONIBLE del mismo producto con stock suficiente,
        distinto al lote que falló. Usado tanto por el flujo de Venta (Técnico)
        como por el flujo de Manufactura (Auxiliar Diplomado) cuando el lote
        originalmente seleccionado pierde la carrera por concurrencia o queda
        sin stock suficiente.

        Aplica bloqueo a nivel de fila sobre el candidato encontrado para que
        la reasignación misma sea segura ante transacciones concurrentes.
        """
        return db.query(Lote).filter(
            Lote.producto_id == producto_id,
            Lote.id != excluir_lote_id,
            Lote.estado == EstadoLote.DISPONIBLE,
            Lote.cantidad >= cantidad_requerida
        ).with_for_update(nowait=True).first()

    @staticmethod
    def crear_venta_iniciada(db: Session, tecnico_id: int, id_cliente: str) -> Venta:
        import uuid
        codigo_unico = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        nueva_venta = Venta(
            codigo_venta=codigo_unico,
            tecnico_id=tecnico_id,
            id_cliente=id_cliente,
            estado=EstadoVenta.INICIADA
        )
        db.add(nueva_venta)
        db.commit()
        db.refresh(nueva_venta)
        return nueva_venta

    @staticmethod
    def obtener_cola_recetas(db: Session) -> List[RecetaMagistral]:
        """Retorna las recetas estructuradas bajo el modelo FIFO."""
        estados_activos = [EstadoReceta.EN_ESPERA, EstadoReceta.EN_ELABORACION]
        return db.query(RecetaMagistral).filter(
            RecetaMagistral.estado.in_(estados_activos)
        ).order_by(RecetaMagistral.fecha_ingreso.asc()).all()