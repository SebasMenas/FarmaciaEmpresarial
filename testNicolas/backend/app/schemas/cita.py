from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class CitaBase(BaseModel):
    fecha_hora: datetime
    asunto: str
    docente_id: int
    paciente_id: Optional[int] = None

class CitaCreate(CitaBase):
    pass

class CitaResponse(CitaBase):
    id: int
    usuario_id: int
    estado: int
    
    model_config = ConfigDict(from_attributes=True)