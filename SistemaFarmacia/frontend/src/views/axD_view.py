from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QHeaderView,
)
from api.AdminConsultas import ClienteMonitoreo, ClienteOperaciones


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
        # FILA 1: VALIDACIÓN Y ÓRDENES PENDIENTES (EN ESPERA)
        # ==================================================
        fila_1 = QHBoxLayout()

        # 1. Validación de Credencial
        grupo_validacion = QGroupBox("Firma Digital del Auxiliar")
        layout_validacion = QVBoxLayout()

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Ingrese PIN de Operación")
        self.input_codigo.setEchoMode(QLineEdit.Password)

        self.btn_validar = QPushButton("Registrar Firma PIN")
        self.btn_validar.clicked.connect(self.validar_credencial)

        layout_validacion.addWidget(QLabel("Credencial / PIN"))
        layout_validacion.addWidget(self.input_codigo)
        layout_validacion.addWidget(self.btn_validar)
        grupo_validacion.setLayout(layout_validacion)

        # 2. Tabla órdenes en espera
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

        fila_1.addWidget(grupo_validacion, 1)
        fila_1.addWidget(grupo_ordenes, 3)

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
        # FILA 3: ACCIONES Y ELABORACIÓN
        # ==================================================
        grupo_acciones = QGroupBox("Operaciones Sanitarias y Elaboración")
        layout_acciones = QVBoxLayout()

        self.cmb_productos = QComboBox()

        botones = QHBoxLayout()
        self.btn_elaborar = QPushButton("Elaborar Receta (Lock Batch)")
        self.btn_ticket = QPushButton("Generar Ticket Validación")
        self.btn_dispensar = QPushButton("Dispensar Receta")
        self.btn_refrescar = QPushButton("Refrescar Cola")

        self.btn_elaborar.clicked.connect(self.elaborar_receta)
        self.btn_ticket.clicked.connect(self.generar_ticket)
        self.btn_dispensar.clicked.connect(self.dispensar_receta)
        self.btn_refrescar.clicked.connect(self.cargar_datos_iniciales)

        botones.addWidget(self.btn_ticket)
        botones.addWidget(self.btn_elaborar)
        botones.addWidget(self.btn_dispensar)
        botones.addWidget(self.btn_refrescar)

        layout_acciones.addWidget(QLabel("Seleccionar Lote del Insumo a Bloquear para Manufactura"))
        layout_acciones.addWidget(self.cmb_productos)
        layout_acciones.addLayout(botones)
        grupo_acciones.setLayout(layout_acciones)

        # Agregar layouts principales
        layout_principal.addLayout(fila_1, 1)
        layout_principal.addWidget(grupo_recetas, 1)
        layout_principal.addWidget(grupo_acciones, 1)

    # ==================================================
    # LÓGICA DE NEGOCIO Y CONEXIONES API
    # ==================================================

    def cargar_datos_iniciales(self):
        self.cargar_lotes()
        self.cargar_recetas()

    def cargar_lotes(self):
        res = ClienteMonitoreo.obtener_almacenamiento()
        if res["exito"]:
            self.cmb_productos.clear()
            self.lotes_disponibles = res["datos"]
            for lote in self.lotes_disponibles:
                if lote.get("estado") == "DISPONIBLE":
                    prod_name = lote.get("producto", {}).get("nombre", "Desconocido")
                    lote_cod = lote.get("codigo_lote", "")
                    cant = lote.get("cantidad", 0)
                    self.cmb_productos.addItem(f"{prod_name} (Lote: {lote_cod} | Stock: {cant})", lote.get("id"))
        else:
            QMessageBox.warning(self, "Advertencia", "No se pudo cargar la lista de lotes.")

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
            self.tabla_ordenes.setItem(fila, 0, QTableWidgetItem(str(rec.get("id"))))
            self.tabla_ordenes.setItem(fila, 1, QTableWidgetItem(str(rec.get("numero_orden"))))
            self.tabla_ordenes.setItem(fila, 2, QTableWidgetItem(str(rec.get("id_cliente"))))
            self.tabla_ordenes.setItem(fila, 3, QTableWidgetItem(str(rec.get("tipo"))))
            self.tabla_ordenes.setItem(fila, 4, QTableWidgetItem(str(rec.get("fecha_ingreso", ""))[:19]))

        # 2. Poblar Tabla Recetas en Elaboración
        self.tabla_recetas.setRowCount(len(self.recetas_elaboracion))
        for fila, rec in enumerate(self.recetas_elaboracion):
            self.tabla_recetas.setItem(fila, 0, QTableWidgetItem(str(rec.get("id"))))
            self.tabla_recetas.setItem(fila, 1, QTableWidgetItem(str(rec.get("numero_orden"))))
            self.tabla_recetas.setItem(fila, 2, QTableWidgetItem(str(rec.get("id_cliente"))))
            self.tabla_recetas.setItem(fila, 3, QTableWidgetItem(str(rec.get("tipo"))))
            self.tabla_recetas.setItem(fila, 4, QTableWidgetItem(str(rec.get("ticket_validacion", ""))))

    def validar_credencial(self):
        pin = self.input_codigo.text().strip()
        if not pin:
            QMessageBox.warning(self, "Validación", "Debe ingresar un PIN.")
            return

        self.pin_actual = pin
        QMessageBox.information(self, "Firma Registrada", "El PIN ha sido guardado temporalmente para operaciones en esta sesión.")

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

    def elaborar_receta(self):
        if not self.pin_actual:
            QMessageBox.warning(self, "Validación", "Primero debe registrar su PIN de firma digital.")
            return

        lote_id = self.cmb_productos.currentData()
        if not lote_id:
            QMessageBox.warning(self, "Validación", "No hay lotes disponibles seleccionados.")
            return

        res = ClienteOperaciones.iniciar_manufactura(lote_id, self.pin_actual)
        if res["exito"]:
            datos = res["datos"]
            QMessageBox.information(
                self, "Lote Reservado", 
                f"El lote {datos.get('codigo_lote')} ha sido bloqueado exitosamente "
                f"por 15 minutos en el backend para manufactura magistral."
            )
            self.cargar_lotes()
        else:
            QMessageBox.critical(self, "Firma o Bloqueo Inválido", f"Error:\n{res.get('error')}")

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