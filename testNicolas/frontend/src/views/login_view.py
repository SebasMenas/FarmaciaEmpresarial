from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox
from PySide6.QtCore import Qt
from api.cliente_auth import ClienteAuth 
from views.menu_view import VentanaPrincipal

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso al Sistema - CESFAM")
        self.setFixedSize(350, 250)
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout()
        self.txt_usuario = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_login = QPushButton("Entrar")
        
        layout.addWidget(self.txt_usuario)
        layout.addWidget(self.txt_password)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)
        
        self.btn_login.clicked.connect(self.procesar_login)

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()

        # Llamada al servicio en la carpeta api
        resultado = ClienteAuth.iniciar_sesion(usuario, password)

        if resultado.get("exito"):
            datos_reales = resultado["datos"]
            
            self.main_window = VentanaPrincipal(datos_reales["usuario"], datos_reales["access_token"])
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Error", resultado.get("error", "Fallo de conexión"))