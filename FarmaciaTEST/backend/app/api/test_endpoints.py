from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from ..test.mock_laboratorio import MockLaboratorio
from ..test.mock_cliente import MockCliente

router = APIRouter(prefix="/test", tags=["Mocks de Simulación Externa"])

@router.post("/simular-proveedor-certificado")
def simular_entrada_valida(db: Session = Depends(get_db)):
    """Inyecta un lote de un laboratorio con certificación sanitaria vigente"""
    return MockLaboratorio.simular_ingreso_lote(db, certificado=True)

@router.post("/simular-proveedor-no-certificado")
def simular_entrada_invalida(db: Session = Depends(get_db)):
    """Prueba el filtro de trazabilidad forzando el rechazo de un laboratorio no certificado"""
    return MockLaboratorio.simular_ingreso_lote(db, certificado=False)

@router.post("/simular-consumo-cliente")
def simular_compra(db: Session = Depends(get_db)):
    """Dispara un evento aleatorio de decremento de stock en el inventario activo"""
    return MockCliente.simular_consumo_aleatorio(db)