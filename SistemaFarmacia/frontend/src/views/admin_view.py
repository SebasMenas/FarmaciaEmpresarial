from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QGroupBox,
    QHeaderView, QMessageBox
)
from api.AdminConsultas import ClienteMonitoreo
from api.cliente_auth import ClienteAuth
from forms.empleados_form import RegistroEmpleadoView
from forms.empEdit_form import EditarEmpleadoView
from forms.solicitar_producto_form import SolicitarProductoView
from forms.reabastecer_form import ReabastecerProductoView
from forms.recalibrar_capacidad_form import RecalibrarCapacidadView

class AdminView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Personal e Inventario")
        self.resize(1400, 800)

        self.inicializar_ui()

        self.btn_nuevo_empleado.clicked.connect(
            self.abrir_registro_empleado
        )
        self.btn_solicitar_producto.clicked.connect(
            self.abrir_solicitar_producto
        )
        self.btn_reabastecer.clicked.connect(
            self.abrir_reabastecer_producto
        )
        self.btn_capacidad_zonas.clicked.connect(
            self.abrir_recalibrar_capacidad
        )
        
        self.cargar_empleados()
        self.cargar_productos()
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
        self.tabla_empleados.setColumnCount(5)
        self.tabla_empleados.setHorizontalHeaderLabels([
            "Nombres",
            "Apellidos",
            "Rol",
            "Estado",
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
        # FILA INFERIOR (Acciones de Administración)
        # ==================================================
        grupo_acciones = QGroupBox("Acciones Rápidas de Administración")
        layout_acciones = QHBoxLayout()

        self.btn_nuevo_empleado = QPushButton("Nuevo Empleado")
        self.btn_solicitar_producto = QPushButton("Solicitar Producto")
        self.btn_reabastecer = QPushButton("Reabastecer Producto")
        self.btn_capacidad_zonas = QPushButton("Capacidad de Zonas")

        self.btn_nuevo_empleado.setFixedHeight(40)
        self.btn_solicitar_producto.setFixedHeight(40)
        self.btn_reabastecer.setFixedHeight(40)
        self.btn_capacidad_zonas.setFixedHeight(40)

        layout_acciones.addWidget(self.btn_nuevo_empleado)
        layout_acciones.addWidget(self.btn_solicitar_producto)
        layout_acciones.addWidget(self.btn_reabastecer)
        layout_acciones.addWidget(self.btn_capacidad_zonas)
        grupo_acciones.setLayout(layout_acciones)

        fila_inferior = QHBoxLayout()
        fila_inferior.addWidget(grupo_acciones)

        # ==================================================
        # AGREGAR FILAS AL LAYOUT PRINCIPAL
        # ==================================================
        layout_principal.addLayout(fila_superior, 2)
        layout_principal.addLayout(fila_inferior, 1)

    def cargar_empleados(self):
        res = ClienteMonitoreo.obtener_empleados()

        if not res["exito"]:
            QMessageBox.critical(self, "Error", res["error"])
            return

        self.empleados = res["datos"]
        empleados = self.empleados
        self.tabla_empleados.setRowCount(len(empleados))

        username_actual = ClienteAuth.obtener_username_actual()

        for fila, empleado in enumerate(empleados):
            es_propia_cuenta = empleado.get("username") == username_actual

            nombre_mostrado = str(empleado.get("nombre", ""))
            if es_propia_cuenta:
                nombre_mostrado += "  (mi cuenta)"

            # Casteo explícito a string para evitar TypeErrors con valores nulos
            self.tabla_empleados.setItem(fila, 0, QTableWidgetItem(nombre_mostrado))
            self.tabla_empleados.setItem(fila, 1, QTableWidgetItem(str(empleado.get("apellidos", ""))))
            self.tabla_empleados.setItem(fila, 2, QTableWidgetItem(str(empleado.get("rol", ""))))

            estado_texto = "Activo" if empleado.get("activo", True) else "Desactivado"
            self.tabla_empleados.setItem(fila, 3, QTableWidgetItem(estado_texto))

            boton = QPushButton("Editar")

            if es_propia_cuenta:
                # El backend ya rechaza intentos de auto-desactivación o cambio
                # de rol propio (ver PUT /admin/empleados/{id}); aquí se refleja
                # también en la UI para que no parezca una acción habilitada
                # que luego falla sin explicación.
                boton.setEnabled(False)
                boton.setToolTip("No puede editar su propia cuenta desde aquí (riesgo de autobloqueo).")
            else:
                boton.clicked.connect(
                    lambda _, empleado=empleado:
                        self.abrir_edicion(empleado)
                )

            self.tabla_empleados.setCellWidget(fila, 4, boton)

    def cargar_productos(self):
        res = ClienteMonitoreo.obtener_almacenamiento()

        if not res["exito"]:
            # Opcional: Mostrar error si falla la carga de productos
            # QMessageBox.warning(self, "Advertencia", res.get("error", "Error desconocido"))
            return

        productos = res["datos"]
        self.tabla_productos.setRowCount(len(productos))

        for fila, producto in enumerate(productos):
            # 1. Extracción correcta del diccionario anidado 'laboratorio'
            nombre_lab = producto.get("laboratorio", {}).get("nombre", "Desconocido")
            
            # 2. Casteo explícito a cadena de texto para cada columna
            self.tabla_productos.setItem(fila, 0, QTableWidgetItem(str(nombre_lab)))
            self.tabla_productos.setItem(fila, 1, QTableWidgetItem(str(producto.get("codigo_lote", ""))))
            self.tabla_productos.setItem(fila, 2, QTableWidgetItem(str(producto.get("codigo_trazabilidad", ""))))
            self.tabla_productos.setItem(fila, 3, QTableWidgetItem(str(producto.get("fecha_ingreso", ""))))

            boton = QPushButton("Retirar")
            lote_id = producto.get("id")
            boton.clicked.connect(
                lambda _, lid=lote_id: self.retirar_lote(lid)
            )
            self.tabla_productos.setCellWidget(fila, 4, boton)

    def abrir_registro_empleado(self):
        self.ventana_registro = RegistroEmpleadoView(callback_exito=self.cargar_empleados)
        self.ventana_registro.show()

    def abrir_edicion(self, empleado):
        self.ventana_edicion = EditarEmpleadoView(
            empleado,
            callback_exito=self.cargar_empleados
        )
        self.ventana_edicion.show()

    def abrir_solicitar_producto(self):
        self.ventana_solicitud = SolicitarProductoView(callback_exito=self.cargar_productos)
        self.ventana_solicitud.show()

    def abrir_reabastecer_producto(self):
        self.ventana_reabastecer = ReabastecerProductoView(
            callback_exito=self.cargar_productos
        )
        self.ventana_reabastecer.show()

    def abrir_recalibrar_capacidad(self):
        self.ventana_capacidad = RecalibrarCapacidadView()
        self.ventana_capacidad.show()

    def retirar_lote(self, lote_id):
        confirmar = QMessageBox.question(
            self, "Confirmar Retiro",
            "¿Está seguro de que desea retirar este lote del inventario?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmar == QMessageBox.Yes:
            res = ClienteMonitoreo.cambiar_estado_lote(lote_id, "RETIRADO")
            if res["exito"]:
                QMessageBox.information(self, "Éxito", "Lote marcado como RETIRADO.")
                self.cargar_productos()
            else:
                QMessageBox.critical(self, "Error", res.get("error", "No se pudo retirar el lote."))

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = AdminView()
    ventana.show()

    sys.exit(app.exec())