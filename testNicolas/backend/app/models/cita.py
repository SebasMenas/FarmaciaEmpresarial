from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Cita(Base):
    __tablename__ = "citas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, index=True)
    asunto: Mapped[str] = mapped_column(String(200))
    estado: Mapped[int] = mapped_column(Integer, default=1) # 0=cancelada, 1=activa, 2=ausente, 3=concluida

    # Claves Foráneas (Restricción de Integridad)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    docente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)

    # Relaciones inversas
    paciente: Mapped["Usuario"] = relationship(
        "Usuario", 
        foreign_keys=[usuario_id], 
        back_populates="citas_como_paciente"
    )
    docente: Mapped["Usuario"] = relationship(
        "Usuario", 
        foreign_keys=[docente_id], 
        back_populates="citas_como_doctor"
    )