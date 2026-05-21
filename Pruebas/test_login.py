import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from test_db import inicializar_db, validar_credenciales

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_ventana()
        self.inicializar_ui()

    def configurar_ventana(self):
        self.setWindowTitle("Control de Citas - Acceso")
        self.setFixedSize(320, 200)

    def inicializar_ui(self):

        layout = QVBoxLayout()

        # Etiqueta de Título
        self.lbl_titulo = QLabel("SISTEMA DE GESTIÓN DE CITAS")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.lbl_titulo)

        # Campo de entrada: Usuario
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Nombre de usuario")
        layout.addWidget(self.txt_usuario)

        # Campo de entrada: Contraseña
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.txt_password)

        # Botón de validación
        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.clicked.connect(self.procesar_login)
        layout.addWidget(self.btn_login)
        self.txt_usuario.returnPressed.connect(self.procesar_login)
        self.txt_password.returnPressed.connect(self.procesar_login)
        
        self.setLayout(layout)

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()

        # Validación de campos vacíos
        if not usuario or not password:
            QMessageBox.warning(self, "Error de validación", "Debe proveer usuario y contraseña.")
            return

        # Llamada a test_db
        usuario_activo = validar_credenciales(usuario, password)

        if usuario_activo:
            # Desempaquetado de informacion de usuario
            
            QMessageBox.information(
                self, 
                "Acceso Concedido", 
                f"Autenticación exitosa.\n\nUsuario: {usuario_activo.nombre} {usuario_activo.apellidos}\nRol: {usuario_activo.rol}"
            )

            self.close()
        else:
            QMessageBox.critical(self, "Acceso Denegado", "Las credenciales ingresadas no son válidas.")
            self.txt_password.clear()

if __name__ == "__main__":
    # Integridad de base de datos
    inicializar_db()

    app = QApplication(sys.argv)
    ventana_login = LoginWindow()
    ventana_login.show()
    sys.exit(app.exec())