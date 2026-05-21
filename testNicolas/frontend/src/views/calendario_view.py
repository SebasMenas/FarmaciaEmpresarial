from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QCalendarWidget, 
                               QTableWidget, QTableWidgetItem, QLabel, QPushButton, 
                               QComboBox, QLineEdit, QTimeEdit, QMessageBox, QGroupBox, QHeaderView)
from PySide6.QtCore import QTime
from api.cliente_citas import ClienteCitas
from api.cliente_usuarios import ClienteUsuarios

class CalendarioView(QWidget):
    def __init__(self, token, rol_usuario=""):
        super().__init__()
        self.token = token
        self.rol = rol_usuario.strip().upper()
        
        self.doctores_ids = [] 
        self.pacientes_ids = []
        
        self.inicializar_ui()

        # Carga de datos inicial
        if self.rol == "DOCTOR":
            self.cargar_doctores_en_combobox()
            self.cargar_pacientes_en_combobox()

    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self)

        # ==========================================
        # PANEL IZQUIERDO: Calendario y Tabla
        # ==========================================
        panel_izquierdo = QVBoxLayout()
        
        self.calendario = QCalendarWidget()
        self.calendario.setGridVisible(True)
        self.calendario.clicked.connect(self.actualizar_tabla_citas) 

        self.lbl_fecha = QLabel("Citas para el día seleccionado:")
        self.lbl_fecha.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5) # Añadimos columna para "Acción"
        self.tabla.setHorizontalHeaderLabels(["Hora", "Asunto", "Doctor", "Paciente", "Acción"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        panel_izquierdo.addWidget(self.calendario)
        panel_izquierdo.addWidget(self.lbl_fecha)
        panel_izquierdo.addWidget(self.tabla)

        layout_principal.addLayout(panel_izquierdo, 2)

        # ==========================================
        # PANEL DERECHO: Formulario (Doctor/Paciente)
        # ==========================================
        if self.rol != "ADMIN" and self.rol != "PACIENTE":
            panel_derecho = QVBoxLayout()
            grupo_agendar = QGroupBox("Agendar Nueva Cita")
            layout_form = QVBoxLayout(grupo_agendar)

            # Selector de Doctor
            layout_form.addWidget(QLabel("Doctor:"))
            self.cmb_doctores = QComboBox()
            layout_form.addWidget(self.cmb_doctores)

            # Selector de Paciente
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
            self.btn_agendar.setStyleSheet("background-color: #2E86C1; color: white; padding: 5px; font-weight: bold;")
            self.btn_agendar.clicked.connect(self.procesar_agendamiento)
            layout_form.addWidget(self.btn_agendar)

            layout_form.addStretch() 
            panel_derecho.addWidget(grupo_agendar)
            layout_principal.addLayout(panel_derecho, 1)
        
        elif self.rol == "PACIENTE":
            panel_info = QVBoxLayout()
            lbl_info = QLabel("Seleccione una fecha para revisar sus citas programadas.")
            lbl_info.setWordWrap(True)
            panel_info.addWidget(lbl_info)
            panel_info.addStretch()
            layout_principal.addLayout(panel_info, 1)
        
        else:
            panel_derecho = QVBoxLayout()
            info_admin = QLabel("Modo Supervisor\n\nSolo lectura de citas.")
            info_admin.setStyleSheet("color: gray; font-size: 14px; font-style: italic;")
            panel_derecho.addWidget(info_admin)
            panel_derecho.addStretch()
            layout_principal.addLayout(panel_derecho, 1)

        self.actualizar_tabla_citas(self.calendario.selectedDate())

    # --- LÓGICA DE DATOS ---

    def cargar_doctores_en_combobox(self):
        res = ClienteUsuarios.obtener_doctores(self.token)
        if res["exito"]:
            for doc in res["datos"]:
                self.cmb_doctores.addItem(f"Dr/a. {doc['nombre']} {doc['apellidos']}")
                self.doctores_ids.append(doc["id"])

    def cargar_pacientes_en_combobox(self):
        """Carga la lista de pacientes registrados"""
        res = ClienteUsuarios.obtener_pacientes(self.token)
        if res["exito"]:
            self.cmb_pacientes.clear()
            self.pacientes_ids = []
            for pac in res["datos"]:
                self.cmb_pacientes.addItem(f"{pac['nombre']} {pac['apellidos']}")
                self.pacientes_ids.append(pac["id"])

    def actualizar_tabla_citas(self, qdate):
        fecha_str = qdate.toString("yyyy-MM-dd")
        self.lbl_fecha.setText(f"Citas para el {fecha_str}:")
        
        res = ClienteCitas.obtener_citas_por_dia(self.token, fecha_str)
        if res["exito"]:
            citas = res["datos"]
            self.tabla.setRowCount(len(citas))
            
            # Ajustamos las columnas según el rol
            if self.rol == "PACIENTE":
                self.tabla.setColumnCount(2)
                self.tabla.setHorizontalHeaderLabels(["Hora", "Asunto"])
            else:
                self.tabla.setColumnCount(5)
                self.tabla.setHorizontalHeaderLabels(["Hora", "Asunto", "Doctor", "Paciente", "Acción"])

            for i, cita in enumerate(citas):
                hora = cita["fecha_hora"].split("T")[1][:5]
                self.tabla.setItem(i, 0, QTableWidgetItem(hora))
                self.tabla.setItem(i, 1, QTableWidgetItem(cita["asunto"]))
            
                if self.rol != "PACIENTE":
                    self.tabla.setItem(i, 2, QTableWidgetItem(f"ID: {cita['docente_id']}"))
                    self.tabla.setItem(i, 3, QTableWidgetItem(f"ID: {cita['usuario_id']}"))
                    
                    btn_cancelar = QPushButton("Cancelar")
                    btn_cancelar.setStyleSheet("background-color: #C0392B; color: white; border-radius: 3px;")
                    btn_cancelar.clicked.connect(lambda checked=False, id_c=cita["id"]: self.cancelar_cita(id_c))
                    self.tabla.setCellWidget(i, 4, btn_cancelar)
        else:
            self.tabla.setRowCount(0)

    def cancelar_cita(self, id_cita):
        confirmacion = QMessageBox.question(self, "Confirmar", "¿Seguro que desea cancelar esta cita?",
                                           QMessageBox.Yes | QMessageBox.No)
        if confirmacion == QMessageBox.Yes:
            res = ClienteCitas.cancelar_cita(self.token, id_cita)
            if res["exito"]:
                QMessageBox.information(self, "Éxito", "Cita cancelada correctamente.")
                self.actualizar_tabla_citas(self.calendario.selectedDate())
            else:
                QMessageBox.critical(self, "Error", f"No se pudo cancelar: {res['error']}")

    def procesar_agendamiento(self):
        if self.cmb_doctores.currentIndex() == -1 or self.cmb_pacientes.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Debe seleccionar doctor y paciente.")
            return
            
        fecha_str = self.calendario.selectedDate().toString("yyyy-MM-dd")
        hora_str = self.input_hora.time().toString("HH:mm:ss")
        fecha_hora_iso = f"{fecha_str}T{hora_str}"

        doctor_id = self.doctores_ids[self.cmb_doctores.currentIndex()]
        paciente_id = self.pacientes_ids[self.cmb_pacientes.currentIndex()]

        datos_cita = {
            "fecha_hora": fecha_hora_iso,
            "asunto": self.input_asunto.text().strip(),
            "docente_id": doctor_id,
            "paciente_id": paciente_id
        }

        res = ClienteCitas.agendar_cita(self.token, datos_cita)

        if res["exito"]:
            QMessageBox.information(self, "Éxito", "Cita agendada correctamente.")
            self.input_asunto.clear()
            self.actualizar_tabla_citas(self.calendario.selectedDate())
        else:
            datos_error = res.get("error")
            mensaje_final = "\n".join([e.get('msg') for e in datos_error]) if isinstance(datos_error, list) else str(datos_error)
            QMessageBox.critical(self, "Error al Agendar", mensaje_final)