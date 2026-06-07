from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QTableWidget,
    QTableWidgetItem, QPushButton,
    QLabel, QLineEdit, QComboBox,
    QMessageBox, QHeaderView
)


class RecetasMagistralesView(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Recetas Magistrales")
        self.resize(1400, 800)

        self.ticket_actual = None

        self.inicializar_ui()

    def inicializar_ui(self):

        layout_principal = QVBoxLayout(self)

        # ==================================================
        # FILA 1
        # ==================================================

        fila_1 = QHBoxLayout()

        # -------------------------
        # Verificación
        # -------------------------

        grupo_validacion = QGroupBox(
            "Validación de Credencial"
        )

        layout_validacion = QVBoxLayout()

        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText(
            "Ingrese código"
        )

        self.btn_validar = QPushButton(
            "Validar"
        )

        self.btn_validar.clicked.connect(
            self.validar_credencial
        )

        layout_validacion.addWidget(
            QLabel("Código de Verificación")
        )

        layout_validacion.addWidget(
            self.input_codigo
        )

        layout_validacion.addWidget(
            self.btn_validar
        )

        grupo_validacion.setLayout(
            layout_validacion
        )

        # -------------------------
        # Tabla órdenes
        # -------------------------

        grupo_ordenes = QGroupBox(
            "Órdenes Pendientes"
        )

        layout_ordenes = QVBoxLayout()

        self.tabla_ordenes = QTableWidget()

        self.tabla_ordenes.setColumnCount(5)

        self.tabla_ordenes.setHorizontalHeaderLabels([
            "Número Orden",
            "Id Cliente",
            "Tipo Receta",
            "Hora Ingreso",
            "CheckList"
        ])

        self.tabla_ordenes.horizontalHeader()\
            .setSectionResizeMode(
                QHeaderView.Stretch
            )

        layout_ordenes.addWidget(
            self.tabla_ordenes
        )

        grupo_ordenes.setLayout(
            layout_ordenes
        )

        fila_1.addWidget(
            grupo_validacion,
            1
        )

        fila_1.addWidget(
            grupo_ordenes,
            3
        )

        # ==================================================
        # FILA 2
        # ==================================================

        grupo_recetas = QGroupBox(
            "Recetas Magistrales"
        )

        layout_recetas = QVBoxLayout()

        self.tabla_recetas = QTableWidget()

        self.tabla_recetas.setColumnCount(4)

        self.tabla_recetas.setHorizontalHeaderLabels([
            "Número Orden",
            "Id Cliente",
            "Tipo Receta",
            "Receta"
        ])

        self.tabla_recetas.horizontalHeader()\
            .setSectionResizeMode(
                QHeaderView.Stretch
            )

        layout_recetas.addWidget(
            self.tabla_recetas
        )

        grupo_recetas.setLayout(
            layout_recetas
        )

        # ==================================================
        # FILA 3
        # ==================================================

        grupo_acciones = QGroupBox(
            "Elaboración y Dispensación"
        )

        layout_acciones = QVBoxLayout()

        self.cmb_productos = QComboBox()

        self.cmb_productos.addItems([
            "Paracetamol",
            "Ibuprofeno",
            "Amoxicilina",
            "Insulina"
        ])

        botones = QHBoxLayout()

        self.btn_elaborar = QPushButton(
            "Elaborar Receta Magistral"
        )

        self.btn_ticket = QPushButton(
            "Generar Ticket Validación"
        )

        self.btn_dispensar = QPushButton(
            "Dispensar Receta"
        )

        self.btn_elaborar.clicked.connect(
            self.elaborar_receta
        )

        self.btn_ticket.clicked.connect(
            self.generar_ticket
        )

        self.btn_dispensar.clicked.connect(
            self.dispensar_receta
        )

        botones.addWidget(
            self.btn_elaborar
        )

        botones.addWidget(
            self.btn_ticket
        )

        botones.addWidget(
            self.btn_dispensar
        )

        layout_acciones.addWidget(
            QLabel("Producto")
        )

        layout_acciones.addWidget(
            self.cmb_productos
        )

        layout_acciones.addLayout(
            botones
        )

        grupo_acciones.setLayout(
            layout_acciones
        )

        # ==================================================

        layout_principal.addLayout(
            fila_1
        )

        layout_principal.addWidget(
            grupo_recetas
        )

        layout_principal.addWidget(
            grupo_acciones
        )

        self.cargar_datos_prueba()

    # ==================================================
    # LÓGICA
    # ==================================================

    def validar_credencial(self):

        codigo = self.input_codigo.text().strip()

        if codigo != "ABC123":

            QMessageBox.critical(
                self,
                "Error",
                "Error! credencial no valida"
            )

            return

        QMessageBox.information(
            self,
            "Correcto",
            "Credencial validada"
        )

    def elaborar_receta(self):

        fila = self.tabla_recetas.rowCount()

        self.tabla_recetas.insertRow(
            fila
        )

        self.tabla_recetas.setItem(
            fila,
            0,
            QTableWidgetItem("ORD-001")
        )

        self.tabla_recetas.setItem(
            fila,
            1,
            QTableWidgetItem("CLI-001")
        )

        self.tabla_recetas.setItem(
            fila,
            2,
            QTableWidgetItem("Magistral")
        )

        self.tabla_recetas.setItem(
            fila,
            3,
            QTableWidgetItem(
                self.cmb_productos.currentText()
            )
        )

    def generar_ticket(self):

        self.ticket_actual = "TK-00001"

        QMessageBox.information(
            self,
            "Ticket",
            f"Ticket generado:\n{self.ticket_actual}"
        )

    def dispensar_receta(self):

        producto_en_mal_estado = False

        if producto_en_mal_estado:

            QMessageBox.critical(
                self,
                "Error",
                "Error! Producto utilizado esta en mal estado, orden cancelada"
            )

            return

        QMessageBox.information(
            self,
            "Dispensación",
            "Receta dispensada correctamente"
        )

    # ==================================================

    def cargar_datos_prueba(self):

        ordenes = [
            (
                "ORD-001",
                "CLI-100",
                "Magistral",
                "07/06/26",
                "Pendiente"
            ),
            (
                "ORD-002",
                "CLI-101",
                "Controlada",
                "07/06/26",
                "Pendiente"
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


if __name__ == "__main__":

    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = RecetasMagistralesView()
    ventana.show()

    sys.exit(app.exec())