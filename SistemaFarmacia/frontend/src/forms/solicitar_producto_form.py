from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDateEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import QDate
from api.AdminConsultas import ClienteMonitoreo


class SolicitarProductoView(QWidget):
    """
    Formulario para que el Admin solicite un producto NUEVO en el catálogo.

    El Admin solo indica el nombre del producto, una cantidad fija de
    ingreso y la fecha de caducidad de ese primer lote. La ficha técnica
    (componente activo, concentración, tipo de producto e indicación
    ambiental) la determina el backend automáticamente, y el laboratorio
    proveedor se asigna reutilizando uno certificado existente: ninguno
    de esos datos los inventa quien solicita el abastecimiento.
    """

    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Solicitar Nuevo Producto")
        self.resize(400, 260)

        layout = QVBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Amoxicilina")

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 100000)
        self.spin_cantidad.setValue(100)

        self.date_caducidad = QDateEdit()
        self.date_caducidad.setCalendarPopup(True)
        self.date_caducidad.setDate(QDate.currentDate().addYears(1))

        form = QFormLayout()
        form.addRow("Nombre del producto", self.input_nombre)
        form.addRow("Cantidad de ingreso", self.spin_cantidad)
        form.addRow("Fecha de caducidad", self.date_caducidad)

        self.lbl_nota = QLabel(
            "La ficha técnica (componente activo, tipo e indicación\n"
            "ambiental) y el laboratorio proveedor se asignan\n"
            "automáticamente al registrar el producto."
        )
        self.lbl_nota.setWordWrap(True)

        self.btn_solicitar = QPushButton("Solicitar Producto")

        layout.addLayout(form)
        layout.addWidget(self.lbl_nota)
        layout.addStretch()
        layout.addWidget(self.btn_solicitar)

        self.setLayout(layout)

        self.btn_solicitar.clicked.connect(self.solicitar_producto)

    def solicitar_producto(self):
        nombre = self.input_nombre.text().strip()
        cantidad_inicial = self.spin_cantidad.value()
        fecha_caducidad = self.date_caducidad.date().toString("yyyy-MM-dd")

        if not nombre:
            QMessageBox.warning(self, "Validación", "Debe ingresar el nombre del producto.")
            return

        datos = {
            "nombre": nombre,
            "cantidad_inicial": cantidad_inicial,
            "fecha_caducidad": fecha_caducidad,
        }

        res = ClienteMonitoreo.registrar_producto(datos)
        if res["exito"]:
            cuerpo = res["datos"]
            ficha = cuerpo.get("ficha_tecnica_generada", {})
            QMessageBox.information(
                self, "Producto Registrado",
                f"Producto '{nombre}' registrado exitosamente.\n\n"
                f"Lote inicial: {cuerpo.get('codigo_lote', '—')}\n"
                f"Laboratorio: {cuerpo.get('laboratorio', '—')}\n\n"
                f"Ficha técnica generada:\n"
                f"Componente activo: {ficha.get('componente_activos', '—')}\n"
                f"Tipo: {ficha.get('tipo_producto', '—')}\n"
                f"Indicación ambiental: {ficha.get('indicacion_ambiental', '—')}"
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", str(res.get("error", "No se pudo registrar el producto.")))