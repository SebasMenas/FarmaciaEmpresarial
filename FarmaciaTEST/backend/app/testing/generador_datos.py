import random

class GeneradorDatos:
    @staticmethod
    def generar_rut_valido() -> str:
        """Genera un RUT chileno con formato válido y dígito verificador correcto"""
        cuerpo = random.randint(11111111, 22222222)
        # Algoritmo del módulo 11 para el dígito verificador (IA)
        suma = 0
        multiplo = 2
        for c in reversed(str(cuerpo)):
            suma += int(c) * multiplo
            multiplo = 4 if multiplo == 7 else multiplo + 1
        dvr = 11 - (suma % 11)
        dv = 'K' if dvr == 10 else '0' if dvr == 11 else str(dvr)
        return f"{cuerpo}-{dv}"

    @staticmethod
    def obtener_producto_aleatorio() -> dict:
        productos_mock = [
            {"nombre": "Amoxicilina", "componente": "Amoxicilina Trihidrato", "tipo": "MEDICAMENTO", "ambiente": "AMBIENTE"},
            {"nombre": "Insulina Glargina", "componente": "Insulina", "tipo": "MEDICAMENTO", "ambiente": "REFRIGERADO"},
            {"nombre": "Base Dermatológica", "componente": "Glicerina/Vasenila", "tipo": "COSMETICO", "ambiente": "AMBIENTE"},
            {"nombre": "Jeringa Desechable", "componente": "Plástico/Acero", "tipo": "INSUMO_MEDICO", "ambiente": "AMBIENTE"}
        ]
        return random.choice(productos_mock)