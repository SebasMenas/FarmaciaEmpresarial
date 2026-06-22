from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from api.cliente_operaciones import ClienteOperaciones


class AgregarItemView(QWidget):
    def __init__(self, id_venta, lote_id, lote_cod, prod_nombre, stock_disp, callback_exito=None):
        super().__init__()

        self.id_venta = id_venta
        self.lote_id = lote_id
        self.lote_cod = lote_cod
        self.stock_disp = stock_disp
        self.callback_exito = callback_exito

        self.setWindowTitle("Agregar al Carro")
        self.resize(350, 250)

        layout = QVBoxLayout()

        self.lbl_info = QLabel(f"Producto: {prod_nombre}\nLote: {lote_cod}\nStock Disponible: {stock_disp}")
        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText("Cantidad a agregar")

        self.btn_agregar = QPushButton("Agregar al Carrito")

        layout.addWidget(self.lbl_info)
        layout.addWidget(QLabel("Cantidad"))
        layout.addWidget(self.input_cantidad)
        layout.addStretch()
        layout.addWidget(self.btn_agregar)

        self.setLayout(layout)

        self.btn_agregar.clicked.connect(self.agregar_item)

    def agregar_item(self):
        cant_str = self.input_cantidad.text().strip()
        if not cant_str.isdigit():
            QMessageBox.warning(self, "Validación", "La cantidad debe ser un número entero.")
            return

        cantidad = int(cant_str)
        if cantidad <= 0:
            QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor que cero.")
            return

        # Advertencia de stock local
        if cantidad > self.stock_disp:
            confirmar = QMessageBox.warning(
                self, "Advertencia de Stock", 
                "La cantidad ingresada supera el stock visible de este lote. El sistema intentará reasignar stock si existe. ¿Desea continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmar == QMessageBox.No:
                return

        res = ClienteOperaciones.agregar_item_venta(self.id_venta, self.lote_id, cantidad)
        if res["exito"]:
            datos = res["datos"]
            msg = "Producto agregado al carro."
            if datos.get("lote_reasignado"):
                msg += f"\n[Concurrencia] Stock reasignado automáticamente al lote: {datos.get('lote_utilizado')}"
            QMessageBox.information(self, "Éxito", msg)
            lote_final = datos.get("lote_utilizado") if datos.get("lote_reasignado") else self.lote_cod
            if self.callback_exito:
                import inspect
                sig = inspect.signature(self.callback_exito)
                if len(sig.parameters) >= 2:
                    self.callback_exito(lote_final, cantidad)
                else:
                    self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error de Stock / Transacción", f"Error:\n{res.get('error')}")
