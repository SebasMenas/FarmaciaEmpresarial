from sqlalchemy.orm import Session
from app.models.entidades import Laboratorio, Producto, Lote, EstadoLote
from app.testing.generador_datos import GeneradorDatos
import random
from datetime import date, timedelta

class MockLaboratorio:
    @staticmethod
    def simular_ingreso_lote(db: Session, certificado: bool = True):
        """
        Simula físicamente la inyección de un lote desde un laboratorio proveedor.
        Permite testear el filtro de laboratorio sanitario del backend.
        """
        # Crear o seleccionar un laboratorio de prueba
        nombre_lab = f"Laboratorio Bio_{random.randint(100, 999)}"
        lab = db.query(Laboratorio).filter(Laboratorio.nombre == nombre_lab).first()
        if not lab:
            lab = Laboratorio(nombre=nombre_lab, certificado=certificado)
            db.add(lab)
            db.commit()
            db.refresh(lab)

        # Seleccionar un producto base de simulación
        prod_datos = GeneradorDatos.obtener_producto_aleatorio()
        prod = db.query(Producto).filter(Producto.nombre == prod_datos["nombre"]).first()
        if not prod:
            prod = Producto(
                nombre=prod_datos["nombre"],
                componente_activos=prod_datos["componente"],
                tipo_producto=prod_datos["tipo"],
                indicacion_ambiental=prod_datos["ambiente"],
                stock_max=500
            )
            db.add(prod)
            db.commit()
            db.refresh(prod)

        # Fabricar metadatos del lote
        num_aleatorio = random.randint(100, 999)
        nuevo_lote = Lote(
            codigo_lote=f"L-{num_aleatorio}",
            codigo_trazabilidad=f"TZ-{num_aleatorio}",
            producto_id=prod.id,
            laboratorio_id=lab.id,
            cantidad=random.randint(50, 200),
            fecha_caducidad=date.today() + timedelta(days=random.randint(-10, 120)), # Puede generar vencidos
            ubicacion_almacen=f"Estante-{random.choice(['A', 'B', 'C'])}-Nivel{random.randint(1,4)}",
            estado=EstadoLote.DISPONIBLE if bool(lab.certificado) else EstadoLote.RETIRADO
        )
        
        # Aplicacion de la regla de trazabilidad sanitaria normativa de Fase 1
        if not bool(lab.certificado):
            # Si el laboratorio no cumple, simulamos el aborto transaccional
            return {"exito": False, "detalle": f"Transacción abortada: {lab.nombre} no posee certificación sanitaria."}
        
        try:
            db.add(nuevo_lote)
            db.commit()
            db.refresh(nuevo_lote)
            return {"exito": True, "lote_id": nuevo_lote.id, "codigo": nuevo_lote.codigo_lote, "estado": nuevo_lote.estado}
        except Exception as e:
            db.rollback()
            return {"exito": False, "detalle": str(e)}