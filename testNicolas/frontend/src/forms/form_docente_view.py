from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QMessageBox)
from api.cliente_usuarios import ClienteUsuarios

class FormularioDocenteView(QWidget):
    def __init__(self, token_activo):
        super().__init__()
        self.token = token_activo
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.txt_username = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_apellidos = QLineEdit()
        self.txt_rut = QLineEdit()
        self.txt_sexo = QLineEdit()

        form_layout.addRow("Usuario:", self.txt_username)
        form_layout.addRow("Contraseña:", self.txt_password)
        form_layout.addRow("Nombre:", self.txt_nombre)
        form_layout.addRow("Apellidos:", self.txt_apellidos)
        form_layout.addRow("RUT:", self.txt_rut)
        form_layout.addRow("Sexo:", self.txt_sexo)

        self.btn_guardar = QPushButton("Registrar Doctor")
        self.btn_guardar.clicked.connect(self.procesar_registro)

        layout.addLayout(form_layout)
        layout.addWidget(self.btn_guardar)
        self.setLayout(layout)

    def procesar_registro(self):
        # Empaquetar los datos tal como los espera FastAPI (Schema UsuarioCreate)
        datos = {
            "username": self.txt_username.text().strip(),
            "password": self.txt_password.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "apellidos": self.txt_apellidos.text().strip(),
            "rut": self.txt_rut.text().strip(),
            "sexo": self.txt_sexo.text().strip(),
            "rol": "DOCTOR" # Forzamos el rol desde este formulario
        }

        resultado = ClienteUsuarios.registrar_usuario(self.token, datos)

        if resultado["exito"]:
            QMessageBox.information(self, "Éxito", "Doctor registrado correctamente en la base de datos.")
        else:
            QMessageBox.critical(self, "Error", resultado["error"])