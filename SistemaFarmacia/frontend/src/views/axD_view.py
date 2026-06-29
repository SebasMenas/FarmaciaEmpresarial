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
    QMessageBox,
    QHeaderView,
)
from PySide6.QtGui import QFont
from api.AdminConsultas import ClienteMonitoreo, ClienteOperaciones


class AuxilarDiplo(QWidget):
    """
    Pantalla del Auxiliar Diplomado. El flujo correcto es:
    1. Ingresar código de empleado (otorgado por el Admin) -> desbloquea
       el resto de la pantalla.
    2. Seleccionar una receta de la cola en espera -> se muestra la lista
       REAL de insumos que esa receta requiere (no un catálogo genérico).
    3. Reservar cada insumo requerido -> el sistema resuelve el lote
       automáticamente y valida que el producto realmente sea parte de
       la receta; si no lo es, lo rechaza aunque haya stock disponible.
    4. Validar productos -> solo posible cuando todos los insumos están
       reservados; genera la alerta de elaboración exitosa.
    5. Dispensar receta magistral -> cierra el ciclo y el cliente recibe
       su pedido.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Elaboración y Validación de Recetas Magistrales")
        self.resize(1500, 900)

        self.codigo_validado = False
        self.codigo_actual = None
        self.recetas_espera = []
        self.recetas_elaboracion = []
        self.receta_seleccionada = None
        self.insumos_receta_actual = []

        self.inicializar_ui()
        self.cargar_recetas()
        self._actualizar_bloqueo_pantalla()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA 1: CÓDIGO DE EMPLEADO Y ÓRDENES PENDIENTES
        # ==================================================
        fila_1 = QHBoxLayout()

        # 1. Validación de código de empleado
        grupo_validacion = QGroupBox("Acceso del Auxiliar Diplomado")
        layout_validacion = QVBoxLayout()

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Código asignado por el Administrador")
        self.input_codigo.setEchoMode(QLineEdit.Password)

        self.btn_ingresar_codigo = QPushButton("Ingresar Código Empleado")
        self.btn_ingresar_codigo.clicked.connect(self.ingresar_codigo_empleado)

        self.lbl_estado_codigo = QLabel("Pantalla bloqueada hasta validar el código.")
        self.lbl_estado_codigo.setWordWrap(True)

        layout_validacion.addWidget(QLabel("Código de empleado"))
        layout_validacion.addWidget(self.input_codigo)
        layout_validacion.addWidget(self.btn_ingresar_codigo)
        layout_validacion.addWidget(self.lbl_estado_codigo)
        grupo_validacion.setLayout(layout_validacion)

        # 2. Tabla órdenes en espera
        grupo_ordenes = QGroupBox("Cola de Recetas en Espera (FIFO) — seleccione una para ver sus insumos")
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
        self.tabla_ordenes.itemSelectionChanged.connect(self.seleccionar_receta_espera)
        layout_ordenes.addWidget(self.tabla_ordenes)
        grupo_ordenes.setLayout(layout_ordenes)

        fila_1.addWidget(grupo_validacion, 1)
        fila_1.addWidget(grupo_ordenes, 3)

        # ==================================================
        # FILA 2: INSUMOS REQUERIDOS DE LA RECETA SELECCIONADA
        # (más grande, para que se pueda leer bien)
        # ==================================================
        grupo_insumos = QGroupBox("Insumos Requeridos por la Receta Seleccionada")
        layout_insumos = QVBoxLayout()

        self.lbl_descripcion_receta = QLabel("Seleccione una receta de la cola para ver el detalle.")
        self.lbl_descripcion_receta.setWordWrap(True)
        fuente_descripcion = QFont()
        fuente_descripcion.setPointSize(13)
        fuente_descripcion.setBold(True)
        self.lbl_descripcion_receta.setFont(fuente_descripcion)

        self.tabla_insumos = QTableWidget()
        self.tabla_insumos.setColumnCount(4)
        self.tabla_insumos.setHorizontalHeaderLabels([
            "Producto requerido",
            "Cantidad",
            "Estado",
            "Acción"
        ])
        header_insumos = self.tabla_insumos.horizontalHeader()
        header_insumos.setSectionResizeMode(0, QHeaderView.Stretch)
        header_insumos.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_insumos.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_insumos.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        fuente_tabla = QFont()
        fuente_tabla.setPointSize(12)
        self.tabla_insumos.setFont(fuente_tabla)
        self.tabla_insumos.verticalHeader().setDefaultSectionSize(44)
        self.tabla_insumos.horizontalHeader().setFont(fuente_tabla)

        layout_insumos.addWidget(self.lbl_descripcion_receta)
        layout_insumos.addWidget(self.tabla_insumos)
        grupo_insumos.setLayout(layout_insumos)

        # ==================================================
        # FILA 3: RECETAS EN ELABORACIÓN Y ACCIONES FINALES
        # ==================================================
        fila_3 = QHBoxLayout()

        grupo_recetas = QGroupBox("Recetas Magistrales en Elaboración")
        layout_recetas = QVBoxLayout()

        self.tabla_recetas = QTableWidget()
        self.tabla_recetas.setColumnCount(5)
        self.tabla_recetas.setHorizontalHeaderLabels([
            "ID Receta",
            "Número Orden",
            "Id Cliente",
            "Tipo Receta",
            "Alerta de Elaboración"
        ])
        self.tabla_recetas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_recetas.addWidget(self.tabla_recetas)
        grupo_recetas.setLayout(layout_recetas)

        grupo_acciones = QGroupBox("Acciones")
        layout_acciones = QVBoxLayout()

        self.btn_validar_productos = QPushButton("Validar Productos")
        self.btn_dispensar = QPushButton("Dispensar Receta Magistral")

        self.btn_validar_productos.clicked.connect(self.validar_productos)
        self.btn_dispensar.clicked.connect(self.dispensar_receta)

        layout_acciones.addWidget(self.btn_validar_productos)
        layout_acciones.addWidget(self.btn_dispensar)
        layout_acciones.addStretch()
        grupo_acciones.setLayout(layout_acciones)

        fila_3.addWidget(grupo_recetas, 3)
        fila_3.addWidget(grupo_acciones, 1)

        # Agregar layouts principales
        layout_principal.addLayout(fila_1, 2)
        layout_principal.addWidget(grupo_insumos, 3)
        layout_principal.addLayout(fila_3, 2)

    # ==================================================
    # LÓGICA DE NEGOCIO Y CONEXIONES API
    # ==================================================

    def _actualizar_bloqueo_pantalla(self):
        """
        Bloquea todas las opciones operativas hasta que el código de
        empleado sea validado. Solo el campo y el botón de ingreso de
        código quedan habilitados antes de eso.
        """
        habilitado = self.codigo_validado
        self.tabla_insumos.setEnabled(habilitado)
        self.btn_validar_productos.setEnabled(habilitado)
        self.btn_dispensar.setEnabled(habilitado)
        self.tabla_ordenes.setEnabled(habilitado)
        self.tabla_recetas.setEnabled(habilitado)

        if habilitado:
            self.lbl_estado_codigo.setText("Código validado. Pantalla desbloqueada.")
            self.lbl_estado_codigo.setStyleSheet("color: green;")
        else:
            self.lbl_estado_codigo.setText("Pantalla bloqueada hasta validar el código.")
            self.lbl_estado_codigo.setStyleSheet("color: #B85C00;")

    def ingresar_codigo_empleado(self):
        codigo = self.input_codigo.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Validación", "Debe ingresar su código de empleado.")
            return

        res = ClienteOperaciones.validar_credencial_empleado(codigo)
        if res["exito"]:
            self.codigo_actual = codigo
            self.codigo_validado = True
            self._actualizar_bloqueo_pantalla()
        else:
            self.codigo_validado = False
            self._actualizar_bloqueo_pantalla()
            QMessageBox.critical(self, "Código inválido", f"{res.get('error')}")

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

        # Si la receta que estaba seleccionada ya no está en espera (porque
        # avanzó a elaboración), se limpia el detalle de insumos.
        if self.receta_seleccionada and self.receta_seleccionada.get("estado") != "EN_ESPERA":
            self._limpiar_detalle_insumos()

    def seleccionar_receta_espera(self):
        fila_sel = self.tabla_ordenes.currentRow()
        if fila_sel < 0 or fila_sel >= len(self.recetas_espera):
            return

        self.receta_seleccionada = self.recetas_espera[fila_sel]
        self.insumos_receta_actual = self.receta_seleccionada.get("insumos_requeridos", [])

        self.lbl_descripcion_receta.setText(
            f"Receta {self.receta_seleccionada.get('tipo', '')}: {self.receta_seleccionada.get('descripcion', '')}"
        )

        self.tabla_insumos.setRowCount(len(self.insumos_receta_actual))
        for fila, insumo in enumerate(self.insumos_receta_actual):
            nombre = insumo.get("producto", {}).get("nombre", "Desconocido")
            cantidad = insumo.get("cantidad_requerida", 0)
            cubierto = insumo.get("cubierto", False)

            self.tabla_insumos.setItem(fila, 0, QTableWidgetItem(str(nombre)))
            self.tabla_insumos.setItem(fila, 1, QTableWidgetItem(str(cantidad)))

            estado_texto = "Reservado" if cubierto else "Pendiente"
            self.tabla_insumos.setItem(fila, 2, QTableWidgetItem(estado_texto))

            boton = QPushButton("Reservar")
            boton.setEnabled(not cubierto)
            producto_id = insumo.get("producto_id")
            receta_id = self.receta_seleccionada.get("id")
            boton.clicked.connect(
                lambda _, pid=producto_id, rid=receta_id, cant=cantidad: self.reservar_insumo(rid, pid, cant)
            )
            self.tabla_insumos.setCellWidget(fila, 3, boton)

    def _limpiar_detalle_insumos(self):
        self.receta_seleccionada = None
        self.insumos_receta_actual = []
        self.tabla_insumos.setRowCount(0)
        self.lbl_descripcion_receta.setText("Seleccione una receta de la cola para ver el detalle.")

    def reservar_insumo(self, receta_id, producto_id, cantidad):
        if not self.codigo_validado:
            QMessageBox.warning(self, "Validación", "Primero debe ingresar su código de empleado.")
            return

        res = ClienteOperaciones.iniciar_manufactura_por_producto(receta_id, producto_id, cantidad, self.codigo_actual)
        if res["exito"]:
            datos = res["datos"]
            QMessageBox.information(
                self, "Insumo Reservado",
                f"El lote {datos.get('codigo_lote')} fue reservado exitosamente "
                f"por 15 minutos para la elaboración de la receta magistral."
            )
            # El stock recién cambió: se refresca automáticamente.
            self.cargar_recetas()
            self.seleccionar_receta_espera_por_id(receta_id)
        else:
            if res.get("codigo_error") == "FIRMA_INVALIDA":
                self.codigo_validado = False
                self._actualizar_bloqueo_pantalla()
            QMessageBox.critical(self, "No se pudo reservar el insumo", f"{res.get('error')}")

    def seleccionar_receta_espera_por_id(self, receta_id):
        """Re-selecciona en la tabla la misma receta tras refrescar la cola, para no perder el contexto visual."""
        for fila, rec in enumerate(self.recetas_espera):
            if rec.get("id") == receta_id:
                self.tabla_ordenes.setCurrentCell(fila, 0)
                return
        self._limpiar_detalle_insumos()

    def validar_productos(self):
        if not self.codigo_validado:
            QMessageBox.warning(self, "Validación", "Primero debe ingresar su código de empleado.")
            return

        if not self.receta_seleccionada:
            QMessageBox.warning(self, "Validación", "Seleccione una receta de la cola en espera.")
            return

        id_receta = self.receta_seleccionada.get("id")

        res = ClienteOperaciones.generar_ticket_receta(id_receta)
        if res["exito"]:
            QMessageBox.information(
                self, "Elaboración exitosa",
                "Todos los productos fueron validados correctamente.\n"
                "La receta magistral está lista para dispensación."
            )
            self._limpiar_detalle_insumos()
            self.cargar_recetas()
        else:
            QMessageBox.critical(self, "Control sanitario fallido", f"{res.get('error')}")
            self.cargar_recetas()  # Recargar en caso de que se haya descartado por falta de stock

    def dispensar_receta(self):
        if not self.codigo_validado:
            QMessageBox.warning(self, "Validación", "Primero debe ingresar su código de empleado.")
            return

        fila_sel = self.tabla_recetas.currentRow()
        if fila_sel < 0 or fila_sel >= len(self.recetas_elaboracion):
            QMessageBox.warning(self, "Validación", "Seleccione una receta en elaboración de la tabla correspondiente.")
            return

        receta = self.recetas_elaboracion[fila_sel]
        id_receta = receta.get("id")

        res = ClienteOperaciones.dispensar_receta(id_receta)
        if res["exito"]:
            QMessageBox.information(
                self, "Pedido completado",
                "La receta magistral fue dispensada. El cliente completó su pedido."
            )
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