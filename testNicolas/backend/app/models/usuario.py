from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    # Mapeo estricto con validación de tipos
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    rut: Mapped[str] = mapped_column(String(12), unique=True)
    sexo: Mapped[str] = mapped_column(String(20))
    rol: Mapped[str] = mapped_column(String(20)) # "ADMIN", "DOCTOR", "PACIENTE"

    # Relaciones direccionales (El string "Cita" evita problemas de importación circular)
    citas_como_paciente: Mapped[list["Cita"]] = relationship(
        "Cita", 
        foreign_keys="[Cita.usuario_id]", 
        back_populates="paciente"
    )
    citas_como_doctor: Mapped[list["Cita"]] = relationship(
        "Cita", 
        foreign_keys="[Cita.docente_id]", 
        back_populates="docente"
    )