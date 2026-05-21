from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PySide6.QtCore import Qt

# Importacion de Vistas(Views)
from Views import ListaDocentesWidget,ListaCitasWidget # Importación lista docentes


# Importación de Formularios(Forms) 
from Forms import FormularioDocente,FormularioCita, FormularioUser

class VentanaPrincipal(QMainWindow):
    def __init__(self, usuario_activo):
        super().__init__()
        self.usuario = usuario_activo
        self.setWindowTitle(f"Sistema de Gestión de Citas - {self.usuario.nombre} ({self.usuario.rol})")
        self.setMinimumSize(800, 600)

        # Widget central y layout principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Sidebar
        self.sidebar = QVBoxLayout()
        self.sidebar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.sidebar, 1) # Proporción 1

        # area de contenido dinamico
        self.content_area = QStackedWidget()
        self.main_layout.addWidget(self.content_area, 4)

        self.inicializar_paginas()
        self.inicializar_menu()

    def inicializar_paginas(self):
        
        num = 0
        if self.usuario.rol.upper() == "PACIENTE":
            num = 3
        
        # Índice 0: Pantalla de Inicio
        self.pag_inicio = QLabel(f"Bienvenido(a), {self.usuario.nombre} {self.usuario.apellidos}.\n\nSeleccione una opción en el menú lateral.")
        self.pag_inicio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pag_inicio.setStyleSheet("font-size: 18px; color: #00FF00;")
        self.content_area.addWidget(self.pag_inicio)

        # Índice 1: Formulario de Registro de Docentes
        self.form_docente = FormularioDocente()
        self.content_area.addWidget(self.form_docente)

        # Índice 2: Formulario de Agendamiento de Citas
        self.form_cita = FormularioCita(num)
        self.content_area.addWidget(self.form_cita)

        # Índice 3: Nueva vista de lista de docentes
        self.lista_docentes = ListaDocentesWidget()
        self.content_area.addWidget(self.lista_docentes)
        
        # Indice 4: Formulario Agregar Usuario
        self.form_usr = FormularioUser()
        self.content_area.addWidget(self.form_usr)

        # Indice 5: Vista para ver las citas
        self.view_cita = ListaCitasWidget()
        self.content_area.addWidget(self.view_cita)
        
        # Indice 6: Ver Solicitudes
        #self.view_soli =

        # Indice 

    
    def inicializar_menu(self):
        lbl_menu = QLabel("MENÚ PRINCIPAL")
        lbl_menu.setStyleSheet("font-weight: bold; font-size: 14px; padding-bottom: 10px;")
        self.sidebar.addWidget(lbl_menu)

        # Boton general para todos los roles
        btn_inicio = QPushButton("Inicio")
        btn_inicio.clicked.connect(lambda: self.content_area.setCurrentIndex(0))
        self.sidebar.addWidget(btn_inicio)

        # Logica de distribución de opciones según el ROL
        rol = self.usuario.rol.upper()

        if rol == "ADMIN":
            btn_add_docente = QPushButton("Registrar Docente")
            btn_add_docente.clicked.connect(lambda: self.content_area.setCurrentIndex(1))
            self.sidebar.addWidget(btn_add_docente)

            btn_agendar = QPushButton("Agendar Cita")
            btn_agendar.clicked.connect(lambda: self.content_area.setCurrentIndex(2))
            self.sidebar.addWidget(btn_agendar)

            btn_ver_docentes = QPushButton("Ver Docentes")
            btn_ver_docentes.clicked.connect(self.cambiar_a_lista_docentes)
            self.sidebar.addWidget(btn_ver_docentes)

            btn_AgUsr = QPushButton("Agregar Usuario")
            btn_AgUsr.clicked.connect(lambda: self.content_area.setCurrentIndex(4))
            self.sidebar.addWidget(btn_AgUsr)

            btn_citas = QPushButton("Ver Citas")
            btn_citas.clicked.connect(self.cambiar_a_lista_citas)
            self.sidebar.addWidget(btn_citas)
            

        elif rol == "PACIENTE":
            btn_agendar = QPushButton("Agendar Cita")
            btn_agendar.clicked.connect(lambda: self.content_area.setCurrentIndex(2))
            self.sidebar.addWidget(btn_agendar)

        elif rol in ["DOCENTE", "DOCTOR"]:
            lbl_info = QLabel("\n(Módulo de revisión de agenda\nen construcción)")
            lbl_info.setStyleSheet("color: gray; font-size: 11px;")
            self.sidebar.addWidget(lbl_info)

        self.sidebar.addStretch()

    def cambiar_a_lista_docentes(self):
        self.lista_docentes.actualizar_tabla()
        self.content_area.setCurrentIndex(3)

    def cambiar_a_lista_citas(self):
        self.view_cita.actualizar_tabla()
        self.content_area.setCurrentIndex(5)