from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                               QLabel, QMessageBox, QGroupBox, QComboBox)
from api.cliente_usuarios import ClienteUsuarios

class FormularioPacienteView(QWidget):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout(self)
        grupo = QGroupBox("Registrar Nuevo Paciente")
        layout_form = QVBoxLayout(grupo)

        self.txt_rut = QLineEdit()
        self.txt_rut.setPlaceholderText("RUT (Ej: 12345678-9)")
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombres")
        
        self.txt_apellidos = QLineEdit()
        self.txt_apellidos.setPlaceholderText("Apellidos")

        self.cmb_sexo = QComboBox()
        self.cmb_sexo.addItems(["MASCULINO", "FEMENINO", "OTRO"])

        # Por defecto, la contraseña será el RUT para que el paciente pueda entrar
        layout_form.addWidget(QLabel("RUT (Usuario):"))
        layout_form.addWidget(self.txt_rut)
        layout_form.addWidget(QLabel("Nombre:"))
        layout_form.addWidget(self.txt_nombre)
        layout_form.addWidget(QLabel("Apellidos:"))
        layout_form.addWidget(self.txt_apellidos)
        layout_form.addWidget(QLabel("Sexo:"))
        layout_form.addWidget(self.cmb_sexo)

        self.btn_registrar = QPushButton("Crear Cuenta de Paciente")
        self.btn_registrar.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 8px;")
        self.btn_registrar.clicked.connect(self.registrar_paciente)
        
        layout_form.addWidget(self.btn_registrar)
        layout.addWidget(grupo)

    def registrar_paciente(self):
        rut = self.txt_rut.text().strip()
        # JSON para el endpoint /usuarios/
        datos = {
            "username": rut,
            "password": rut, # Contraseña inicial = RUT
            "nombre": self.txt_nombre.text().strip(),
            "apellidos": self.txt_apellidos.text().strip(),
            "rut": rut,
            "sexo": self.cmb_sexo.currentText(),
            "rol": "PACIENTE"
        }

        res = ClienteUsuarios.registrar_usuario(self.token, datos)
        if res["exito"]:
            QMessageBox.information(self, "Éxito", f"Paciente {datos['nombre']} registrado.\nSu contraseña es su RUT.")
            self.limpiar_campos()
        else:
            QMessageBox.critical(self, "Error", str(res["error"]))

    def limpiar_campos(self):
        self.txt_rut.clear()
        self.txt_nombre.clear()
        self.txt_apellidos.clear()