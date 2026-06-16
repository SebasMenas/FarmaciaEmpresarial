from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox,
    QHeaderView
)


class OrdenesView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestión de Órdenes")
        self.resize(1400, 800)

        self.inicializar_ui()

    def inicializar_ui(self):

        layout_principal = QHBoxLayout(self)

        # =====================================
        # COLUMNA IZQUIERDA
        # =====================================

        panel_botones = QVBoxLayout()

        self.btn_nueva_orden = QPushButton("Nueva Orden")
        self.btn_procesar = QPushButton("Procesar Orden")
        self.btn_refrescar = QPushButton("Refrescar")

        panel_botones.addWidget(self.btn_nueva_orden)
        panel_botones.addWidget(self.btn_procesar)
        panel_botones.addWidget(self.btn_refrescar)

        panel_botones.addStretch()

        # =====================================
        # COLUMNA DERECHA
        # =====================================

        panel_tablas = QVBoxLayout()

        # -------------------------------------
        # TABLA 1: ÓRDENES
        # -------------------------------------

        grupo_ordenes = QGroupBox("Órdenes Pendientes")

        layout_ordenes = QVBoxLayout()

        self.tabla_ordenes = QTableWidget()
        self.tabla_ordenes.setColumnCount(4)

        self.tabla_ordenes.setHorizontalHeaderLabels([
            "Número Orden",
            "Id Cliente",
            "Orden",
            "Hora Ingreso"
        ])

        header = self.tabla_ordenes.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        layout_ordenes.addWidget(self.tabla_ordenes)
        grupo_ordenes.setLayout(layout_ordenes)

        # -------------------------------------
        # TABLA 2: INVENTARIO
        # -------------------------------------

        grupo_productos = QGroupBox(
            "Inventario Disponible"
        )

        layout_productos = QVBoxLayout()

        self.tabla_productos = QTableWidget()

        self.tabla_productos.setColumnCount(7)

        self.tabla_productos.setHorizontalHeaderLabels([
            "Nombre",
            "Producto/Lab",
            "Temp °C",
            "Fecha Cad",
            "Estado",
            "Stock",
            "Cant Selec"
        ])

        self.tabla_productos.horizontalHeader()\
            .setSectionResizeMode(
                QHeaderView.Stretch
            )

        layout_productos.addWidget(
            self.tabla_productos
        )

        grupo_productos.setLayout(
            layout_productos
        )

        # -------------------------------------

        panel_tablas.addWidget(
            grupo_ordenes,
            2
        )

        panel_tablas.addWidget(
            grupo_productos,
            1
        )

        # =====================================

        layout_principal.addLayout(
            panel_botones,
            1
        )

        layout_principal.addLayout(
            panel_tablas,
            5
        )

        self.cargar_datos_prueba()

    def cargar_datos_prueba(self):

        # Órdenes

        ordenes = [
            (
                "0001",
                "CLI-101",
                "Paracetamol x10, Ibuprofeno x5, Suero x2",
                "07/06/26"
            ),
            (
                "0002",
                "CLI-205",
                "Insulina x2, Jeringas x20",
                "07/06/26"
            )
        ]

        self.tabla_ordenes.setRowCount(
            len(ordenes)
        )

        for fila, orden in enumerate(ordenes):

            for col, valor in enumerate(orden):

                self.tabla_ordenes.setItem(
                    fila,
                    col,
                    QTableWidgetItem(valor)
                )

        # Inventario

        productos = [
            (
                "Paracetamol",
                "Bayer",
                "22",
                "10/12/26",
                "Disponible",
                "120",
                "0"
            ),
            (
                "Insulina",
                "Novo Nordisk",
                "4",
                "15/09/26",
                "Disponible",
                "30",
                "0"
            ),
            (
                "Vacuna A",
                "Pfizer",
                "2",
                "20/01/27",
                "Disponible",
                "60",
                "0"
            )
        ]

        self.tabla_productos.setRowCount(
            len(productos)
        )

        for fila, producto in enumerate(productos):

            for col, valor in enumerate(producto):

                self.tabla_productos.setItem(
                    fila,
                    col,
                    QTableWidgetItem(valor)
                )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = OrdenesView()
    ventana.show()

    sys.exit(app.exec())