from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QMessageBox
)

from api.AdminConsultas import ClienteMonitoreo


class EditarEmpleadoView(QWidget):

    def __init__(self, empleado):
        super().__init__()

        self.empleado = empleado
        self.id_empleado = empleado["id"]

        self.setWindowTitle("Editar Empleado")
        self.resize(450, 500)

        self.inicializar_ui()
        self.cargar_datos()

    def inicializar_ui(self):

        layout = QVBoxLayout()

        self.input_nombre = QLineEdit()

        self.input_apellidos = QLineEdit()

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems([
            "ADMIN",
            "AUXILIAR_DIPLOMADO_MAYOR",
            "AUXILIAR_DIPLOMADO",
            "TECNICO_FARMACEUTICO"
        ])

        self.input_credencial = QLineEdit()

        self.chk_activo = QCheckBox("Empleado activo")

        self.btn_guardar = QPushButton("Guardar Cambios")

        layout.addWidget(QLabel("Nombre"))
        layout.addWidget(self.input_nombre)

        layout.addWidget(QLabel("Apellidos"))
        layout.addWidget(self.input_apellidos)

        layout.addWidget(QLabel("Rol"))
        layout.addWidget(self.cmb_rol)

        layout.addWidget(QLabel("Credencial"))
        layout.addWidget(self.input_credencial)

        layout.addWidget(self.chk_activo)

        layout.addStretch()

        layout.addWidget(self.btn_guardar)

        self.setLayout(layout)

        self.btn_guardar.clicked.connect(
            self.guardar
        )

    def cargar_datos(self):

        self.input_nombre.setText(
            self.empleado["nombre"]
        )

        self.input_apellidos.setText(
            self.empleado["apellidos"]
        )

        self.cmb_rol.setCurrentText(
            self.empleado["rol"]
        )

        self.input_credencial.setText(
            self.empleado["credencial"]
        )

        #self.chk_activo.setChecked(
        #    self.empleado["activo"]
        #)

    def guardar(self):

        datos = {
            "nombre": self.input_nombre.text(),
            "apellidos": self.input_apellidos.text(),
            "rol": self.cmb_rol.currentText(),
            "credencial": self.input_credencial.text(),
            "activo": self.chk_activo.isChecked()
        }

        ClienteMonitoreo.editar_empleado(
            self.id_empleado,
            datos
        )

        if ClienteMonitoreo.res["exito"]:
            QMessageBox.information(
                self,
                "Éxito",
                "Empleado actualizado."
            )
            self.close()

        else:
            QMessageBox.critical(
                self,
                "Error",
                res["error"]
            )