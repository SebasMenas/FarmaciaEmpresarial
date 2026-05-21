import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLineEdit,
    QPushButton,QFormLayout,
    QMessageBox
)

#Version Ultra Minimalista

class FormularioUser(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Formulario de Usuario")

        # Crear layout de formulario
        layout = QFormLayout()

        # Campos
        self.nombre    = QLineEdit()

        # Botón
        self.boton = QPushButton("Guardar")
        self.boton.clicked.connect(self.guardar)

        # Agregar al layout
        layout.addRow("Nombre:", self.nombre)
        layout.addRow(self.boton)

        self.setLayout(layout)

    def guardar(self):
        nombre = self.nombre.text()
        docente = self.docente.text()
        asunto = self.asunto.text()
        fecha = self.fecha.date()

        if not nombre or not docente:
            QMessageBox.warning(self, "Error", "Campos obligatorios vacíos")
            return

        # Obtener valores de fecha
        anio = fecha.year()
        mes = fecha.month()
        dia = fecha.day()

        QMessageBox.information(
            self,
            "Guardado",
            f"Cita para {nombre}\nDocente: {docente}\nFecha: {dia}/{mes}/{anio}\nAsunto: {asunto}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = FormularioUser()
    ventana.show()
    sys.exit(app.exec())