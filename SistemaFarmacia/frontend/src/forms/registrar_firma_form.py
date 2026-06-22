from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)


class RegistrarFirmaView(QWidget):
    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Registrar Firma PIN")
        self.resize(300, 200)

        layout = QVBoxLayout()

        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("Ingrese PIN de Operación")
        self.input_pin.setEchoMode(QLineEdit.Password)

        self.btn_guardar = QPushButton("Guardar PIN")

        layout.addWidget(QLabel("PIN de Seguridad"))
        layout.addWidget(self.input_pin)
        layout.addStretch()
        layout.addWidget(self.btn_guardar)

        self.setLayout(layout)

        self.btn_guardar.clicked.connect(self.guardar_pin)

    def guardar_pin(self):
        pin = self.input_pin.text().strip()
        if not pin:
            QMessageBox.warning(self, "Validación", "Debe ingresar su PIN.")
            return

        if self.callback_exito:
            self.callback_exito(pin)
        QMessageBox.information(self, "Éxito", "PIN registrado temporalmente para esta sesión.")
        self.close()
