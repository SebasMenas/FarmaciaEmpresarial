from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.models.entidades import Lote, EstadoLote
from typing import Any
import random

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