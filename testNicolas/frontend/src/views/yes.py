from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QCalendarWidget,
    QTableWidget, QTableWidgetItem, QLabel, QPushButton,
    QComboBox, QLineEdit, QTimeEdit, QMessageBox,
    QGroupBox, QHeaderView
)
from PySide6.QtCore import QTime


class CalendarioView(QWidget):
    def __init__(self, token=None, rol_usuario="DOCTOR"):
        super().__init__()

        self.token = token
        self.rol = rol_usuario.strip().upper()

        # -----------------------------
        # DATOS SIMULADOS (sin BD)
        # -----------------------------
        self.doctores = [
            {"id": 1, "nombre": "Juan", "apellidos": "Pérez"},
            {"id": 2, "nombre": "Ana", "apellidos": "Gómez"}
        ]

        self.pacientes = [
            {"id": 1, "nombre": "Carlos", "apellidos": "López"},
            {"id": 2, "nombre": "María", "apellidos": "Torres"}
        ]

        self.citas = []  # aquí se guardan las citas

        self.doctores_ids = []
        self.pacientes_ids = []

        self.inicializar_ui()

        if self.rol == "DOCTOR":
            self.cargar_doctores_en_combobox()
            self.cargar_pacientes_en_combobox()

    # =====================================
    # INTERFAZ
    # =====================================
    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self)

        # -------- PANEL IZQUIERDO ----------
        panel_izquierdo = QVBoxLayout()

        self.calendario = QCalendarWidget()
        self.calendario.setGridVisible(True)
        self.calendario.clicked.connect(self.actualizar_tabla_citas)

        self.lbl_fecha = QLabel("Citas para el día seleccionado:")
        self.lbl_fecha.setStyleSheet(
            "font-weight: bold; font-size: 14px;"
        )

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["Hora", "Asunto", "Doctor", "Paciente", "Acción"]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        panel_izquierdo.addWidget(self.calendario)
        panel_izquierdo.addWidget(self.lbl_fecha)
        panel_izquierdo.addWidget(self.tabla)

        layout_principal.addLayout(panel_izquierdo, 2)

        # -------- PANEL DERECHO ----------
        if self.rol != "ADMIN" and self.rol != "PACIENTE":
            panel_derecho = QVBoxLayout()

            grupo_agendar = QGroupBox("Agendar Nueva Cita")
            layout_form = QVBoxLayout(grupo_agendar)

            layout_form.addWidget(QLabel("Doctor:"))
            self.cmb_doctores = QComboBox()
            layout_form.addWidget(self.cmb_doctores)

            layout_form.addWidget(QLabel("Paciente:"))
            self.cmb_pacientes = QComboBox()
            layout_form.addWidget(self.cmb_pacientes)

            layout_form.addWidget(QLabel("Hora:"))
            self.input_hora = QTimeEdit()
            self.input_hora.setTime(QTime(9, 0))
            layout_form.addWidget(self.input_hora)

            layout_form.addWidget(QLabel("Asunto / Motivo:"))
            self.input_asunto = QLineEdit()
            layout_form.addWidget(self.input_asunto)

            self.btn_agendar = QPushButton("Agendar Cita")
            self.btn_agendar.clicked.connect(
                self.procesar_agendamiento
            )
            layout_form.addWidget(self.btn_agendar)

            panel_derecho.addWidget(grupo_agendar)
            layout_principal.addLayout(panel_derecho, 1)

        self.actualizar_tabla_citas(
            self.calendario.selectedDate()
        )

    # =====================================
    # CARGA DE DATOS
    # =====================================
    def cargar_doctores_en_combobox(self):
        self.cmb_doctores.clear()
        self.doctores_ids = []

        for doc in self.doctores:
            self.cmb_doctores.addItem(
                f"Dr/a. {doc['nombre']} {doc['apellidos']}"
            )
            self.doctores_ids.append(doc["id"])

    def cargar_pacientes_en_combobox(self):
        self.cmb_pacientes.clear()
        self.pacientes_ids = []

        for pac in self.pacientes:
            self.cmb_pacientes.addItem(
                f"{pac['nombre']} {pac['apellidos']}"
            )
            self.pacientes_ids.append(pac["id"])

    # =====================================
    # MOSTRAR CITAS
    # =====================================
    def actualizar_tabla_citas(self, qdate):
        fecha_str = qdate.toString("yyyy-MM-dd")
        self.lbl_fecha.setText(
            f"Citas para el {fecha_str}:"
        )

        citas_dia = [
            c for c in self.citas
            if c["fecha_hora"].startswith(fecha_str)
        ]

        self.tabla.setRowCount(len(citas_dia))

        for i, cita in enumerate(citas_dia):
            hora = cita["fecha_hora"].split("T")[1][:5]

            self.tabla.setItem(
                i, 0, QTableWidgetItem(hora)
            )

            self.tabla.setItem(
                i, 1, QTableWidgetItem(cita["asunto"])
            )

            self.tabla.setItem(
                i, 2,
                QTableWidgetItem(
                    f"ID: {cita['docente_id']}"
                )
            )

            self.tabla.setItem(
                i, 3,
                QTableWidgetItem(
                    f"ID: {cita['paciente_id']}"
                )
            )

            btn = QPushButton("Cancelar")
            btn.clicked.connect(
                lambda checked=False,
                id_c=cita["id"]:
                self.cancelar_cita(id_c)
            )

            self.tabla.setCellWidget(i, 4, btn)

    # =====================================
    # CANCELAR
    # =====================================
    def cancelar_cita(self, id_cita):
        confirmacion = QMessageBox.question(
            self,
            "Confirmar",
            "¿Cancelar esta cita?"
        )

        if confirmacion == QMessageBox.Yes:
            self.citas = [
                c for c in self.citas
                if c["id"] != id_cita
            ]

            QMessageBox.information(
                self,
                "Éxito",
                "Cita cancelada"
            )

            self.actualizar_tabla_citas(
                self.calendario.selectedDate()
            )

    # =====================================
    # AGENDAR
    # =====================================
    def procesar_agendamiento(self):
        if not self.input_asunto.text().strip():
            QMessageBox.warning(
                self,
                "Error",
                "Ingrese un asunto"
            )
            return

        fecha = self.calendario.selectedDate().toString(
            "yyyy-MM-dd"
        )

        hora = self.input_hora.time().toString(
            "HH:mm:ss"
        )

        nueva_cita = {
            "id": len(self.citas) + 1,
            "fecha_hora": f"{fecha}T{hora}",
            "asunto": self.input_asunto.text(),
            "docente_id":
                self.doctores_ids[
                    self.cmb_doctores.currentIndex()
                ],
            "paciente_id":
                self.pacientes_ids[
                    self.cmb_pacientes.currentIndex()
                ]
        }

        self.citas.append(nueva_cita)

        QMessageBox.information(
            self,
            "Éxito",
            "Cita agendada"
        )

        self.input_asunto.clear()

        self.actualizar_tabla_citas(
            self.calendario.selectedDate()
        )

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    ventana = CalendarioView()
    ventana.resize(900, 500)
    ventana.show()

    sys.exit(app.exec())