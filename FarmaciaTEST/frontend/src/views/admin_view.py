from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox,
    QHeaderView
)


class AdminView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Personal e Inventario")
        self.resize(1400, 800)

        self.inicializar_ui()

    def inicializar_ui(self):
        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA SUPERIOR
        # ==================================================
        fila_superior = QHBoxLayout()

        # ----------------------------------------
        # TABLA EMPLEADOS
        # ----------------------------------------
        grupo_empleados = QGroupBox("Empleados")
        layout_empleados = QVBoxLayout()

        self.tabla_empleados = QTableWidget()
        self.tabla_empleados.setColumnCount(4)
        self.tabla_empleados.setHorizontalHeaderLabels([
            "Nombres",
            "Apellidos",
            "Rol",
            "Acción"
        ])

        self.tabla_empleados.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout_empleados.addWidget(self.tabla_empleados)
        grupo_empleados.setLayout(layout_empleados)

        # ----------------------------------------
        # TABLA PRODUCTOS
        # ----------------------------------------
        grupo_productos = QGroupBox("Productos")
        layout_productos = QVBoxLayout()

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(5)
        self.tabla_productos.setHorizontalHeaderLabels([
            "Laboratorio",
            "Código Lote",
            "Código Trazabilidad",
            "Fecha Ingreso",
            "Acción"
        ])

        self.tabla_productos.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout_productos.addWidget(self.tabla_productos)
        grupo_productos.setLayout(layout_productos)

        fila_superior.addWidget(grupo_empleados)
        fila_superior.addWidget(grupo_productos)

        # ==================================================
        # FILA INFERIOR
        # ==================================================
        fila_inferior = QHBoxLayout()

        # ----------------------------------------
        # FORMULARIO EMPLEADO
        # ----------------------------------------
        grupo_empleado = QGroupBox("Registrar Empleado")
        layout_empleado = QVBoxLayout()

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre")

        self.input_apellido = QLineEdit()
        self.input_apellido.setPlaceholderText("Apellido")

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems([
            "Administrador",
            "Supervisor",
            "Empleado"
        ])

        self.btn_agregar_empleado = QPushButton("Agregar Empleado")

        layout_empleado.addWidget(QLabel("Nombre"))
        layout_empleado.addWidget(self.input_nombre)

        layout_empleado.addWidget(QLabel("Apellido"))
        layout_empleado.addWidget(self.input_apellido)

        layout_empleado.addWidget(QLabel("Rol"))
        layout_empleado.addWidget(self.cmb_rol)

        layout_empleado.addWidget(self.btn_agregar_empleado)

        grupo_empleado.setLayout(layout_empleado)

        # ----------------------------------------
        # FORMULARIO SOLICITAR PRODUCTO
        # ----------------------------------------
        grupo_solicitud = QGroupBox("Solicitar Producto")
        layout_solicitud = QVBoxLayout()

        self.input_lab_nuevo = QLineEdit()
        self.input_lab_nuevo.setPlaceholderText("Laboratorio")

        self.input_lote_nuevo = QLineEdit()
        self.input_lote_nuevo.setPlaceholderText("Código de lote")

        self.input_trazabilidad_nuevo = QLineEdit()
        self.input_trazabilidad_nuevo.setPlaceholderText(
            "Código de trazabilidad"
        )

        self.btn_solicitar_producto = QPushButton(
            "Solicitar Producto"
        )

        layout_solicitud.addWidget(QLabel("Laboratorio"))
        layout_solicitud.addWidget(self.input_lab_nuevo)

        layout_solicitud.addWidget(QLabel("Código de lote"))
        layout_solicitud.addWidget(self.input_lote_nuevo)

        layout_solicitud.addWidget(QLabel("Código trazabilidad"))
        layout_solicitud.addWidget(self.input_trazabilidad_nuevo)

        layout_solicitud.addWidget(self.btn_solicitar_producto)

        grupo_solicitud.setLayout(layout_solicitud)

        # ----------------------------------------
        # FORMULARIO REABASTECER
        # ----------------------------------------
        grupo_reabastecer = QGroupBox("Reabastecer Producto")
        layout_reabastecer = QVBoxLayout()

        self.cmb_productos = QComboBox()

        self.input_cantidad = QLineEdit()
        self.input_cantidad.setPlaceholderText(
            "Cantidad a ingresar"
        )

        self.btn_reabastecer = QPushButton(
            "Reabastecer"
        )

        layout_reabastecer.addWidget(QLabel("Producto"))
        layout_reabastecer.addWidget(self.cmb_productos)

        layout_reabastecer.addWidget(QLabel("Cantidad"))
        layout_reabastecer.addWidget(self.input_cantidad)

        layout_reabastecer.addWidget(self.btn_reabastecer)

        grupo_reabastecer.setLayout(layout_reabastecer)

        fila_inferior.addWidget(grupo_empleado)
        fila_inferior.addWidget(grupo_solicitud)
        fila_inferior.addWidget(grupo_reabastecer)

        # ==================================================
        # AGREGAR FILAS AL LAYOUT PRINCIPAL
        # ==================================================
        layout_principal.addLayout(fila_superior, 2)
        layout_principal.addLayout(fila_inferior, 1)

        # ==================================================
        # DATOS DE PRUEBA
        # ==================================================
        self.cargar_datos_prueba()

    def cargar_datos_prueba(self):

        # Empleados
        empleados = [
            ("Juan", "Pérez", "Supervisor"),
            ("Ana", "González", "Empleado"),
            ("Carlos", "Rojas", "Administrador")
        ]

        self.tabla_empleados.setRowCount(len(empleados))

        for fila, emp in enumerate(empleados):
            self.tabla_empleados.setItem(
                fila, 0, QTableWidgetItem(emp[0])
            )
            self.tabla_empleados.setItem(
                fila, 1, QTableWidgetItem(emp[1])
            )
            self.tabla_empleados.setItem(
                fila, 2, QTableWidgetItem(emp[2])
            )

            btn_citar = QPushButton("Citar")
            self.tabla_empleados.setCellWidget(
                fila, 3, btn_citar
            )

        # Productos
        productos = [
            ("Pfizer", "LOT001", "TRZ001", "07/06/26"),
            ("Bayer", "LOT002", "TRZ002", "05/06/26"),
            ("Roche", "LOT003", "TRZ003", "01/06/26")
        ]

        self.tabla_productos.setRowCount(len(productos))

        for fila, prod in enumerate(productos):

            for columna, valor in enumerate(prod):
                self.tabla_productos.setItem(
                    fila,
                    columna,
                    QTableWidgetItem(valor)
                )

            btn_eliminar = QPushButton("Eliminar")
            self.tabla_productos.setCellWidget(
                fila,
                4,
                btn_eliminar
            )

            self.cmb_productos.addItem(
                f"{prod[0]} - {prod[1]}"
            )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = AdminView()
    ventana.show()

    sys.exit(app.exec())