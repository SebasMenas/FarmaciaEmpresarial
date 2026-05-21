from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QFormLayout,
    QMessageBox, QComboBox, QDateEdit, QTimeEdit, QSpinBox
)
from PySide6.QtCore import QDate
from localDb import sqlite3


class FormularioCita(QWidget):
    def __init__(self, _t):
        super().__init__()
        self.setWindowTitle("Registro de Nueva Cita")
        self.setFixedSize(400, 300)
        self.inicializar_ui(_t)

    def inicializar_ui(self,_tipoU):
        layout = QFormLayout()

        # 🔹 Campos
        self.spn_usuario_id = QSpinBox()
        self.spn_usuario_id.setMinimum(1)
        self.spn_usuario_id.setMaximum(9999)

        self.txt_docente = QLineEdit()
        self.txt_asunto = QLineEdit()

        self.date_fecha = QDateEdit()
        self.date_fecha.setDate(QDate.currentDate())

        self.time_hora = QTimeEdit()
        self.time_hora.setDisplayFormat("HH:mm")

        self.cbx_estado = QComboBox()
        self.cbx_estado.addItems(["Activa", "Cancelada", "Ausente", "Concluida"])

        # 🔹 Agregar al layout
        if not(_tipoU == 3):
            layout.addRow("ID Usuario:", self.spn_usuario_id)
        layout.addRow("Docente:", self.txt_docente)
        layout.addRow("Asunto:", self.txt_asunto)
        layout.addRow("Fecha:", self.date_fecha)
        layout.addRow("Hora:", self.time_hora)
        layout.addRow("Estado:", self.cbx_estado)

        # 🔹 Botón
        self.btn_guardar = QPushButton("Registrar Cita")
        self.btn_guardar.clicked.connect(self.guardar_cita)
        layout.addRow(self.btn_guardar)

        self.setLayout(layout)

    def guardar_cita(self):
        # 🔹 Obtener datos
        usuario_id = self.spn_usuario_id.value()
        docente = self.txt_docente.text().strip()
        asunto = self.txt_asunto.text().strip()
        fecha = self.date_fecha.date()
        hora = self.time_hora.time()

        # 🔹 Mapear estado
        estado_map = {
            "Cancelada": 0,
            "Activa": 1,
            "Ausente": 2,
            "Concluida": 3
        }
        estado = estado_map[self.cbx_estado.currentText()]

        # 🔴 Validación
        if not docente or not asunto:
            QMessageBox.warning(self, "Error", "Docente y Asunto son obligatorios.")
            return

        try:
            conn = sqlite3.connect("sistema_citas.db")
            cursor = conn.cursor()

            cursor.execute('''INSERT INTO citas 
                (anio, mes, dia, hora, minutos, usuario_id, docente, asunto, estado)
                VALUES (?,?,?,?,?,?,?,?,?)''',
                (
                    fecha.year(),
                    fecha.month(),
                    fecha.day(),
                    hora.hour(),
                    hora.minute(),
                    usuario_id,
                    docente,
                    asunto,
                    estado
                )
            )

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", "Cita registrada correctamente.")
            self.limpiar_campos()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de base de datos: {e}")

    def limpiar_campos(self):
        self.txt_docente.clear()
        self.txt_asunto.clear()
        self.spn_usuario_id.setValue(1)
        self.date_fecha.setDate(QDate.currentDate())