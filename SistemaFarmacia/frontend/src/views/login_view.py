from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QMessageBox
from PySide6.QtCore import Qt
from api.cliente_auth import ClienteAuth 
from views.menu_view import VentanaPrincipal

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso al Sistema - Farmacias Sol")
        self.setFixedSize(350, 250)
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Nombre de usuario")
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Contraseña")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.btn_login = QPushButton("Entrar")
        
        layout.addWidget(self.txt_usuario)
        layout.addWidget(self.txt_password)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)
        
        self.btn_login.clicked.connect(self.procesar_login)
        self.txt_usuario.returnPressed.connect(self.procesar_login)
        self.txt_password.returnPressed.connect(self.procesar_login)
  

    def procesar_login(self):
        usuario = self.txt_usuario.text().strip()
        password = self.txt_password.text().strip()

        # Validacion
        if not usuario or not password:
            QMessageBox.warning(self, "Validación", "Debe completar ambos campos para continuar.")
            return

        # Petición HTTP sincrona al backend
        resultado = ClienteAuth.iniciar_sesion(usuario, password)

        if resultado.get("exito"):
            datos_reales = resultado["datos"]
            rol_usuario = datos_reales.get("rol")
            
            # Instanciación de la interfaz principal inyectando el rol para filtrado de vistas
            self.main_window = VentanaPrincipal(usuario, rol_usuario)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.critical(self, "Error de Autenticación", resultado.get("error", "Fallo de conexión"))