from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
)


class RegistroEmpleadoView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registrar Empleado")
        self.resize(400, 550)

        layout = QVBoxLayout()

        # Usuario
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Nombre de usuario")

        # Contraseña
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)

        # Nombre
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre")

        # Apellidos
        self.input_apellidos = QLineEdit()
        self.input_apellidos.setPlaceholderText("Apellidos")

        # RUT
        self.input_rut = QLineEdit()
        self.input_rut.setPlaceholderText("12.345.678-9")

        # Rol
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems([
            "ADMIN",
            "AUXILIAR_DIPLOMADO_MAYOR",
            "AUXILIAR_DIPLOMADO",
            "TECNICO_FARMACEUTICO"
        ])

        # Credencial
        self.input_credencial = QLineEdit()
        self.input_credencial.setPlaceholderText("Credencial")

        # Activo
        self.chk_activo = QCheckBox("Empleado activo")
        self.chk_activo.setChecked(True)

        # Botón
        self.btn_registrar = QPushButton("Registrar")

        # Layout
        layout.addWidget(QLabel("Usuario"))
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("Contraseña"))
        layout.addWidget(self.input_password)

        layout.addWidget(QLabel("Nombre"))
        layout.addWidget(self.input_nombre)

        layout.addWidget(QLabel("Apellidos"))
        layout.addWidget(self.input_apellidos)

        layout.addWidget(QLabel("RUT"))
        layout.addWidget(self.input_rut)

        layout.addWidget(QLabel("Rol"))
        layout.addWidget(self.cmb_rol)

        layout.addWidget(QLabel("Credencial"))
        layout.addWidget(self.input_credencial)

        layout.addWidget(self.chk_activo)

        layout.addStretch()

        layout.addWidget(self.btn_registrar)

        self.setLayout(layout)