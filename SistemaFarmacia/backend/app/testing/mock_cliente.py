from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.models.entidades import Lote, EstadoLote, Producto, TipoProducto
from typing import Any
import random
import uuid

class MockCliente:
    @staticmethod
    def simular_consumo_aleatorio(db: Session) -> dict[str, Any]:
        try:
            # Bloqueo Pesimista
            lote = db.query(Lote).filter(
                Lote.estado == EstadoLote.DISPONIBLE, 
                Lote.cantidad > 0
            ).with_for_update(nowait=True).first()
            
            if not lote:
                return {"exito": False, "detalle": "No hay lotes disponibles o se encuentran reservados en otra transacción."}
                
            cantidad_a_comprar = random.randint(1, 10)
            
            if lote.cantidad < cantidad_a_comprar:
                cantidad_a_comprar = lote.cantidad
                
            # Mutacion directa del objeto (ORM SQLAlchemy nativo)
            lote.cantidad = lote.cantidad - cantidad_a_comprar
            
            if lote.cantidad == 0:
                lote.estado = EstadoLote.AGOTADO
                
            db.commit()
            db.refresh(lote)
            
            return {
                "exito": True, 
                "lote_afectado": lote.codigo_lote, 
                "unidades_consumidas": cantidad_a_comprar, 
                "stock_remanente": lote.cantidad,
                "nuevo_estado": lote.estado
            }
            
        except OperationalError:
            # Falla controlada si un Auxiliar y el Mock interactuan en el mismo milisegundo
            db.rollback()
            return {"exito": False, "detalle": "Falla de concurrencia simulada interceptada exitosamente."}
        except Exception as e:
            db.rollback()
            return {"exito": False, "detalle": str(e)}

    @staticmethod
    def simular_pedido_cliente(db: Session) -> dict[str, Any]:
        """
        Simula la llegada de un cliente con un pedido completo.

        Regla de negocio (simplificada a propósito para no introducir un
        estado nuevo de "requiere receta por producto"): TODO medicamento
        que el cliente pide requiere receta, sin excepción. Los productos
        generales de farmacia (insumos médicos, cosméticos: bloqueador,
        mascarillas, pañuelos, etc.) nunca la requieren.

        Los insumos de la receta se eligen siempre entre medicamentos que
        existen realmente en el catálogo con stock disponible — nunca se
        inventa un nombre. Si no hay medicamentos reales disponibles, el
        pedido simplemente no incluye receta (la venta de productos
        generales, si los hay, puede seguir su curso igual).

        - 1 medicamento elegido -> receta NORMAL (se dispensa tal cual).
        - 2+ medicamentos elegidos -> receta MAGISTRAL (se combinan en un
          producto nuevo simulado; no se crea ninguna fila real en Producto
          para ese resultado).

        Retorna:
        - id_cliente
        - productos_solicitados: lista de {producto_id, nombre, cantidad}
          (solo productos GENERALES, sin receta)
        - requiere_receta, tipo_receta, descripcion_receta
        - insumos_receta: lista de {producto_id, nombre, cantidad} si
          requiere_receta es True (vacía si no hay medicamentos disponibles)
        """
        productos_con_stock = db.query(Producto).join(Lote).filter(
            Lote.estado == EstadoLote.DISPONIBLE,
            Lote.cantidad > 0
        ).distinct().all()

        if not productos_con_stock:
            return {"exito": False, "detalle": "No hay productos con stock disponible para simular un pedido."}

        productos_generales = [p for p in productos_con_stock if p.tipo_producto != TipoProducto.MEDICAMENTO]
        medicamentos_disponibles = [p for p in productos_con_stock if p.tipo_producto == TipoProducto.MEDICAMENTO]

        # --- Productos generales (nunca requieren receta) ---
        productos_solicitados = []
        if productos_generales:
            cantidad_generales = random.randint(0, min(2, len(productos_generales)))
            for producto in random.sample(productos_generales, cantidad_generales):
                productos_solicitados.append({
                    "producto_id": producto.id,
                    "nombre": producto.nombre,
                    "cantidad": random.randint(1, 5),
                })

        # --- Medicamentos (siempre requieren receta si el cliente pide alguno) ---
        requiere_receta = False
        tipo_receta = None
        descripcion_receta = None
        insumos_receta = []

        if medicamentos_disponibles and random.random() < 0.6:
            # El cliente trae receta solo si decide pedir algún medicamento.
            # Si no hay medicamentos reales en el sistema, jamás se genera
            # una receta que pida algo que no existe.
            cantidad_insumos = random.randint(1, min(2, len(medicamentos_disponibles)))
            medicamentos_elegidos = random.sample(medicamentos_disponibles, cantidad_insumos)

            for medicamento in medicamentos_elegidos:
                insumos_receta.append({
                    "producto_id": medicamento.id,
                    "nombre": medicamento.nombre,
                    "cantidad": random.randint(1, 3),
                })

            requiere_receta = True
            nombres = [insumo["nombre"] for insumo in insumos_receta]

            if len(insumos_receta) == 1:
                tipo_receta = "NORMAL"
                descripcion_receta = f"Dispensar {nombres[0]} según indicación médica."
            else:
                tipo_receta = "MAGISTRAL"
                descripcion_receta = (
                    f"Elaboración magistral combinando {' + '.join(nombres)} "
                    f"en un producto compuesto único."
                )

        # Si ni hubo productos generales ni medicamentos elegibles, no hay
        # nada que vender en este pedido; se simula de nuevo en otro intento.
        if not productos_solicitados and not insumos_receta:
            return {"exito": False, "detalle": "El cliente no encontró ningún producto disponible que necesitara."}

        return {
            "exito": True,
            "id_cliente": f"CLI-{uuid.uuid4().hex[:6].upper()}",
            "productos_solicitados": productos_solicitados,
            "requiere_receta": requiere_receta,
            "tipo_receta": tipo_receta,
            "descripcion_receta": descripcion_receta,
            "insumos_receta": insumos_receta,
        }