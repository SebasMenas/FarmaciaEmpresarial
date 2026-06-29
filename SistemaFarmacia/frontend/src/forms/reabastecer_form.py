from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QSpinBox,
    QDateEdit,
    QComboBox,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import QDate
from api.AdminConsultas import ClienteMonitoreo


class ReabastecerProductoView(QWidget):
    """
    Formulario para que el Admin reabastezca un producto YA EXISTENTE
    en catálogo.

    El Admin solo indica qué producto, cuánta cantidad y para cuándo
    vence. El laboratorio proveedor y los códigos de lote/trazabilidad
    los genera el backend automáticamente (mismo patrón que usa el
    laboratorio externo real al despachar un pedido), evitando además
    colisiones con las columnas únicas de la base de datos.
    """

    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.setWindowTitle("Reabastecer Producto")
        self.resize(400, 280)

        layout = QVBoxLayout()

        self.cmb_productos = QComboBox()
        self.cargar_productos_combo()

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 100000)
        self.spin_cantidad.setValue(50)

        self.date_caducidad = QDateEdit()
        self.date_caducidad.setCalendarPopup(True)
        self.date_caducidad.setDate(QDate.currentDate().addDays(120))
        self.date_caducidad.setMinimumDate(QDate.currentDate().addDays(1))

        form = QFormLayout()
        form.addRow("Producto", self.cmb_productos)
        form.addRow("Cantidad a ingresar", self.spin_cantidad)
        form.addRow("Fecha de caducidad", self.date_caducidad)

        self.lbl_nota = QLabel(
            "El laboratorio proveedor y los códigos de lote/trazabilidad\n"
            "se generan automáticamente al registrar el reabastecimiento."
        )
        self.lbl_nota.setWordWrap(True)

        self.btn_reabastecer = QPushButton("Registrar Reabastecimiento")

        layout.addLayout(form)
        layout.addWidget(self.lbl_nota)
        layout.addStretch()
        layout.addWidget(self.btn_reabastecer)

        self.setLayout(layout)

        self.btn_reabastecer.clicked.connect(self.reabastecer_producto)

    def cargar_productos_combo(self):
        """
        Carga el catálogo real de productos (GET /admin/productos),
        independiente de si ya tienen lotes ingresados o no. Antes esta
        lista se derivaba de los lotes existentes, así que un producto
        recién creado sin stock todavía nunca aparecía para reabastecer.
        """
        self.cmb_productos.clear()

        res = ClienteMonitoreo.listar_catalogo_productos()
        if not res["exito"]:
            QMessageBox.warning(
                self, "Catálogo no disponible",
                f"No se pudo cargar el catálogo de productos:\n{res.get('error', '')}"
            )
            return

        productos = res["datos"]
        if not productos:
            self.cmb_productos.addItem("(Sin productos en catálogo)", None)
            return

        for prod in productos:
            etiqueta = f"{prod['nombre']}  —  stock actual: {prod.get('stock_total', 0)}"
            self.cmb_productos.addItem(etiqueta, prod["id"])

    def reabastecer_producto(self):
        prod_id = self.cmb_productos.currentData()
        if not prod_id:
            QMessageBox.warning(self, "Validación", "Debe seleccionar un producto.")
            return

        cantidad = self.spin_cantidad.value()
        fecha_caducidad = self.date_caducidad.date().toString("yyyy-MM-dd")

        datos_lote = {
            "producto_id": prod_id,
            "cantidad": cantidad,
            "fecha_caducidad": fecha_caducidad,
        }

        res = ClienteMonitoreo.registrar_lote(datos_lote)
        if res["exito"]:
            datos_resultado = res["datos"]
            QMessageBox.information(
                self, "Reabastecimiento Exitoso",
                f"Lote ingresado exitosamente:\n"
                f"Lote: {datos_resultado.get('codigo_lote', '—')}\n"
                f"Trazabilidad: {datos_resultado.get('codigo_trazabilidad', '—')}\n"
                f"Laboratorio: {datos_resultado.get('laboratorio', '—')}\n"
                f"Cantidad: {cantidad}"
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", str(res.get("error", "Error al registrar el reabastecimiento.")))