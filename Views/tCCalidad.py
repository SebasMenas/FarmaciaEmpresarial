from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView,
    QPushButton, QMessageBox, QLabel
)
from PySide6.QtGui import QColor
from datetime import datetime


class ControlCalidadLotesWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titulo = QLabel("Control de Calidad de Lotes")
        layout.addWidget(titulo)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Producto",
            "Lote",
            "Fecha Importación",
            "Fecha Vencimiento",
            "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.tabla)

        # Botón notificación
        self.btn_alerta = QPushButton("Enviar alerta")
        self.btn_alerta.clicked.connect(self.enviar_alerta)
        layout.addWidget(self.btn_alerta)

        self.actualizar_tabla()


    def actualizar_tabla(self):
        """
        Consulta la BD y llena tabla
        """

        from localDb import obtener_todos_lotes

        lotes = obtener_todos_lotes()

        hoy = datetime.today()

        datos = []

        # analizar vencimientos
        for lote in lotes:
            fecha_v = datetime.strptime(
                lote.fecha_vencimiento,
                "%Y-%m-%d"
            )

            dias = (fecha_v - hoy).days

            if dias <= 0:
                estado = "VENCIDO"
                prioridad = 0
            elif dias <= 30:
                estado = "POR VENCER"
                prioridad = 1
            else:
                estado = "OK"
                prioridad = 2

            datos.append({
                "obj": lote,
                "estado": estado,
                "prioridad": prioridad
            })

        # ordenar: primero urgentes
        datos.sort(key=lambda x: x["prioridad"])

        self.tabla.setRowCount(len(datos))

        for fila, d in enumerate(datos):
            lote = d["obj"]

            self.tabla.setItem(
                fila, 0,
                QTableWidgetItem(str(lote.id))
            )

            self.tabla.setItem(
                fila, 1,
                QTableWidgetItem(lote.producto)
            )

            self.tabla.setItem(
                fila, 2,
                QTableWidgetItem(lote.numero_lote)
            )

            self.tabla.setItem(
                fila, 3,
                QTableWidgetItem(lote.fecha_importacion)
            )

            self.tabla.setItem(
                fila, 4,
                QTableWidgetItem(lote.fecha_vencimiento)
            )

            estado_item = QTableWidgetItem(d["estado"])

            # colores
            if d["estado"] == "VENCIDO":
                estado_item.setBackground(QColor("red"))

            elif d["estado"] == "POR VENCER":
                estado_item.setBackground(QColor("yellow"))

            else:
                estado_item.setBackground(QColor("lightgreen"))

            self.tabla.setItem(fila, 5, estado_item)


    def enviar_alerta(self):
        """
        Guarda alerta en tabla notificaciones
        """

        fila = self.tabla.currentRow()

        if fila == -1:
            QMessageBox.warning(
                self,
                "Error",
                "Seleccione un lote"
            )
            return

        id_lote = self.tabla.item(fila, 0).text()
        producto = self.tabla.item(fila, 1).text()
        estado = self.tabla.item(fila, 5).text()

        mensaje = f"Alerta: lote {id_lote} ({producto}) está {estado}"

        from localDb import insertar_notificacion
        insertar_notificacion(mensaje)

        QMessageBox.information(
            self,
            "Éxito",
            "Notificación enviada"
        )