from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QHeaderView,
)
from api.cliente_monitoreo import ClienteMonitoreo
from api.cliente_operaciones import ClienteOperaciones
from forms.registrar_firma_form import RegistrarFirmaView
from forms.elaborar_receta_form import ElaborarRecetaView


class AuxilarDiplo(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Elaboración y Validación de Recetas Magistrales")
        self.resize(1400, 800)

        self.pin_actual = None
        self.lotes_disponibles = []
        self.recetas_espera = []
        self.recetas_elaboracion = []

        self.inicializar_ui()
        self.cargar_datos_iniciales()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA 1: ÓRDENES PENDIENTES (EN ESPERA)
        # ==================================================
        grupo_ordenes = QGroupBox("Cola de Recetas en Espera (FIFO)")
        layout_ordenes = QVBoxLayout()

        self.tabla_ordenes = QTableWidget()
        self.tabla_ordenes.setColumnCount(5)
        self.tabla_ordenes.setHorizontalHeaderLabels([
            "ID Receta",
            "Número Orden",
            "Id Cliente",
            "Tipo Receta",
            "Hora Ingreso"
        ])
        self.tabla_ordenes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_ordenes.addWidget(self.tabla_ordenes)
        grupo_ordenes.setLayout(layout_ordenes)

        # ==================================================
        # FILA 2: RECETAS EN ELABORACIÓN
        # ==================================================
        grupo_recetas = QGroupBox("Recetas Magistrales en Elaboración")
        layout_recetas = QVBoxLayout()

        self.tabla_recetas = QTableWidget()
        self.tabla_recetas.setColumnCount(5)
        self.tabla_recetas.setHorizontalHeaderLabels([
            "ID Receta",
            "Número Orden",
            "Id Cliente",
            "Tipo Receta",
            "Ticket de Validación"
        ])
        self.tabla_recetas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_recetas.addWidget(self.tabla_recetas)
        grupo_recetas.setLayout(layout_recetas)

        # ==================================================
        # FILA 3: ACCIONES RÁPIDAS
        # ==================================================
        grupo_acciones = QGroupBox("Acciones Rápidas de Auxiliar Diplomado")
        layout_acciones = QHBoxLayout()

        self.btn_validar = QPushButton("Registrar PIN / Firma")
        self.btn_ticket = QPushButton("Generar Ticket Validación")
        self.btn_elaborar = QPushButton("Elaborar Receta (Lock Lote)")
        self.btn_dispensar = QPushButton("Dispensar Receta")
        self.btn_refrescar = QPushButton("Refrescar Cola")

        self.btn_validar.setFixedHeight(40)
        self.btn_ticket.setFixedHeight(40)
        self.btn_elaborar.setFixedHeight(40)
        self.btn_dispensar.setFixedHeight(40)
        self.btn_refrescar.setFixedHeight(40)

        layout_acciones.addWidget(self.btn_validar)
        layout_acciones.addWidget(self.btn_ticket)
        layout_acciones.addWidget(self.btn_elaborar)
        layout_acciones.addWidget(self.btn_dispensar)
        layout_acciones.addWidget(self.btn_refrescar)
        grupo_acciones.setLayout(layout_acciones)

        # Agregar layouts principales
        layout_principal.addWidget(grupo_ordenes, 2)
        layout_principal.addWidget(grupo_recetas, 2)
        layout_principal.addWidget(grupo_acciones, 1)

        # Eventos
        self.btn_validar.clicked.connect(self.abrir_registrar_firma)
        self.btn_elaborar.clicked.connect(self.abrir_elaborar_receta)
        self.btn_ticket.clicked.connect(self.generar_ticket)
        self.btn_dispensar.clicked.connect(self.dispensar_receta)
        self.btn_refrescar.clicked.connect(self.cargar_datos_iniciales)

    # ==================================================
    # LÓGICA DE NEGOCIO Y CONEXIONES API
    # ==================================================

    def cargar_datos_iniciales(self):
        self.cargar_lotes()
        self.cargar_recetas()

    def cargar_lotes(self):
        res = ClienteMonitoreo.obtener_productos_disponibles()
        if res["exito"]:
            self.lotes_disponibles = res["datos"]
        else:
            QMessageBox.warning(self, "Advertencia", f"No se pudo cargar la lista de lotes:\n{res.get('error', 'Error desconocido')}")

    def cargar_recetas(self):
        res = ClienteOperaciones.obtener_cola_recetas()
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la cola de recetas: {res.get('error')}")
            return

        recetas = res["datos"]
        self.recetas_espera = [r for r in recetas if r.get("estado") == "EN_ESPERA"]
        self.recetas_elaboracion = [r for r in recetas if r.get("estado") == "EN_ELABORACION"]

        # 1. Poblar Tabla Órdenes en Espera
        self.tabla_ordenes.setRowCount(len(self.recetas_espera))
        for fila, rec in enumerate(self.recetas_espera):
            num_orden = rec.get("numero_orden") or rec.get("venta", {}).get("codigo_venta", "Desconocido")
            id_cliente = rec.get("id_cliente") or rec.get("venta", {}).get("id_cliente", "Desconocido")
            self.tabla_ordenes.setItem(fila, 0, QTableWidgetItem(str(rec.get("id"))))
            self.tabla_ordenes.setItem(fila, 1, QTableWidgetItem(str(num_orden)))
            self.tabla_ordenes.setItem(fila, 2, QTableWidgetItem(str(id_cliente)))
            self.tabla_ordenes.setItem(fila, 3, QTableWidgetItem(str(rec.get("tipo"))))
            self.tabla_ordenes.setItem(fila, 4, QTableWidgetItem(str(rec.get("fecha_ingreso", ""))[:19]))

        # 2. Poblar Tabla Recetas en Elaboración
        self.tabla_recetas.setRowCount(len(self.recetas_elaboracion))
        for fila, rec in enumerate(self.recetas_elaboracion):
            num_orden = rec.get("numero_orden") or rec.get("venta", {}).get("codigo_venta", "Desconocido")
            id_cliente = rec.get("id_cliente") or rec.get("venta", {}).get("id_cliente", "Desconocido")
            self.tabla_recetas.setItem(fila, 0, QTableWidgetItem(str(rec.get("id"))))
            self.tabla_recetas.setItem(fila, 1, QTableWidgetItem(str(num_orden)))
            self.tabla_recetas.setItem(fila, 2, QTableWidgetItem(str(id_cliente)))
            self.tabla_recetas.setItem(fila, 3, QTableWidgetItem(str(rec.get("tipo"))))
            self.tabla_recetas.setItem(fila, 4, QTableWidgetItem(str(rec.get("ticket_validacion", ""))))

    def abrir_registrar_firma(self):
        self.ventana_firma = RegistrarFirmaView(callback_exito=self.guardar_pin)
        self.ventana_firma.show()

    def guardar_pin(self, pin):
        self.pin_actual = pin

    def abrir_elaborar_receta(self):
        self.ventana_elaborar = ElaborarRecetaView(
            lotes=self.lotes_disponibles,
            pin_predeterminado=self.pin_actual,
            callback_exito=self.cargar_lotes
        )
        self.ventana_elaborar.show()

    def generar_ticket(self):
        fila_sel = self.tabla_ordenes.currentRow()
        if fila_sel < 0 or fila_sel >= len(self.recetas_espera):
            QMessageBox.warning(self, "Validación", "Seleccione una receta de la cola en espera.")
            return

        receta = self.recetas_espera[fila_sel]
        id_receta = receta.get("id")

        res = ClienteOperaciones.generar_ticket_receta(id_receta)
        if res["exito"]:
            ticket = res["datos"].get("ticket")
            QMessageBox.information(
                self, "Ticket Generado", 
                f"La receta ha sido admitida para elaboración.\n"
                f"Ticket de Validación: {ticket}"
            )
            self.cargar_recetas()
        else:
            QMessageBox.critical(self, "Error de Insumos", f"Control Sanitario:\n{res.get('error')}")
            self.cargar_datos_iniciales() # Recargar en caso de que se haya cancelado por falta de stock

    def dispensar_receta(self):
        fila_sel = self.tabla_recetas.currentRow()
        if fila_sel < 0 or fila_sel >= len(self.recetas_elaboracion):
            QMessageBox.warning(self, "Validación", "Seleccione una receta en elaboración de la tabla correspondiente.")
            return

        receta = self.recetas_elaboracion[fila_sel]
        id_receta = receta.get("id")

        res = ClienteOperaciones.dispensar_receta(id_receta)
        if res["exito"]:
            QMessageBox.information(self, "Dispensación Exitosa", "La receta ha sido dispensada y entregada correctamente.")
            self.cargar_recetas()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo dispensar la receta: {res.get('error')}")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ventana = AuxilarDiplo()
    ventana.show()
    sys.exit(app.exec())