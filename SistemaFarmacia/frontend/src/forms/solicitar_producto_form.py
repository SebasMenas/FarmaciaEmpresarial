from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from api.cliente_monitoreo import ClienteMonitoreo


class SolicitarProductoView(QWidget):
    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Registrar Nuevo Producto")
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Nombre del producto
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del producto")

        # Stock mínimo
        self.input_stock_min = QLineEdit()
        self.input_stock_min.setPlaceholderText("Stock mínimo (ej: 10)")
        self.input_stock_min.setText("0")  # Valor por defecto

        # Stock máximo
        self.input_stock_max = QLineEdit()
        self.input_stock_max.setPlaceholderText("Stock máximo (ej: 100)")

        # Botón
        self.btn_registrar = QPushButton("Registrar Producto")

        layout.addWidget(QLabel("Nombre del Producto"))
        layout.addWidget(self.input_nombre)

        layout.addWidget(QLabel("Stock Mínimo"))
        layout.addWidget(self.input_stock_min)

        layout.addWidget(QLabel("Stock Máximo"))
        layout.addWidget(self.input_stock_max)

        layout.addStretch()
        layout.addWidget(self.btn_registrar)

        self.setLayout(layout)

        self.btn_registrar.clicked.connect(self.registrar_producto)

    def registrar_producto(self):
        nombre = self.input_nombre.text().strip()
        stock_min_str = self.input_stock_min.text().strip()
        stock_max_str = self.input_stock_max.text().strip()

        if not nombre or not stock_max_str:
            QMessageBox.warning(self, "Validación", "Debe ingresar el nombre del producto y el stock máximo.")
            return

        if stock_min_str and not stock_min_str.isdigit():
            QMessageBox.warning(self, "Validación", "El stock mínimo debe ser un número entero válido.")
            return

        if not stock_max_str.isdigit():
            QMessageBox.warning(self, "Validación", "El stock máximo debe ser un número entero válido.")
            return

        stock_min = int(stock_min_str) if stock_min_str else 0
        stock_max = int(stock_max_str)

        if stock_min < 0:
            QMessageBox.warning(self, "Validación", "El stock mínimo no puede ser negativo.")
            return

        if stock_max <= 0:
            QMessageBox.warning(self, "Validación", "El stock máximo debe ser mayor a cero.")
            return

        if stock_max <= stock_min:
            QMessageBox.warning(self, "Validación", "El stock máximo debe ser mayor que el stock mínimo.")
            return

        datos = {
            "nombre": nombre,
            "stock_min": stock_min,
            "stock_max": stock_max
        }

        res = ClienteMonitoreo.registrar_producto(datos)
        if res["exito"]:
            QMessageBox.information(
                self, "Registro Exitoso",
                f"Producto '{nombre}' registrado correctamente."
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", res.get("error", "Error al registrar el producto."))
