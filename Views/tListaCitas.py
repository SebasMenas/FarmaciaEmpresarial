from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout,  QWidget)

class ListaCitasWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Fecha", "Hora", "Usuario ID", "Docente", "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.tabla)
        self.actualizar_tabla()

    def actualizar_tabla(self):
        from localDb import obtener_todas_citas
        citas = obtener_todas_citas()

        self.tabla.setRowCount(len(citas))

        for i, c in enumerate(citas):
            # Formato de fecha y hora
            fecha_str = c.fecha.strftime("%d/%m/%Y")
            hora_str = c.fecha.strftime("%H:%M")

            # Traducir estado
            estado_map = {
                0: "Cancelada",
                1: "Activa",
                2: "Ausente",
                3: "Concluida"
            }

            self.tabla.setItem(i, 0, QTableWidgetItem(str(c.id)))
            self.tabla.setItem(i, 1, QTableWidgetItem(fecha_str))
            self.tabla.setItem(i, 2, QTableWidgetItem(hora_str))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(c.usuario_id)))
            self.tabla.setItem(i, 4, QTableWidgetItem(str(c.docente)))
            self.tabla.setItem(i, 5, QTableWidgetItem(estado_map.get(c.estado, "Desconocido")))