from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox,
    QHeaderView, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from api.AdminConsultas import ClienteMonitoreo, ClienteOperaciones


class OrdenesView(QWidget):
    """
    Pantalla del Técnico. El cliente y su pedido (productos deseados y,
    si corresponde, receta ya emitida por un doctor) se generan
    automáticamente al presionar "Nueva Venta" — el Técnico nunca asigna
    un ID de cliente ni redacta ninguna receta. Al facturar, si el pedido
    trae receta, la derivación al Auxiliar Diplomado es automática; no se
    le pregunta nada al Técnico en ese momento.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestión de Órdenes")
        self.resize(1400, 800)

        self.venta_actual_id = None
        self.pedido_actual = []  # lista de líneas {producto_id, nombre, cantidad_solicitada, cubierto}
        self.productos_disponibles = []

        self.inicializar_ui()
        self.cargar_inventario()

    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self)

        # =====================================
        # COLUMNA IZQUIERDA — ACCIONES
        # =====================================
        panel_botones = QVBoxLayout()

        self.lbl_cliente_actual = QLabel("Sin venta activa")
        self.lbl_cliente_actual.setWordWrap(True)

        self.lbl_receta_actual = QLabel("")
        self.lbl_receta_actual.setWordWrap(True)
        self.lbl_receta_actual.setStyleSheet("color: #B85C00; font-weight: bold;")

        self.btn_nueva_venta = QPushButton("Nueva Venta")
        self.btn_facturar = QPushButton("Facturar")
        self.btn_cancelar_venta = QPushButton("Cancelar Venta")

        self.btn_facturar.setEnabled(False)
        self.btn_cancelar_venta.setEnabled(False)

        panel_botones.addWidget(self.lbl_cliente_actual)
        panel_botones.addWidget(self.lbl_receta_actual)
        panel_botones.addSpacing(12)
        panel_botones.addWidget(self.btn_nueva_venta)
        panel_botones.addWidget(self.btn_facturar)
        panel_botones.addWidget(self.btn_cancelar_venta)
        panel_botones.addStretch()

        # =====================================
        # COLUMNA DERECHA — TABLAS
        # =====================================
        panel_tablas = QVBoxLayout()

        # -------------------------------------
        # TABLA 1: PEDIDO DEL CLIENTE ACTUAL
        # -------------------------------------
        grupo_pedido = QGroupBox("Pedido del Cliente Actual")
        layout_pedido = QVBoxLayout()

        self.tabla_pedido = QTableWidget()
        self.tabla_pedido.setColumnCount(4)
        self.tabla_pedido.setHorizontalHeaderLabels([
            "Producto",
            "Cantidad solicitada",
            "Estado",
            "Acción"
        ])
        header_pedido = self.tabla_pedido.horizontalHeader()
        header_pedido.setSectionResizeMode(0, QHeaderView.Stretch)
        header_pedido.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_pedido.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_pedido.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout_pedido.addWidget(self.tabla_pedido)
        grupo_pedido.setLayout(layout_pedido)

        # -------------------------------------
        # TABLA 2: INVENTARIO DISPONIBLE (solo lectura)
        # -------------------------------------
        grupo_productos = QGroupBox("Inventario Disponible")
        layout_productos = QVBoxLayout()

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(5)
        self.tabla_productos.setHorizontalHeaderLabels([
            "Producto",
            "Laboratorio",
            "Fecha Cad.",
            "Estado",
            "Stock"
        ])
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout_productos.addWidget(self.tabla_productos)
        grupo_productos.setLayout(layout_productos)

        panel_tablas.addWidget(grupo_pedido, 2)
        panel_tablas.addWidget(grupo_productos, 1)

        # =====================================
        layout_principal.addLayout(panel_botones, 1)
        layout_principal.addLayout(panel_tablas, 5)

        # Eventos
        self.btn_nueva_venta.clicked.connect(self.iniciar_nueva_venta)
        self.btn_facturar.clicked.connect(self.facturar_venta)
        self.btn_cancelar_venta.clicked.connect(self.cancelar_venta_actual)

    # ==================================================
    # MÉTODOS DE DATOS Y CONEXIONES API
    # ==================================================

    def iniciar_nueva_venta(self):
        if self.venta_actual_id:
            QMessageBox.warning(
                self, "Venta en curso",
                "Ya hay una venta activa. Factúrela o cancélela antes de atender a un nuevo cliente."
            )
            return

        res = ClienteOperaciones.atender_cliente()
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo atender al cliente:\n{res.get('error')}")
            return

        venta = res["datos"]
        self.venta_actual_id = venta["id"]

        self.lbl_cliente_actual.setText(
            f"Cliente: {venta['id_cliente']}\nOrden: {venta['codigo_venta']}"
        )

        if venta.get("requiere_receta"):
            self.lbl_receta_actual.setText(
                f"⚠ Pedido con receta {venta.get('tipo_receta', '').lower()}.\n"
                "Se derivará automáticamente al Auxiliar Diplomado al facturar."
            )
        else:
            self.lbl_receta_actual.setText("")

        self.btn_facturar.setEnabled(True)
        self.btn_cancelar_venta.setEnabled(True)

        self.cargar_pedido_actual()

    def cargar_pedido_actual(self):
        if not self.venta_actual_id:
            return

        res = ClienteOperaciones.obtener_pedido_solicitado(self.venta_actual_id)
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el pedido:\n{res.get('error')}")
            return

        datos = res["datos"]
        self.pedido_actual = datos.get("productos_solicitados", [])
        self.tabla_pedido.setRowCount(len(self.pedido_actual))

        for fila, linea in enumerate(self.pedido_actual):
            self.tabla_pedido.setItem(fila, 0, QTableWidgetItem(str(linea.get("nombre", ""))))
            self.tabla_pedido.setItem(fila, 1, QTableWidgetItem(str(linea.get("cantidad_solicitada", 0))))

            cubierto = linea.get("cubierto", False)
            estado_texto = "En carrito" if cubierto else "Pendiente"
            self.tabla_pedido.setItem(fila, 2, QTableWidgetItem(estado_texto))

            boton = QPushButton("Agregar al carrito")
            boton.setEnabled(not cubierto)
            producto_id = linea.get("producto_id")
            cantidad = linea.get("cantidad_solicitada")
            boton.clicked.connect(
                lambda _, pid=producto_id, cant=cantidad: self.agregar_al_carrito(pid, cant)
            )
            self.tabla_pedido.setCellWidget(fila, 3, boton)

    def agregar_al_carrito(self, producto_id, cantidad):
        if not self.venta_actual_id:
            return

        res = ClienteOperaciones.agregar_producto_pedido(self.venta_actual_id, producto_id, cantidad)
        if res["exito"]:
            # El stock recién cambió: se refrescan ambas tablas automáticamente,
            # sin que el Técnico tenga que presionar nada manual.
            self.cargar_pedido_actual()
            self.cargar_inventario()
        else:
            QMessageBox.warning(
                self, "Sin stock disponible",
                f"No se pudo agregar el producto al carrito:\n{res.get('error')}"
            )

    def cargar_inventario(self):
        res = ClienteMonitoreo.obtener_productos_disponibles()
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el inventario: {res.get('error')}")
            return

        self.productos_disponibles = res["datos"]
        self.tabla_productos.setRowCount(len(self.productos_disponibles))

        for fila, lote in enumerate(self.productos_disponibles):
            prod_name = lote.get("producto", {}).get("nombre", "Desconocido")
            lab_name = lote.get("laboratorio", {}).get("nombre", "—") if lote.get("laboratorio") else "—"

            self.tabla_productos.setItem(fila, 0, QTableWidgetItem(str(prod_name)))
            self.tabla_productos.setItem(fila, 1, QTableWidgetItem(str(lab_name)))
            self.tabla_productos.setItem(fila, 2, QTableWidgetItem(str(lote.get("fecha_caducidad", ""))))
            self.tabla_productos.setItem(fila, 3, QTableWidgetItem(str(lote.get("estado", ""))))
            self.tabla_productos.setItem(fila, 4, QTableWidgetItem(str(lote.get("cantidad", 0))))

    def facturar_venta(self):
        if not self.venta_actual_id:
            return

        pendientes = [linea for linea in self.pedido_actual if not linea.get("cubierto")]
        if pendientes:
            confirmar = QMessageBox.question(
                self, "Pedido incompleto",
                f"Quedan {len(pendientes)} producto(s) del pedido sin agregar al carrito.\n"
                "¿Desea facturar igual solo con lo ya agregado?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirmar != QMessageBox.Yes:
                return

        # No se pregunta nada sobre receta: el backend ya sabe si esta
        # venta la requiere desde que el cliente fue atendido.
        res = ClienteOperaciones.finalizar_facturacion(self.venta_actual_id)
        if res["exito"]:
            datos = res["datos"]
            if datos.get("derivado_a_recetas"):
                QMessageBox.information(
                    self, "Venta facturada",
                    "Venta completada. El pedido fue derivado automáticamente "
                    "a la cola del Auxiliar Diplomado para su elaboración/dispensación."
                )
            else:
                QMessageBox.information(self, "Venta facturada", "Venta completada correctamente.")
            self._cerrar_venta_actual()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo facturar la venta:\n{res.get('error')}")

    def cancelar_venta_actual(self):
        if not self.venta_actual_id:
            return

        confirmar = QMessageBox.question(
            self, "Confirmar Cancelación",
            "¿Está seguro de que desea cancelar esta venta? El stock ya agregado al carrito se restituirá.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar != QMessageBox.Yes:
            return

        res = ClienteOperaciones.cancelar_venta(self.venta_actual_id)
        if res["exito"]:
            QMessageBox.information(self, "Venta cancelada", "La transacción fue revertida y el stock restituido.")
            self._cerrar_venta_actual()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar la venta:\n{res.get('error')}")

    def _cerrar_venta_actual(self):
        self.venta_actual_id = None
        self.pedido_actual = []
        self.tabla_pedido.setRowCount(0)
        self.lbl_cliente_actual.setText("Sin venta activa")
        self.lbl_receta_actual.setText("")
        self.btn_facturar.setEnabled(False)
        self.btn_cancelar_venta.setEnabled(False)
        self.cargar_inventario()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = OrdenesView()
    ventana.show()

    sys.exit(app.exec())