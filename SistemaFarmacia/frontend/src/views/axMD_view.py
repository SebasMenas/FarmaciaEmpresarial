from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCalendarWidget, QGroupBox,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLabel,
    QComboBox, QLineEdit,
    QHeaderView
)

from PySide6.QtCharts import (
    QChart,
    QChartView,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis
)

from PySide6.QtCore import Qt


class auxMayor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Supervisor de Inventario"
        )

        self.resize(1600, 900)

        self.inicializar_ui()

    def inicializar_ui(self):

        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA 1
        # ==================================================

        fila_1 = QHBoxLayout()

        # ------------------------------------------
        # Calendario
        # ------------------------------------------

        grupo_cal = QGroupBox(
            "Seleccionar Fecha"
        )

        layout_cal = QVBoxLayout()

        self.calendario = QCalendarWidget()

        layout_cal.addWidget(
            self.calendario
        )

        grupo_cal.setLayout(
            layout_cal
        )

        # ------------------------------------------
        # Formulario tareas
        # ------------------------------------------

        grupo_form = QGroupBox(
            "Asignar Tarea"
        )

        layout_form = QVBoxLayout()

        self.cmb_empleado = QComboBox()

        self.cmb_empleado.addItems([
            "Juan Pérez",
            "Ana Soto",
            "Carlos Díaz"
        ])

        self.input_tarea = QLineEdit()

        self.input_tarea.setPlaceholderText(
            "Descripción tarea"
        )

        self.btn_asignar = QPushButton(
            "Asignar"
        )

        layout_form.addWidget(
            QLabel("Empleado")
        )

        layout_form.addWidget(
            self.cmb_empleado
        )

        layout_form.addWidget(
            QLabel("Tarea")
        )

        layout_form.addWidget(
            self.input_tarea
        )

        layout_form.addWidget(
            self.btn_asignar
        )

        grupo_form.setLayout(
            layout_form
        )

        # ------------------------------------------
        # Tabla tareas
        # ------------------------------------------

        grupo_tareas = QGroupBox(
            "Tareas Asignadas"
        )

        layout_tareas = QVBoxLayout()

        self.tabla_tareas = QTableWidget()

        self.tabla_tareas.setColumnCount(4)

        self.tabla_tareas.setHorizontalHeaderLabels([
            "Empleado",
            "Tarea Asignada",
            "Fecha",
            "CheckList"
        ])

        self.tabla_tareas.horizontalHeader()\
            .setSectionResizeMode(
                QHeaderView.Stretch
            )

        layout_tareas.addWidget(
            self.tabla_tareas
        )

        grupo_tareas.setLayout(
            layout_tareas
        )

        fila_1.addWidget(
            grupo_cal, 2
        )

        fila_1.addWidget(
            grupo_form, 1
        )

        fila_1.addWidget(
            grupo_tareas, 3
        )

        # ==================================================
        # FILA 2
        # ==================================================

        fila_2 = QHBoxLayout()

        # ------------------------------------------
        # Gráfico
        # ------------------------------------------

        grupo_grafico = QGroupBox(
            "Capacidad de Almacenamiento"
        )

        layout_grafico = QVBoxLayout()

        barras = QBarSet("Capacidad")

        barras.append([
            65,  # refrigeración
            80   # ambiente
        ])

        serie = QBarSeries()
        serie.append(barras)

        chart = QChart()
        chart.addSeries(serie)

        categorias = [
            "Espacio Refrigeración (%)",
            "Espacio Ambiente (%)"
        ]

        eje_x = QBarCategoryAxis()
        eje_x.append(categorias)

        chart.addAxis(
            eje_x,
            Qt.AlignBottom
        )

        serie.attachAxis(
            eje_x
        )

        eje_y = QValueAxis()
        eje_y.setRange(0, 100)

        chart.addAxis(
            eje_y,
            Qt.AlignLeft
        )

        serie.attachAxis(
            eje_y
        )

        chart.setTitle(
            "Uso de Capacidad"
        )

        grafico = QChartView(chart)

        layout_grafico.addWidget(
            grafico
        )

        grupo_grafico.setLayout(
            layout_grafico
        )

        # ------------------------------------------
        # Form inventario
        # ------------------------------------------

        grupo_inventario = QGroupBox(
            "Modificar Inventario"
        )

        layout_inv = QVBoxLayout()

        self.cmb_producto = QComboBox()

        self.cmb_producto.addItems([
            "Paracetamol",
            "Ibuprofeno",
            "Insulina"
        ])

        self.input_ubicacion = QLineEdit()

        self.input_ubicacion.setPlaceholderText(
            "Ubicación"
        )

        self.btn_actualizar = QPushButton(
            "Actualizar"
        )

        layout_inv.addWidget(
            QLabel("Producto")
        )

        layout_inv.addWidget(
            self.cmb_producto
        )

        layout_inv.addWidget(
            QLabel("Ubicación")
        )

        layout_inv.addWidget(
            self.input_ubicacion
        )

        layout_inv.addWidget(
            self.btn_actualizar
        )

        grupo_inventario.setLayout(
            layout_inv
        )

        # ------------------------------------------
        # Tabla inventario
        # ------------------------------------------

        grupo_stock = QGroupBox(
            "Inventario Actual"
        )

        layout_stock = QVBoxLayout()

        self.tabla_stock = QTableWidget()

        self.tabla_stock.setColumnCount(6)

        self.tabla_stock.setHorizontalHeaderLabels([
            "Nombre Producto/Lab",
            "Temp °C",
            "FechaCad",
            "Estado",
            "CodTraz",
            "Stock"
        ])

        self.tabla_stock.horizontalHeader()\
            .setSectionResizeMode(
                QHeaderView.Stretch
            )

        layout_stock.addWidget(
            self.tabla_stock
        )

        grupo_stock.setLayout(
            layout_stock
        )

        fila_2.addWidget(
            grupo_grafico, 2
        )

        fila_2.addWidget(
            grupo_inventario, 1
        )

        fila_2.addWidget(
            grupo_stock, 3
        )

        # ==================================================

        layout_principal.addLayout(
            fila_1
        )

        layout_principal.addLayout(
            fila_2
        )

        self.cargar_datos_prueba()

    def cargar_datos_prueba(self):

        datos = [
            (
                "Paracetamol\nBayer",
                "22",
                "10/12/26",
                "Disponible",
                "TRZ001",
                "120"
            ),
            (
                "Insulina\nNovo Nordisk",
                "4",
                "15/09/26",
                "Disponible",
                "TRZ002",
                "35"
            ),
            (
                "Vacuna A\nPfizer",
                "2",
                "20/01/27",
                "Disponible",
                "TRZ003",
                "60"
            )
        ]

        self.tabla_stock.setRowCount(
            len(datos)
        )

        for fila, producto in enumerate(datos):

            for col, valor in enumerate(producto):

                self.tabla_stock.setItem(
                    fila,
                    col,
                    QTableWidgetItem(valor)
                )

if __name__ == "__main__":

    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = auxMayor()
    ventana.show()

    sys.exit(app.exec())