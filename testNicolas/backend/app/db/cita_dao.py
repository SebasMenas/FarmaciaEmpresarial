from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cita import Cita
from app.schemas.cita import CitaCreate
from datetime import date, timedelta

class CitaDAO:
    def __init__(self, db: Session):
        self.db = db

    def crear_cita(self, cita_in: CitaCreate, usuario_id: int, rol_usuario: str):
        """Validación de Identidad: Si el usuario es DOCTOR, solo puede agendar para sí mismo"""
        if rol_usuario == "DOCTOR" and cita_in.docente_id != usuario_id:
            raise ValueError("No tienes permiso para agendar citas a nombre de otro doctor.")
        
        margen = timedelta(minutes=30)
        inicio_rango = cita_in.fecha_hora - margen
        fin_rango = cita_in.fecha_hora + margen

        # Busca si el doctor tiene cualquier cita en ese rango
        tope_horario = self.db.query(Cita).filter(
            Cita.docente_id == cita_in.docente_id,
            Cita.fecha_hora > inicio_rango,
            Cita.fecha_hora < fin_rango,
            Cita.estado == 1
        ).first()

        if tope_horario:
            hora_conflicto = tope_horario.fecha_hora.strftime('%H:%M')
            raise ValueError(f"Conflicto: El doctor ya tiene una cita cercana ({hora_conflicto}). Debe haber un margen de 30 min.")

        id_final_paciente = cita_in.paciente_id if cita_in.paciente_id else usuario_id

        nueva_cita = Cita(
            fecha_hora=cita_in.fecha_hora, 
            asunto=cita_in.asunto,
            docente_id=cita_in.docente_id,
            usuario_id=id_final_paciente,
            estado=1
        )
        self.db.add(nueva_cita)
        self.db.commit()
        self.db.refresh(nueva_cita)
        return nueva_cita

    def cancelar_cita(self, cita_id: int):
        cita = self.db.query(Cita).filter(Cita.id == cita_id).first()
        if not cita:
            raise ValueError("La cita no existe.")
        
        cita.estado = 0 
        self.db.commit()
        return True

    def obtener_citas_por_fecha(self, fecha: date, docente_id: int = None):
        query = self.db.query(Cita).filter(
            func.date(Cita.fecha_hora) == fecha,
            Cita.estado == 1  # Solo muestra citas activas
        )
        if docente_id:
            query = query.filter(Cita.docente_id == docente_id)
        return query.all()
    
    def obtener_citas_por_paciente(self, fecha: date, paciente_id: int):
        """Filtra para que el paciente solo vea lo que le corresponde"""
        return self.db.query(Cita).filter(
            func.date(Cita.fecha_hora) == fecha,
            Cita.usuario_id == paciente_id, # Filtro por el ID del paciente logueado
            Cita.estado == 1
        ).all()