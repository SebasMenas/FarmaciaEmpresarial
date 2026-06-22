from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
)
from api.cliente_monitoreo import ClienteMonitoreo
from api.cliente_operaciones import ClienteOperaciones
from forms.nueva_orden_form import NuevaOrdenView
from forms.agregar_item_form import AgregarItemView
from forms.procesar_orden_form import ProcesarOrdenView


class OrdenesView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestión de Ventas y Órdenes - Técnico")
        self.resize(1400, 800)

        self.venta_activa = None  # Almacena el dict de VentaDTO activa
        self.carrito_items = []   # Mantiene los ítems del carro localmente
        self.lotes_disponibles = []

        self.inicializar_ui()
        self.cargar_inventario()
        self.actualizar_estado_carro()

    def inicializar_ui(self):
        layout_principal = QHBoxLayout(self)

        # =====================================
        # COLUMNA IZQUIERDA: CONTROLES
        # =====================================
        panel_botones = QVBoxLayout()

        self.lbl_estado = QLabel("Sin Orden Activa")
        self.lbl_estado.setStyleSheet("font-weight: bold; color: #ff5555; font-size: 14px;")
        self.lbl_estado.setWordWrap(True)

        self.btn_nueva_orden = QPushButton("Nueva Venta")
        self.btn_procesar = QPushButton("Procesar / Facturar")
        self.btn_cancelar = QPushButton("Cancelar Orden")
        self.btn_refrescar = QPushButton("Refrescar Stock")

        self.btn_nueva_orden.setFixedHeight(40)
        self.btn_procesar.setFixedHeight(40)
        self.btn_cancelar.setFixedHeight(40)
        self.btn_refrescar.setFixedHeight(40)

        panel_botones.addWidget(QLabel("Estado de la Sesión:"))
        panel_botones.addWidget(self.lbl_estado)
        panel_botones.addSpacing(20)
        panel_botones.addWidget(self.btn_nueva_orden)
        panel_botones.addWidget(self.btn_procesar)
        panel_botones.addWidget(self.btn_cancelar)
        panel_botones.addWidget(self.btn_refrescar)
        panel_botones.addStretch()

        # =====================================
        # COLUMNA DERECHA: TABLAS
        # =====================================
        panel_tablas = QVBoxLayout()

        # 1. Carrito de Compras de la Orden Activa
        grupo_ordenes = QGroupBox("Carrito de Compras (Orden Activa)")
        layout_ordenes = QVBoxLayout()

        self.tabla_ordenes = QTableWidget()
        self.tabla_ordenes.setColumnCount(4)
        self.tabla_ordenes.setHorizontalHeaderLabels([
            "Ítem",
            "Código Lote",
            "Cantidad",
            "Estado"
        ])
        self.tabla_ordenes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_ordenes.addWidget(self.tabla_ordenes)
        grupo_ordenes.setLayout(layout_ordenes)

        # 2. Inventario Disponible para Venta
        grupo_productos = QGroupBox("Inventario de Insumos / Medicamentos Disponibles")
        layout_productos = QVBoxLayout()

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(6)
        self.tabla_productos.setHorizontalHeaderLabels([
            "Medicamento / Lote",
            "Temperatura",
            "Fecha Venc.",
            "Stock",
            "Estado",
            "Acción"
        ])
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_productos.addWidget(self.tabla_productos)
        grupo_productos.setLayout(layout_productos)

        panel_tablas.addWidget(grupo_ordenes, 2)
        panel_tablas.addWidget(grupo_productos, 3)

        # Configurar Layout Principal
        layout_principal.addLayout(panel_botones, 1)
        layout_principal.addLayout(panel_tablas, 4)

        # Eventos
        self.btn_nueva_orden.clicked.connect(self.abrir_nueva_orden)
        self.btn_procesar.clicked.connect(self.abrir_procesar_orden)
        self.btn_cancelar.clicked.connect(self.cancelar_orden_activa)
        self.btn_refrescar.clicked.connect(self.cargar_inventario)

    # =====================================
    # LÓGICA DE NEGOCIO Y API
    # =====================================

    def cargar_inventario(self):
        res = ClienteMonitoreo.obtener_productos_disponibles()
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el inventario: {res.get('error')}")
            return

        self.lotes_disponibles = res["datos"]
        
        self.tabla_productos.setRowCount(len(self.lotes_disponibles))

        for fila, lote in enumerate(self.lotes_disponibles):
            prod_name = lote.get("producto", {}).get("nombre", "Desconocido")
            temp_env = lote.get("producto", {}).get("indicacion_ambiental", "AMBIENTE")
            temp = "21°C (Ambiente)" if temp_env == "AMBIENTE" else "4°C (Refrigerado)"
            cod_lote = lote.get("codigo_lote", "")
            stock = lote.get("cantidad", 0)

            self.tabla_productos.setItem(fila, 0, QTableWidgetItem(f"{prod_name}\nLote: {cod_lote}"))
            self.tabla_productos.setItem(fila, 1, QTableWidgetItem(str(temp)))
            self.tabla_productos.setItem(fila, 2, QTableWidgetItem(str(lote.get("fecha_caducidad", ""))))
            self.tabla_productos.setItem(fila, 3, QTableWidgetItem(str(stock)))
            self.tabla_productos.setItem(fila, 4, QTableWidgetItem(str(lote.get("estado", ""))))

            # Botón para agregar al carro
            boton = QPushButton("Agregar")
            # Habilitado únicamente si hay una orden activa
            boton.setEnabled(self.venta_activa is not None)
            
            # Pasar parámetros necesarios
            lote_id = lote.get("id")
            boton.clicked.connect(
                lambda _, lid=lote_id, lcode=cod_lote, pname=prod_name, sdisp=stock: 
                    self.abrir_agregar_item(lid, lcode, pname, sdisp)
            )
            self.tabla_productos.setCellWidget(fila, 5, boton)

    def abrir_nueva_orden(self):
        self.ventana_nueva_orden = NuevaOrdenView(callback_exito=self.iniciar_venta_ui)
        self.ventana_nueva_orden.show()

    def iniciar_venta_ui(self, datos_venta):
        self.venta_activa = datos_venta
        self.carrito_items = []
        self.actualizar_estado_carro()
        self.cargar_inventario()

    def abrir_agregar_item(self, lote_id, lote_cod, prod_nombre, stock_disp):
        if not self.venta_activa:
            QMessageBox.warning(self, "Validación", "Debe iniciar una nueva venta primero.")
            return

        self.ventana_agregar = AgregarItemView(
            id_venta=self.venta_activa.get("id"),
            lote_id=lote_id,
            lote_cod=lote_cod,
            prod_nombre=prod_nombre,
            stock_disp=stock_disp,
            callback_exito=lambda lote_final, cant: self.registrar_item_carrito_local(prod_nombre, lote_final, cant)
        )
        self.ventana_agregar.show()

    def registrar_item_carrito_local(self, prod_nombre, lote_cod, cantidad):
        self.cargar_inventario()
        self.recargar_carrito_visual(prod_nombre, lote_cod, cantidad)

    def recargar_carrito_visual(self, prod_nombre, lote_cod_agregado, cantidad):
        encontrado = False
        for item in self.carrito_items:
            if item["lote_cod"] == lote_cod_agregado:
                item["cantidad"] += cantidad
                encontrado = True
                break
        
        if not encontrado:
            self.carrito_items.append({
                "index": len(self.carrito_items) + 1,
                "producto": prod_nombre,
                "lote_cod": lote_cod_agregado,
                "cantidad": cantidad,
                "estado": "Cargado en Carro"
            })
            
        self.tabla_ordenes.setRowCount(len(self.carrito_items))
        for fila, item in enumerate(self.carrito_items):
            self.tabla_ordenes.setItem(fila, 0, QTableWidgetItem(str(item['producto'])))
            self.tabla_ordenes.setItem(fila, 1, QTableWidgetItem(str(item['lote_cod'])))
            self.tabla_ordenes.setItem(fila, 2, QTableWidgetItem(str(item['cantidad'])))
            self.tabla_ordenes.setItem(fila, 3, QTableWidgetItem(str(item['estado'])))

    def abrir_procesar_orden(self):
        if not self.venta_activa:
            QMessageBox.warning(self, "Validación", "No hay ninguna orden activa para procesar.")
            return

        self.ventana_procesar = ProcesarOrdenView(
            id_venta=self.venta_activa.get("id"),
            callback_exito=self.finalizar_venta_ui
        )
        self.ventana_procesar.show()

    def finalizar_venta_ui(self):
        self.venta_activa = None
        self.carrito_items = []
        self.tabla_ordenes.setRowCount(0)
        self.actualizar_estado_carro()
        self.cargar_inventario()

    def cancelar_orden_activa(self):
        if not self.venta_activa:
            return

        confirmar = QMessageBox.question(
            self, "Confirmar Cancelación", 
            "¿Está seguro de que desea cancelar esta orden? El stock físico será devuelto al inventario disponible.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            res = ClienteOperaciones.cancelar_venta(self.venta_activa.get("id"))
            if res["exito"]:
                QMessageBox.information(self, "Éxito", "Venta cancelada y stock devuelto.")
                self.finalizar_venta_ui()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo cancelar la venta: {res.get('error')}")

    def actualizar_estado_carro(self):
        if self.venta_activa:
            codigo = self.venta_activa.get("codigo_venta", "ORD-XXXX")
            cliente = self.venta_activa.get("id_cliente", "CLI-XXXX")
            self.lbl_estado.setText(f"Orden: {codigo}\nCliente: {cliente}")
            self.lbl_estado.setStyleSheet("font-weight: bold; color: #55ff55; font-size: 14px;")
            self.btn_procesar.setEnabled(True)
            self.btn_cancelar.setEnabled(True)
            self.btn_nueva_orden.setEnabled(False)
        else:
            self.lbl_estado.setText("Sin Orden Activa")
            self.lbl_estado.setStyleSheet("font-weight: bold; color: #ff5555; font-size: 14px;")
            self.btn_procesar.setEnabled(False)
            self.btn_cancelar.setEnabled(False)
            self.btn_nueva_orden.setEnabled(True)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ventana = OrdenesView()
    ventana.show()
    sys.exit(app.exec())