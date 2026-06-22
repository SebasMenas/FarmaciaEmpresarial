from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from api.cliente_operaciones import ClienteOperaciones


class ElaborarRecetaView(QWidget):
    def __init__(self, lotes, pin_predeterminado=None, callback_exito=None):
        super().__init__()

        self.lotes = lotes
        self.callback_exito = callback_exito

        self.setWindowTitle("Elaborar Receta - Bloquear Lote")
        self.resize(400, 300)

        layout = QVBoxLayout()

        # Selector de lote
        self.cmb_lotes = QComboBox()
        self.cargar_lotes_combo()

        # PIN
        self.input_pin = QLineEdit()
        self.input_pin.setPlaceholderText("PIN de Operación")
        self.input_pin.setEchoMode(QLineEdit.Password)
        if pin_predeterminado:
            self.input_pin.setText(pin_predeterminado)

        # Botón
        self.btn_elaborar = QPushButton("Reservar Lote para Manufactura")

        layout.addWidget(QLabel("Seleccionar Lote del Insumo"))
        layout.addWidget(self.cmb_lotes)

        layout.addWidget(QLabel("Credencial de empleador"))
        layout.addWidget(self.input_pin)

        layout.addStretch()
        layout.addWidget(self.btn_elaborar)

        self.setLayout(layout)

        self.btn_elaborar.clicked.connect(self.elaborar)

    def cargar_lotes_combo(self):
        self.cmb_lotes.clear()
        for lote in self.lotes:
            if lote.get("estado") == "DISPONIBLE":
                prod_name = lote.get("producto", {}).get("nombre", "Desconocido")
                lote_cod = lote.get("codigo_lote", "")
                cant = lote.get("cantidad", 0)
                self.cmb_lotes.addItem(f"{prod_name} (Lote: {lote_cod} | Stock: {cant})", lote.get("id"))

    def elaborar(self):
        lote_id = self.cmb_lotes.currentData()
        pin = self.input_pin.text().strip()

        if not lote_id:
            QMessageBox.warning(self, "Validación", "No hay lotes disponibles para seleccionar.")
            return

        if not pin:
            QMessageBox.warning(self, "Validación", "Debe ingresar su PIN para firmar la operación.")
            return

        res = ClienteOperaciones.iniciar_manufactura(lote_id, pin)
        if res["exito"]:
            datos = res["datos"]
            msg = f"El lote {datos.get('codigo_lote')} ha sido bloqueado exitosamente en el backend por 15 minutos para manufactura magistral."
            if datos.get("lote_reasignado"):
                msg += f"\n\n[Concurrencia] El lote seleccionado estaba ocupado; se reservó automáticamente el lote alternativo: {datos.get('codigo_lote')}"
            QMessageBox.information(self, "Lote Reservado", msg)
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error de Validación", f"No se pudo reservar el lote:\n{res.get('error')}")
