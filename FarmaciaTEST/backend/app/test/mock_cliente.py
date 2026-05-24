from sqlalchemy.orm import Session
from app.models.entidades import Lote, EstadoLote
from typing import Any
import random

class MockCliente:
    @staticmethod
    def simular_consumo_aleatorio(db: Session) -> dict[str, Any]:
        # Consultar un lote
        lote = db.query(Lote).filter(Lote.estado == "DISPONIBLE", Lote.cantidad > 0).first()
        
        if not lote:
            return {"exito": False, "detalle": "No hay lotes disponibles con stock para conocer."}
            
        cantidad_a_comprar = random.randint(1, 10)
        
        # Se extrae el valor primitivo
        cantidad_actual = getattr(lote, "cantidad")
        if not isinstance(cantidad_actual, int):
            cantidad_actual = int(cantidad_actual)
        
        if cantidad_actual < cantidad_a_comprar:
            cantidad_a_comprar = cantidad_actual
            
        # Modificación de atributos mediante setattr para evadir la restricción estricta Column[int]
        nuevo_stock = cantidad_actual - cantidad_a_comprar
        setattr(lote, "cantidad", nuevo_stock)
        
        if nuevo_stock == 0:
            setattr(lote, "estado", EstadoLote.AGOTADO)
            
        try:
            db.commit()
            db.refresh(lote)
            
            stock_final = getattr(lote, "cantidad")
            estado_final = getattr(lote, "estado")
            codigo_final = getattr(lote, "codigo_lote")
            
            return {
                "exito": True, 
                "lote_afectado": str(codigo_final), 
                "unidades_consumidas": cantidad_a_comprar, 
                "stock_remanente": int(stock_final),
                "nuevo_estado": str(estado_final)
            }
        except Exception as e:
            db.rollback()
            return {"exito": False, "detalle": str(e)}