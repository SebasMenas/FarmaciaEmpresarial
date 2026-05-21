from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, 
    QLabel, QLineEdit, QMessageBox)

from PySide6.QtCore import Qt

from localDb import validar_credenciales # Importación de la base de datos
# Importación de los formularios desarrollados
from menu import VentanaPrincipal

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Citas - Acceso")
        self.setFixedSize(320, 200)
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout()

        self.lbl_titulo = QLabel("SISTEMA DE GESTIÓN DE CITAS")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.lbl_titulo)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Nombre de usuario")
        layout.addWidget(self.txt_usuario)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_password)

        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.clicked.connect(self.procesar_login)
        layout.addWidget(self.btn_login)
        
        self.txt_usuario.returnPressed.connect(self.procesar_login)
        self.txt_password.returnPressed.connect(self.procesar_login)
        
        self.setLayout(layout)

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()

        if not usuario or not password:
            QMessageBox.warning(self, "Error de validación", "Debe proveer usuario y contraseña.")
            return

        usuario_activo = validar_credenciales(usuario, password)

        if usuario_activo:
            self.main_window = VentanaPrincipal(usuario_activo)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Acceso Denegado", "Las credenciales ingresadas no son válidas.")
            self.txt_password.clear()
