import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, , QFormLayout,
    QMessageBox, QDateEdit,QCalendarWidget,QTimeEdit,QSpinBox
    ,QComboBox
)
from PySide6.QtCore import QDate


class FormularioUser(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Formulario de Usuario")

        # Crear layout de formulario
        layout = QFormLayout()

        # Campos
        self.nombre    = QLineEdit()
        self.apellidos = QLineEdit()
        self.rut       = QLineEdit()
        self.fechaN    = QDateEdit()
        self.sexo      = QComboBox()
        self.test      = QLineEdit()

        self.fecha = QDateEdit()
        self.calendario = QCalendarWidget()
        
        self.sexo.addItems(["---","Hombre","Mujer"])
        
        #self.fecha.setCalendarPopup(True)
        self.fecha.setDate(QDate.currentDate())
        self.calendario.clicked.connect(self.fecha.setDate)
        self.hora = QTimeEdit()
        self.hora.setDisplayFormat("HH:mm")
        


        # Botón
        self.boton = QPushButton("Guardar")
        self.boton.clicked.connect(self.guardar)
        self.fecha.dateChanged.connect(self.calendario.setSelectedDate)

        # Agregar al layout
        layout.addRow("Nombre:", self.nombre)
        layout.addRow("Apellidos:", self.apellidos)
        layout.addRow("Rut:", self.rut)
        layout.addRow("Sexo:", self.sexo)
        layout.addRow("FechaNacimiento:", self.fecha)
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