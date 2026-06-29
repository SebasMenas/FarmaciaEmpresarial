from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton,
    QMessageBox,
)
from api.AdminConsultas import ClienteMonitoreo


class RecalibrarCapacidadView(QWidget):
    """
    Formulario para que el Admin recalibre manualmente el techo de
    capacidad física de una de las 4 zonas fijas (A, B refrigerado;
    C, D ambiente).

    Las zonas mismas no se crean ni eliminan desde aquí: se autogeneran
    al arrancar el sistema, así que este formulario solo ajusta el
    número de unidades que cada una admite.
    """

    def __init__(self, callback_exito=None):
        super().__init__()

        self.callback_exito = callback_exito
        self.zonas_cargadas = []
        self.setWindowTitle("Recalibrar Capacidad de Zona")
        self.resize(400, 240)

        layout = QVBoxLayout()

        self.cmb_zona = QComboBox()

        self.lbl_capacidad_actual = QLabel("Capacidad actual: —")

        self.spin_nueva_capacidad = QSpinBox()
        self.spin_nueva_capacidad.setRange(1, 1000000)
        self.spin_nueva_capacidad.setValue(1000)

        form = QFormLayout()
        form.addRow("Zona", self.cmb_zona)
        form.addRow(self.lbl_capacidad_actual)
        form.addRow("Nueva capacidad (unidades)", self.spin_nueva_capacidad)

        self.lbl_nota = QLabel(
            "Si la nueva capacidad queda por debajo de la ocupación\n"
            "actual de la zona, los lotes que excedan el límite no se\n"
            "verán afectados de inmediato, pero no se podrán asignar\n"
            "lotes nuevos a esa zona hasta liberar espacio."
        )
        self.lbl_nota.setWordWrap(True)

        self.btn_guardar = QPushButton("Guardar Nueva Capacidad")

        layout.addLayout(form)
        layout.addWidget(self.lbl_nota)
        layout.addStretch()
        layout.addWidget(self.btn_guardar)

        self.setLayout(layout)

        self.btn_guardar.clicked.connect(self.guardar_capacidad)

        # Se carga el catálogo de zonas al final, una vez que todos los
        # widgets (incluido lbl_capacidad_actual, que actualizar_capacidad_actual
        # escribe) ya existen.
        self.cargar_zonas_combo()
        self.cmb_zona.currentIndexChanged.connect(self.actualizar_capacidad_actual)

    def cargar_zonas_combo(self):
        res = ClienteMonitoreo.listar_zonas()
        if not res["exito"]:
            QMessageBox.warning(
                self, "Zonas no disponibles",
                f"No se pudo cargar el catálogo de zonas:\n{res.get('error', '')}"
            )
            return

        self.zonas_cargadas = res["datos"]
        self.cmb_zona.clear()
        for zona in self.zonas_cargadas:
            etiqueta_ambiente = "Refrigerado (4°C)" if zona["tipo_ambiental"] == "REFRIGERADO" else "Ambiente (21°C)"
            etiqueta = f"Zona {zona['codigo']} — {etiqueta_ambiente}"
            self.cmb_zona.addItem(etiqueta, zona["id"])

        self.actualizar_capacidad_actual()

    def actualizar_capacidad_actual(self):
        zona_id = self.cmb_zona.currentData()
        zona = next((z for z in self.zonas_cargadas if z["id"] == zona_id), None)
        if zona:
            self.lbl_capacidad_actual.setText(f"Capacidad actual: {zona['capacidad_maxima_unidades']} unidades")
            self.spin_nueva_capacidad.setValue(zona["capacidad_maxima_unidades"])
        else:
            self.lbl_capacidad_actual.setText("Capacidad actual: —")

    def guardar_capacidad(self):
        zona_id = self.cmb_zona.currentData()
        if not zona_id:
            QMessageBox.warning(self, "Validación", "Debe seleccionar una zona.")
            return

        nueva_capacidad = self.spin_nueva_capacidad.value()

        res = ClienteMonitoreo.recalibrar_capacidad_zona(zona_id, nueva_capacidad)
        if res["exito"]:
            cuerpo = res["datos"]
            QMessageBox.information(
                self, "Capacidad Actualizada",
                f"Zona {cuerpo.get('codigo_zona', '—')} recalibrada a "
                f"{cuerpo.get('nueva_capacidad', nueva_capacidad)} unidades."
            )
            if self.callback_exito:
                self.callback_exito()
            self.close()
        else:
            QMessageBox.critical(self, "Error", str(res.get("error", "No se pudo recalibrar la zona.")))