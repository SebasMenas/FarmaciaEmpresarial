from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCalendarWidget,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QComboBox,
    QLineEdit,
    QHeaderView,
    QMessageBox,
    QCheckBox,
)

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis
)

from PySide6.QtCore import Qt, QDate
from api.AdminConsultas import ClienteMonitoreo, ClienteOperaciones


class auxMayor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Supervisor de Inventario - Auxiliar Mayor")
        self.resize(1600, 900)

        self.lotes_cargados = []
        self.lote_seleccionado_id = None

        self.inicializar_ui()
        self.cargar_datos_iniciales()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA 1: AGENDA Y TAREAS
        # ==================================================
        fila_1 = QHBoxLayout()

        # 1. Calendario
        grupo_cal = QGroupBox("Seleccionar Fecha")
        layout_cal = QVBoxLayout()
        self.calendario = QCalendarWidget()
        layout_cal.addWidget(self.calendario)
        grupo_cal.setLayout(layout_cal)

        # 2. Formulario Asignar Tarea
        grupo_form = QGroupBox("Asignar Tarea")
        layout_form = QVBoxLayout()

        self.cmb_empleado = QComboBox()
        self.input_tarea = QLineEdit()
        self.input_tarea.setPlaceholderText("Descripción tarea")
        self.btn_asignar = QPushButton("Asignar")

        layout_form.addWidget(QLabel("Empleado Responsable"))
        layout_form.addWidget(self.cmb_empleado)
        layout_form.addWidget(QLabel("Instrucción"))
        layout_form.addWidget(self.input_tarea)
        layout_form.addWidget(self.btn_asignar)
        grupo_form.setLayout(layout_form)

        # 3. Tabla Tareas Asignadas
        grupo_tareas = QGroupBox("Tareas Asignadas de la Fecha")
        layout_tareas = QVBoxLayout()
        self.tabla_tareas = QTableWidget()
        self.tabla_tareas.setColumnCount(4)
        self.tabla_tareas.setHorizontalHeaderLabels([
            "Empleado",
            "Tarea Asignada",
            "Fecha",
            "Completada"
        ])
        self.tabla_tareas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_tareas.addWidget(self.tabla_tareas)
        grupo_tareas.setLayout(layout_tareas)

        fila_1.addWidget(grupo_cal, 2)
        fila_1.addWidget(grupo_form, 1)
        fila_1.addWidget(grupo_tareas, 3)

        # ==================================================
        # FILA 2: GRÁFICO, INVENTARIO Y UBICACIÓN
        # ==================================================
        fila_2 = QHBoxLayout()

        # 1. Gráfico Capacidad de Almacenamiento
        grupo_grafico = QGroupBox("Capacidad de Almacenamiento")
        layout_grafico = QVBoxLayout()

        self.chart = QChart()
        self.chart.setTitle("Uso de Capacidad por Zona (%)")
        self.grafico = QChartView(self.chart)
        layout_grafico.addWidget(self.grafico)
        grupo_grafico.setLayout(layout_grafico)

        # 2. Formulario de Ubicación
        grupo_inventario = QGroupBox("Almacenar / Ubicar Lote Físico")
        layout_inv = QVBoxLayout()

        self.txt_lote_seleccionado = QLineEdit()
        self.txt_lote_seleccionado.setReadOnly(True)
        self.txt_lote_seleccionado.setPlaceholderText("Seleccione un lote de la tabla")

        self.cmb_zona_temperatura = QComboBox()
        self.cmb_zona_temperatura.addItem("Zona Ambiente (21°C)", "AMBIENTE")
        self.cmb_zona_temperatura.addItem("Zona Refrigeración (4°C)", "REFRIGERADO")

        self.input_ubicacion = QLineEdit()
        self.input_ubicacion.setPlaceholderText("Ej: Estante A - Nivel 2")

        self.btn_actualizar = QPushButton("Almacenar Lote")

        layout_inv.addWidget(QLabel("Lote Seleccionado"))
        layout_inv.addWidget(self.txt_lote_seleccionado)
        layout_inv.addWidget(QLabel("Zona Ambiental Destino"))
        layout_inv.addWidget(self.cmb_zona_temperatura)
        layout_inv.addWidget(QLabel("Ubicación Física (Coordenada)"))
        layout_inv.addWidget(self.input_ubicacion)
        layout_inv.addWidget(self.btn_actualizar)
        grupo_inventario.setLayout(layout_inv)

        # 3. Tabla Inventario Actual
        grupo_stock = QGroupBox("Inventario de Lotes Disponibles")
        layout_stock = QVBoxLayout()
        self.tabla_stock = QTableWidget()
        self.tabla_stock.setColumnCount(6)
        self.tabla_stock.setHorizontalHeaderLabels([
            "Producto / Lab",
            "Temperatura",
            "Caducidad",
            "Estado",
            "Cod. Trazabilidad",
            "Stock"
        ])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout_stock.addWidget(self.tabla_stock)
        grupo_stock.setLayout(layout_stock)

        fila_2.addWidget(grupo_grafico, 2)
        fila_2.addWidget(grupo_inventario, 1)
        fila_2.addWidget(grupo_stock, 3)

        # Agregar layouts principales
        layout_principal.addLayout(fila_1, 1)
        layout_principal.addLayout(fila_2, 1)

        # Eventos
        self.calendario.selectionChanged.connect(self.cargar_tareas)
        self.btn_asignar.clicked.connect(self.asignar_tarea)
        self.btn_actualizar.clicked.connect(self.almacenar_lote)
        self.tabla_stock.itemSelectionChanged.connect(self.seleccionar_lote_tabla)

    # ==================================================
    # MÉTODOS DE DATOS Y CONEXIONES API
    # ==================================================

    def cargar_datos_iniciales(self):
        self.cargar_empleados()
        self.cargar_grafico()
        self.cargar_inventario()
        self.cargar_tareas()

    def cargar_empleados(self):
        res = ClienteMonitoreo.obtener_empleados()
        if res["exito"]:
            self.cmb_empleado.clear()
            self.empleados = res["datos"]
            for emp in self.empleados:
                nombre_completo = f"{emp.get('nombre')} {emp.get('apellidos')}"
                self.cmb_empleado.addItem(nombre_completo, emp.get("id"))
        else:
            QMessageBox.warning(self, "Advertencia", f"No se pudo cargar la lista de empleados: {res.get('error')}")

    def cargar_grafico(self):
        res = ClienteMonitoreo.obtener_capacidad()
        if not res["exito"]:
            return

        datos_capacidad = res["datos"]
        self.chart.removeAllSeries()
        
        for axis in list(self.chart.axes()):
            self.chart.removeAxis(axis)

        barras = QBarSet("Ocupación actual (%)")
        porc_refrig = 0.0
        porc_amb = 0.0

        for cap in datos_capacidad:
            zona = cap.get("zona")
            max_u = cap.get("capacidad_maxima_unidades", 1) or 1
            act_u = cap.get("ocupacion_actual", 0) or 0
            porcentaje = (act_u / max_u) * 100.0
            if zona == "REFRIGERADO":
                porc_refrig = porcentaje
            elif zona == "AMBIENTE":
                porc_amb = porcentaje

        barras.append([porc_refrig, porc_amb])

        serie = QBarSeries()
        serie.append(barras)
        self.chart.addSeries(serie)

        categorias = [
            "Zona Refrigeración (%)",
            "Zona Ambiente (%)"
        ]
        eje_x = QBarCategoryAxis()
        eje_x.append(categorias)
        self.chart.addAxis(eje_x, Qt.AlignBottom)
        serie.attachAxis(eje_x)

        eje_y = QValueAxis()
        eje_y.setRange(0, 100)
        self.chart.addAxis(eje_y, Qt.AlignLeft)
        serie.attachAxis(eje_y)

    def cargar_inventario(self):
        res = ClienteMonitoreo.obtener_almacenamiento()
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el inventario: {res.get('error')}")
            return

        self.lotes_cargados = res["datos"]
        self.tabla_stock.setRowCount(len(self.lotes_cargados))

        for fila, lote in enumerate(self.lotes_cargados):
            prod_name = lote.get("producto", {}).get("nombre", "Desconocido")
            lab_name = lote.get("laboratorio", {}).get("nombre", "Desconocido")
            temp_str = lote.get("temperatura", "Desconocida")
            
            self.tabla_stock.setItem(fila, 0, QTableWidgetItem(f"{prod_name}\n({lab_name})"))
            self.tabla_stock.setItem(fila, 1, QTableWidgetItem(str(temp_str)))
            self.tabla_stock.setItem(fila, 2, QTableWidgetItem(str(lote.get("fecha_caducidad", ""))))
            self.tabla_stock.setItem(fila, 3, QTableWidgetItem(str(lote.get("estado", ""))))
            self.tabla_stock.setItem(fila, 4, QTableWidgetItem(str(lote.get("codigo_trazabilidad", ""))))
            self.tabla_stock.setItem(fila, 5, QTableWidgetItem(str(lote.get("cantidad", 0))))

    def cargar_tareas(self):
        fecha_qdate = self.calendario.selectedDate()
        fecha_str = fecha_qdate.toString("yyyy-MM-dd")

        res = ClienteMonitoreo.obtener_tareas(fecha_str)
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las tareas: {res.get('error')}")
            return

        tareas = res["datos"]
        self.tabla_tareas.setRowCount(len(tareas))

        for fila, tarea in enumerate(tareas):
            emp = tarea.get("asignado_a", {})
            nombre_emp = f"{emp.get('nombre', '')} {emp.get('apellidos', '')}"

            self.tabla_tareas.setItem(fila, 0, QTableWidgetItem(nombre_emp))
            self.tabla_tareas.setItem(fila, 1, QTableWidgetItem(str(tarea.get("descripcion", ""))))
            self.tabla_tareas.setItem(fila, 2, QTableWidgetItem(str(tarea.get("fecha", ""))))

            # Columna de checklist con checkbox interactivo
            chk = QCheckBox()
            chk.setChecked(tarea.get("completada", False))
            
            # Contenedor centrado para el checkbox
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(chk)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)

            chk.stateChanged.connect(lambda state, tid=tarea.get("id"): self.cambiar_completada_tarea(tid, state))

            self.tabla_tareas.setCellWidget(fila, 3, widget)

    def cambiar_completada_tarea(self, id_tarea, state):
        completada = (state == 2) # Qt.Checked = 2
        res = ClienteMonitoreo.actualizar_tarea_estado(id_tarea, completada)
        if not res["exito"]:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el estado de la tarea: {res.get('error')}")
            self.cargar_tareas()

    def asignar_tarea(self):
        emp_id = self.cmb_empleado.currentData()
        descripcion = self.input_tarea.text().strip()
        fecha_str = self.calendario.selectedDate().toString("yyyy-MM-dd")

        if not emp_id or not descripcion:
            QMessageBox.warning(self, "Validación", "Debe completar la descripción de la tarea.")
            return

        datos_tarea = {
            "descripcion": descripcion,
            "asignado_a_id": emp_id,
            "fecha": fecha_str
        }

        res = ClienteMonitoreo.crear_tarea(datos_tarea)
        if res["exito"]:
            QMessageBox.information(self, "Éxito", "Tarea programada correctamente.")
            self.input_tarea.clear()
            self.cargar_tareas()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo asignar la tarea: {res.get('error')}")

    def seleccionar_lote_tabla(self):
        fila_seleccionada = self.tabla_stock.currentRow()
        if fila_seleccionada >= 0 and fila_seleccionada < len(self.lotes_cargados):
            lote = self.lotes_cargados[fila_seleccionada]
            self.lote_seleccionado_id = lote.get("id")
            prod_name = lote.get("producto", {}).get("nombre", "")
            cod_lote = lote.get("codigo_lote", "")
            self.txt_lote_seleccionado.setText(f"{prod_name} (Lote: {cod_lote})")

            # Intentar pre-seleccionar la zona térmica idónea
            ind_ambiental = lote.get("producto", {}).get("indicacion_ambiental", "AMBIENTE")
            index = self.cmb_zona_temperatura.findData(ind_ambiental)
            if index >= 0:
                self.cmb_zona_temperatura.setCurrentIndex(index)

            self.input_ubicacion.setText(lote.get("ubicacion_almacen") or "")

    def almacenar_lote(self):
        if not self.lote_seleccionado_id:
            QMessageBox.warning(self, "Validación", "Debe seleccionar un lote del inventario.")
            return

        ubicacion = self.input_ubicacion.text().strip()
        zona_temperatura = self.cmb_zona_temperatura.currentData()

        if not ubicacion:
            QMessageBox.warning(self, "Validación", "Debe ingresar una coordenada de ubicación física.")
            return

        datos_ubicacion = {
            "ubicacion": ubicacion,
            "temperatura_zona": zona_temperatura
        }

        res = ClienteOperaciones.almacenar_lote(self.lote_seleccionado_id, datos_ubicacion)
        if res["exito"]:
            QMessageBox.information(self, "Éxito", "Ubicación del lote actualizada correctamente.")
            self.txt_lote_seleccionado.clear()
            self.input_ubicacion.clear()
            self.lote_seleccionado_id = None
            self.cargar_inventario()
            self.cargar_grafico() # Actualizar gráfico de capacidad
        else:
            QMessageBox.critical(self, "Alerta Térmica", f"No se pudo almacenar:\n{res.get('error')}")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    ventana = auxMayor()
    ventana.show()
    sys.exit(app.exec())