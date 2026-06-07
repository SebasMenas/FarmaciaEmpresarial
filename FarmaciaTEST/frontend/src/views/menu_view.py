from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget
from PySide6.QtCore import Qt
from api.cliente_auth import ClienteAuth

class VentanaPrincipal(QMainWindow):
    def __init__(self, username: str, rol: str):
        super().__init__()
        self.setWindowTitle(f"Panel Principal - Nivel: {rol}")
        self.setFixedSize(400, 300)
        self.inicializar_ui(username, rol)

    def inicializar_ui(self, username: str, rol: str):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_info = QLabel(f"Sesión Activa: {username}\nJerarquía: {rol}")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.clicked.connect(self.procesar_logout)
        
        layout.addWidget(lbl_info)
        layout.addWidget(self.btn_logout)
        
        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

    def procesar_logout(self):

        ClienteAuth.cerrar_sesion()

        # Importación diferida para prevenir ImportError cíclico
        from views.login_view import LoginWindow

        # Instanciación de la vista de autenticación y destrucción de la vista actual
        self.ventana_login = LoginWindow()
        self.ventana_login.show()
        self.close()