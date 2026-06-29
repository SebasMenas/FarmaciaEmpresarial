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

    def __init__(self, empleado, callback_exito=None):
        super().__init__()

        self.empleado = empleado
        self.id_empleado = empleado["id"]
        self.callback_exito = callback_exito

        self.setWindowTitle("Editar Empleado")
        self.resize(450, 500)

        self.inicializar_ui()
        self.cargar_datos()

    def inicializar_ui(self):

        layout = QVBoxLayout()

        self.input_nombre = QLineEdit()

        self.input_apellidos = QLineEdit()

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItem("Administrador", "ADMIN")
        self.cmb_rol.addItem("Auxiliar Diplomado Mayor", "AUX_MAYOR")
        self.cmb_rol.addItem("Auxiliar Diplomado", "AUX_DIPLOMADO")
        self.cmb_rol.addItem("Técnico Farmacéutico", "TECNICO")

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
            self.empleado.get("nombre", "")
        )

        self.input_apellidos.setText(
            self.empleado.get("apellidos", "")
        )

        # Selección por el valor del enum (ADMIN, AUX_MAYOR, ...), no por el
        # texto visible del combo, que es una etiqueta distinta en español.
        rol_actual = self.empleado.get("rol", "")
        indice_rol = self.cmb_rol.findData(rol_actual)
        if indice_rol >= 0:
            self.cmb_rol.setCurrentIndex(indice_rol)

        # credencial es opcional en el backend; puede llegar como None
        # (p. ej. un Técnico sin PIN asignado). setText(None) lanza TypeError.
        self.input_credencial.setText(
            self.empleado.get("credencial") or ""
        )

        self.chk_activo.setChecked(
            bool(self.empleado.get("activo", True))
        )

    def guardar(self):

        # Si el campo de credencial queda vacío, se envía None (no "") para
        # que el backend, que usa exclude_none=True, lo trate como "sin
        # cambios" en vez de borrar una credencial ya asignada.
        credencial_texto = self.input_credencial.text().strip()

        datos = {
            "nombre": self.input_nombre.text(),
            "apellidos": self.input_apellidos.text(),
            "rol": self.cmb_rol.currentData(),   # <-- importante
            "credencial": credencial_texto if credencial_texto else None,
            "activo": self.chk_activo.isChecked()
        }

        res = ClienteMonitoreo.editar_empleado(
            self.id_empleado,
            datos
        )

        if res["exito"]:
            QMessageBox.information(
                self,
                "Éxito",
                "Empleado actualizado."
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()

        else:
            QMessageBox.critical(
                self,
                "Error",
                res["error"]
            )