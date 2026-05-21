class Cita:
    _contador_id = 1  # variable de clase para autoincremento

    def __init__(self, anio, mes, dia, usuario_id, docente, asunto):
        # Validar asunto
        if len(asunto) > 200:
            raise ValueError("El asunto no puede superar los 200 caracteres")

        # Validación simple de fecha
        if not (1 <= mes <= 12):
            raise ValueError("Mes inválido")
        if not (1 <= dia <= 31):
            raise ValueError("Día inválido")

        self.id = Cita._contador_id
        Cita._contador_id += 1

        self.anio = anio
        self.mes = mes
        self.dia = dia
        self.usuario_id = usuario_id
        self.docente = docente
        self.asunto = asunto

    def __repr__(self):
        return (f"Cita(id={self.id}, fecha={self.dia}/{self.mes}/{self.anio}, "
                f"usuario={self.usuario_id}, docente='{self.docente}', asunto='{self.asunto}')")


# Lista donde se almacenan las citas
lista_citas = []


# Función para agregar citas a la lista
def agregar_cita(lista, anio, mes, dia, usuario_id, docente, asunto):
    cita = Cita(anio, mes, dia, usuario_id, docente, asunto)
    lista.append(cita)
    return cita


# Ejemplo de uso
c1 = agregar_cita(lista_citas, 2026, 4, 11, 101, "Dr. Pérez", "Consulta general")
c2 = agregar_cita(lista_citas, 2026, 4, 12, 102, "Dra. López", "Revisión médica")

print(lista_citas)