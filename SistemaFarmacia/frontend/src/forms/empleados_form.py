from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QMessageBox,
)
from api.cliente_auth import ClienteAuth


class RegistroEmpleadoView(QWidget):
    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
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
        self.cmb_rol.addItem("Administrador", "ADMIN")
        self.cmb_rol.addItem("Auxiliar Diplomado Mayor", "AUX_MAYOR")
        self.cmb_rol.addItem("Auxiliar Diplomado", "AUX_DIPLOMADO")
        self.cmb_rol.addItem("Técnico Farmacéutico", "TECNICO")

        # Credencial
        self.input_credencial = QLineEdit()
        self.input_credencial.setPlaceholderText("Credencial / PIN")

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

        # Evento
        self.btn_registrar.clicked.connect(self.registrar_empleado)

    def registrar_empleado(self):
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()
        nombre = self.input_nombre.text().strip()
        apellidos = self.input_apellidos.text().strip()
        rut = self.input_rut.text().strip()
        rol = self.cmb_rol.currentData()
        credencial = self.input_credencial.text().strip() or None
        activo = self.chk_activo.isChecked()

        if not username or not password or not nombre or not apellidos or not rut:
            QMessageBox.warning(self, "Validación", "Debe completar todos los campos obligatorios.")
            return

        exito, resultado = ClienteAuth.registrar_empleado(
            username=username,
            password=password,
            nombre=nombre,
            apellidos=apellidos,
            rut=rut,
            rol=rol,
            credencial=credencial,
            activo=activo
        )

        if exito:
            QMessageBox.information(self, "Éxito", "Empleado registrado correctamente.")
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el empleado:\n{resultado}")