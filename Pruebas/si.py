import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCalendarWidget, QSizePolicy

class Ventana(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.calendario = QCalendarWidget()
        self.calendario.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.calendario)

        self.setLayout(layout)

app = QApplication(sys.argv)
ventana = Ventana()
ventana.resize(400, 300)
ventana.show()
sys.exit(app.exec())

