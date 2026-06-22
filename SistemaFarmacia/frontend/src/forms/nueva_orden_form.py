from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from api.cliente_operaciones import ClienteOperaciones


class NuevaOrdenView(QWidget):
    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Nueva Orden de Venta")
        self.resize(350, 200)

        layout = QVBoxLayout()

        self.input_cliente_id = QLineEdit()
        self.input_cliente_id.setPlaceholderText("Ej: CLI-101 o RUT del Cliente")

        self.btn_crear = QPushButton("Iniciar Orden")

        layout.addWidget(QLabel("ID o Identificación del Cliente"))
        layout.addWidget(self.input_cliente_id)
        layout.addStretch()
        layout.addWidget(self.btn_crear)

        self.setLayout(layout)

        self.btn_crear.clicked.connect(self.iniciar_orden)

    def iniciar_orden(self):
        cliente_id = self.input_cliente_id.text().strip()
        if not cliente_id:
            QMessageBox.warning(self, "Validación", "Debe ingresar el identificador del cliente.")
            return

        res = ClienteOperaciones.iniciar_venta(cliente_id)
        if res["exito"]:
            QMessageBox.information(self, "Éxito", "Orden iniciada correctamente.")
            if self.callback_exito:
                # Pasar la venta recién creada al callback
                self.callback_exito(res["datos"])
            self.close()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar la orden:\n{res.get('error')}")
