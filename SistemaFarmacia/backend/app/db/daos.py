from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, defer
from sqlalchemy import func
from datetime import date, timedelta
from app.models.entidades import (
    Usuario, Lote, Producto, CapacidadAlmacen, 
    Tarea, Venta, ItemVenta, RecetaMagistral,
    EstadoLote, EstadoReceta, EstadoVenta, IndicacionAmbiental
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
        """Calcula el volumen de ocupación agrupando los lotes por requerimiento ambiental."""
        capacidades = db.query(CapacidadAlmacen).all()
        
        ocupacion = db.query(
            Producto.indicacion_ambiental,
            func.sum(Lote.cantidad).label("total_unidades")
        ).join(Lote, Lote.producto_id == Producto.id).filter(
            Lote.estado.in_([
                EstadoLote.DISPONIBLE, EstadoLote.PROXIMO_A_VENCER, 
                EstadoLote.RESERVADO_VENTA, EstadoLote.RESERVADO_MANUFACTURA, 
                EstadoLote.CUARENTENA, EstadoLote.BLOQUEADO
            ])
        ).group_by(Producto.indicacion_ambiental).all()

        mapa_ocupacion = {zona: total or 0 for zona, total in ocupacion}
        
        resultados = []
        for cap in capacidades:
            resultados.append({
                "zona": cap.zona,
                "capacidad_maxima_unidades": cap.capacidad_maxima_unidades,
                "ocupacion_actual": mapa_ocupacion.get(cap.zona, 0)
            })
        return resultados
    
    @staticmethod
    def upsert_capacidad_zona(db: Session, zona: IndicacionAmbiental, capacidad: int) -> CapacidadAlmacen:
        """Inserta o actualiza el techo de capacidad física para una zona específica."""
        registro = db.query(CapacidadAlmacen).filter(CapacidadAlmacen.zona == zona).first()
        if registro:
            registro.capacidad_maxima_unidades = capacidad
        else:
            registro = CapacidadAlmacen(zona=zona, capacidad_maxima_unidades=capacidad)
            db.add(registro)
        db.commit()
        db.refresh(registro)
        return registro

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