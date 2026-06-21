from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from api.AdminConsultas import ClienteMonitoreo


class SolicitarProductoView(QWidget):
    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Solicitar Producto / Simular Proveedor")
        self.resize(400, 350)

        layout = QVBoxLayout()

        # Laboratorio
        self.input_lab_nuevo = QLineEdit()
        self.input_lab_nuevo.setPlaceholderText("Nombre del Laboratorio")

        # Código de lote
        self.input_lote_nuevo = QLineEdit()
        self.input_lote_nuevo.setPlaceholderText("Código de lote")

        # Código de trazabilidad
        self.input_trazabilidad_nuevo = QLineEdit()
        self.input_trazabilidad_nuevo.setPlaceholderText("Código de trazabilidad")

        # Botón
        self.btn_solicitar = QPushButton("Enviar Solicitud / Simular")

        layout.addWidget(QLabel("Laboratorio"))
        layout.addWidget(self.input_lab_nuevo)

        layout.addWidget(QLabel("Código de Lote"))
        layout.addWidget(self.input_lote_nuevo)

        layout.addWidget(QLabel("Código de Trazabilidad"))
        layout.addWidget(self.input_trazabilidad_nuevo)

        layout.addStretch()
        layout.addWidget(self.btn_solicitar)

        self.setLayout(layout)

        self.btn_solicitar.clicked.connect(self.solicitar_producto)

    def solicitar_producto(self):
        lab_nombre = self.input_lab_nuevo.text().strip()
        lote_cod = self.input_lote_nuevo.text().strip()
        traz_cod = self.input_trazabilidad_nuevo.text().strip()

        if not lab_nombre or not lote_cod or not traz_cod:
            QMessageBox.warning(self, "Validación", "Debe completar todos los campos.")
            return

        lab_lower = lab_nombre.lower()
        # Simular comportamiento de validación de laboratorios certificado / no certificado
        if "no" in lab_lower or "uncertified" in lab_lower:
            res = ClienteMonitoreo.simular_proveedor_no_certificado()
            if not res["exito"]:
                detalle = res.get("error", "Transacción abortada: Laboratorio no posee certificación sanitaria.")
                QMessageBox.warning(self, "Control Sanitario", f"Alerta de Calidad:\n{detalle}")
            else:
                QMessageBox.warning(self, "Control Sanitario", "Transacción abortada por falta de certificación del laboratorio.")
        else:
            res = ClienteMonitoreo.simular_proveedor_certificado()
            if res["exito"]:
                datos = res["datos"]
                QMessageBox.information(
                    self, "Simulación Exitosa",
                    f"Se ha inyectado un lote de un proveedor certificado sanitariamente:\n"
                    f"Laboratorio: {datos.get('laboratorio')}\n"
                    f"Lote: {datos.get('codigo_lote')}"
                )
                if self.callback_exito:
                    self.callback_exito()
                self.close()
            else:
                QMessageBox.critical(self, "Error de Simulación", res.get("error", "Error desconocido"))
