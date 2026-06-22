from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QMessageBox,
)
from api.cliente_operaciones import ClienteOperaciones


class ProcesarOrdenView(QWidget):
    def __init__(self, id_venta, callback_exito=None):
        super().__init__()

        self.id_venta = id_venta
        self.callback_exito = callback_exito

        self.setWindowTitle("Facturar / Procesar Orden")
        self.resize(400, 350)

        layout = QVBoxLayout()

        # Checkbox requiere receta
        self.chk_receta = QCheckBox("La orden contiene medicamentos bajo receta médica / magistral")
        self.chk_receta.stateChanged.connect(self.alternar_campos_receta)

        # Campos de receta (inicialmente deshabilitados)
        self.lbl_tipo = QLabel("Tipo de Receta")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["RETENIDA", "MAGISTRAL", "CHEQUE"])

        self.lbl_desc = QLabel("Descripción de la Receta / Indicaciones Médicas")
        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("Ej: Receta médica firmada por Dr. Gómez / Amoxicilina 500mg")

        # Botón
        self.btn_procesar = QPushButton("Finalizar y Facturar")

        layout.addWidget(self.chk_receta)
        layout.addWidget(self.lbl_tipo)
        layout.addWidget(self.cmb_tipo)
        layout.addWidget(self.lbl_desc)
        layout.addWidget(self.input_desc)
        layout.addStretch()
        layout.addWidget(self.btn_procesar)

        self.setLayout(layout)

        # Estado inicial de campos
        self.alternar_campos_receta()

        self.btn_procesar.clicked.connect(self.procesar_orden)

    def alternar_campos_receta(self):
        req_receta = self.chk_receta.isChecked()
        self.lbl_tipo.setVisible(req_receta)
        self.cmb_tipo.setVisible(req_receta)
        self.lbl_desc.setVisible(req_receta)
        self.input_desc.setVisible(req_receta)

    def procesar_orden(self):
        req_receta = self.chk_receta.isChecked()
        tipo_receta = self.cmb_tipo.currentText() if req_receta else None
        desc_receta = self.input_desc.text().strip() if req_receta else None

        if req_receta and not desc_receta:
            QMessageBox.warning(self, "Validación", "Debe describir los datos de la receta médica.")
            return

        payload = {
            "requiere_receta": req_receta,
            "tipo_receta": tipo_receta,
            "descripcion_receta": desc_receta
        }

        res = ClienteOperaciones.finalizar_venta(self.id_venta, payload)
        if res["exito"]:
            datos = res["datos"]
            msg = "Venta facturada exitosamente."
            if datos.get("derivado_a_recetas"):
                msg += "\n[Receta Magistral] Derivado automáticamente a la cola del Auxiliar Diplomado."
            QMessageBox.information(self, "Éxito", msg)
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo facturar la orden:\n{res.get('error')}")
