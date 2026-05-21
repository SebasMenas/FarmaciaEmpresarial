from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional

class UsuarioBase(BaseModel):
    username:   str
    nombre:     str
    apellidos:  str
    rut:        str
    sexo:       str
    rol:        str

    @field_validator('rut')
    @classmethod
    def validar_rut_chileno(cls, valor: str) -> str:
        # Limpieza de caracteres
        rut_limpio = valor.replace(".", "").replace("-", "").replace(" ", "").upper()

        if len(rut_limpio) < 2:
            raise ValueError("RUT demasiado corto.")

        # Separar cuerpo y DV
        cuerpo = rut_limpio[:-1]
        dv_ingresado = rut_limpio[-1]

        if not cuerpo.isdigit():
            raise ValueError("El cuerpo del RUT solo puede contener números.")

        # Algoritmo para DV valido (sugerido IA)
        suma = 0
        multiplicador = 2
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador == 8: multiplicador = 2
                
        resto = suma % 11
        dv_matematico = 11 - resto
        
        if dv_matematico == 11: dv_esperado = "0"
        elif dv_matematico == 10: dv_esperado = "K"
        else: dv_esperado = str(dv_matematico)

        if dv_ingresado != dv_esperado:
            raise ValueError(f"RUT inválido. El dígito verificador debería ser {dv_esperado}")

        return rut_limpio

class UsuarioCreate(UsuarioBase):
    """Esquema para recibir datos al crear un usuario (incluye password)"""
    password: str

class UsuarioResponse(UsuarioBase):
    """Esquema para enviar datos al frontend (oculta el password)"""
    id: int
    
    # Permite convertir modelos de SQLAlchemy a Pydantic automáticamente
    model_config = ConfigDict(from_attributes=True)

class PasswordUpdate(BaseModel):
    password_actual:    str
    password_nueva:     str