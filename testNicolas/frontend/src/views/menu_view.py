from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton
from forms.form_docente_view import FormularioDocenteView
from forms.form_paciente_view import FormularioPacienteView
from views.lista_docentes_view import ListaDocentesView
from views.calendario_view import CalendarioView
from views.dialogo_password import DialogoCambiarPassword 

class VentanaPrincipal(QMainWindow):
    def __init__(self, info_usuario, token):
        super().__init__()
        self.usuario = info_usuario
        self.token = token 
        
        print(f"DEBUG: Datos del usuario recibidos: {self.usuario}")

        self.setWindowTitle(f"CESFAM - {self.usuario['nombre']} ({self.usuario['rol']})")
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        rol_normalizado = str(self.usuario.get("rol", "")).strip().upper()
        
        # --- CASO 1: ADMIN ---
        if rol_normalizado == "ADMIN":
            self.form_docente   = FormularioDocenteView(self.token)
            self.lista_docentes = ListaDocentesView(self.token) 
            self.vista_calendario = CalendarioView(self.token, rol_normalizado)

            layout.addWidget(self.form_docente)
            layout.addWidget(self.lista_docentes) 
            layout.addWidget(self.vista_calendario)

        # --- CASO 2: DOCTOR ---
        elif rol_normalizado == "DOCTOR":
            layout_doctor = QHBoxLayout()
    
            self.form_paciente = FormularioPacienteView(self.token)
            self.vista_calendario = CalendarioView(self.token, rol_normalizado)
            
            layout_doctor.addWidget(self.form_paciente, 1)
            layout_doctor.addWidget(self.vista_calendario, 2)
            
            layout.addLayout(layout_doctor)
            
        # --- CASO 3: PACIENTE ---
        elif rol_normalizado == "PACIENTE":
            layout_paciente = QVBoxLayout()
            header_layout = QHBoxLayout()
            
            apellidos = self.usuario.get('apellidos', '')
            titulo = QLabel(f"Bienvenido/a, {self.usuario['nombre']} {apellidos}")
            titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86C1;")
            
            btn_pwd = QPushButton("Cambiar contraseña")
            btn_pwd.setFixedWidth(150)
            btn_pwd.clicked.connect(self.abrir_cambio_password)
            
            """El paciente usa el mismo CalendarioView, pero con su rol
            esto hará que el Backend solo le devuelva sus citas"""
            self.vista_calendario = CalendarioView(self.token, rol_normalizado)
            
            header_layout.addWidget(titulo)
            header_layout.addStretch()
            header_layout.addWidget(btn_pwd)
            
            layout_paciente.addLayout(header_layout)
            layout_paciente.addWidget(self.vista_calendario)
            
            layout.addLayout(layout_paciente)

        self.setCentralWidget(central_widget)
    
    # POP-UP
    def abrir_cambio_password(self):
        dialogo = DialogoCambiarPassword(self.token, self)
        dialogo.exec() # Pausa la ventana principal hasta que se cierre el popup