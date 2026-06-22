from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
)
from api.cliente_monitoreo import ClienteMonitoreo


class ReabastecerProductoView(QWidget):
    def __init__(self, lotes, callback_exito=None):
        super().__init__()

        self.lotes = lotes
        self.callback_exito = callback_exito
        self.setWindowTitle("Reabastecer Producto")
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Selector de producto
        self.cmb_productos = QComboBox()
        self.cargar_productos_combo()

        # Cantidad
        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText("Cantidad a ingresar")

        # Botón
        self.btn_reabastecer = QPushButton("Registrar Reabastecimiento")

        layout.addWidget(QLabel("Seleccionar Producto"))
        layout.addWidget(self.cmb_productos)

        layout.addWidget(QLabel("Cantidad a ingresar"))
        layout.addWidget(self.input_cantidad)

        layout.addStretch()
        layout.addWidget(self.btn_reabastecer)

        self.setLayout(layout)

        self.btn_reabastecer.clicked.connect(self.reabastecer_producto)

    def cargar_productos_combo(self):
        self.cmb_productos.clear()
        productos_vistos = set()
        for p in self.lotes:
            prod_obj = p.get("producto")
            if prod_obj:
                prod_id = prod_obj.get("id")
                prod_nombre = prod_obj.get("nombre")
                if prod_id not in productos_vistos:
                    productos_vistos.add(prod_id)
                    self.cmb_productos.addItem(prod_nombre, prod_id)

    def reabastecer_producto(self):
        prod_id = self.cmb_productos.currentData()
        if not prod_id:
            QMessageBox.warning(self, "Validación", "Debe seleccionar un producto.")
            return

        cantidad_str = self.input_cantidad.text().strip()
        if not cantidad_str.isdigit():
            QMessageBox.warning(self, "Validación", "La cantidad debe ser un número entero válido.")
            return
        cantidad = int(cantidad_str)
        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor que cero.")
            return

        from datetime import date, timedelta
        
        datos_lote = {
            "producto_id": prod_id,
            "cantidad": cantidad,
            "fecha_caducidad": str(date.today() + timedelta(days=120))
        }

        res = ClienteMonitoreo.registrar_lote(datos_lote)
        if res["exito"]:
            QMessageBox.information(
                self, "Reabastecimiento Exitoso",
                f"Lote ingresado exitosamente.\n"
                f"Cantidad: {cantidad}"
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", res.get("error", "Error al registrar el reabastecimiento."))
