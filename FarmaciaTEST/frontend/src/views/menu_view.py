from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget, QStackedWidget
from PySide6.QtCore import Qt
from api.cliente_auth import ClienteAuth

class VentanaPrincipal(QMainWindow):
    def __init__(self, username: str, rol: str):
        super().__init__()
        self.setWindowTitle(f"Farmacias Sol - Módulo: {rol}")
        self.setMinimumSize(800, 600)
        self.inicializar_ui(username, rol)

    def inicializar_ui(self, username: str, rol: str):
        layout_principal = QVBoxLayout()
        
        # Cabecera global
        lbl_info = QLabel(f"Usuario: {username} | Rol: {rol}")
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.clicked.connect(self.procesar_logout)
        
        # Enrutador visual
        self.stack_vistas = QStackedWidget()
        self.configurar_vistas_por_rol(rol)
        
        layout_principal.addWidget(lbl_info)
        layout_principal.addWidget(self.btn_logout)
        layout_principal.addWidget(self.stack_vistas)
        
        contenedor = QWidget()
        contenedor.setLayout(layout_principal)
        self.setCentralWidget(contenedor)

    def configurar_vistas_por_rol(self, rol: str):
        """Funcion para inyeccion futuras de vistas reales"""
        if rol == "ADMIN":
            vista_admin = QLabel("Renderizando Pantalla Admin (Gestión de Personal/Inventario)")
            self.stack_vistas.addWidget(vista_admin)
        elif rol == "AUX_MAYOR":
            vista_aux_mayor = QLabel("Renderizando Pantalla Auxiliar Mayor (Almacenamiento Ambiental)")
            self.stack_vistas.addWidget(vista_aux_mayor)
        elif rol == "AUX_DIPLOMADO":
            vista_aux_dip = QLabel("Renderizando Pantalla Auxiliar Diplomado (Manufactura Magistral)")
            self.stack_vistas.addWidget(vista_aux_dip)
        elif rol == "TECNICO":
            vista_tecnico = QLabel("Renderizando Pantalla Técnico (Venta POS)")
            self.stack_vistas.addWidget(vista_tecnico)

    def procesar_logout(self):
        ClienteAuth.cerrar_sesion()
        from views.login_view import LoginWindow
        self.ventana_login = LoginWindow()
        self.ventana_login.show()
        self.close()