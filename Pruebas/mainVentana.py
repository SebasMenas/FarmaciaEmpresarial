from PySide6.QtWidgets import (
    QApplication, QWidget,
    QHBoxLayout, QVBoxLayout,
    QPushButton, QCalendarWidget,
    QListWidget, QListWidgetItem,
    QSizePolicy, QLabel, QInputDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class Ventana(QWidget):
    def __init__(self):
        super().__init__()

        # 🔹 Layout general
        self.layout_general = QVBoxLayout()

        # 🏷️ Título
        self.titulo = QLabel("Citas")
        self.titulo.setAlignment(Qt.AlignCenter)

        # 🔹 Layout principal
        self.layout_principal = QHBoxLayout()

        # 📅 Calendario
        self.calendario = QCalendarWidget()
        self.calendario.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 📋 Lista de citas
        self.lista = QListWidget()
        self.lista.setMinimumWidth(220)

        # 🔹 Botones
        self.columna_botones = QVBoxLayout()
        self.botones = [
            self.crear_boton("Agregar", "#28a745"),
            self.crear_boton("Eliminar", "#dc3545")
        ]

        self.columna_botones.addStretch()
        for b in self.botones:
            self.columna_botones.addWidget(b)
        self.columna_botones.addStretch()

        # 🔹 Conexiones
        self.botones[0].clicked.connect(self.agregar_cita)
        self.botones[1].clicked.connect(self.eliminar_cita)

        self.lista.itemClicked.connect(self.seleccionar_cita)
        self.lista.itemDoubleClicked.connect(self.editar_cita)

        # 🔹 Armar layout
        self.layout_principal.addWidget(self.calendario, 3)
        self.layout_principal.addSpacing(10)
        self.layout_principal.addWidget(self.lista, 2)
        self.layout_principal.addSpacing(10)
        self.layout_principal.addLayout(self.columna_botones, 1)

        self.layout_general.addWidget(self.titulo)
        self.layout_general.addLayout(self.layout_principal)

        self.setLayout(self.layout_general)

    # 🎨 Crear botones estilizados
    def crear_boton(self, texto, color):
        boton = QPushButton(texto)
        boton.setMinimumHeight(60)
        boton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #222;
            }}
        """)
        return boton

    # ➕ Agregar cita
    def agregar_cita(self):
        fecha = self.calendario.selectedDate().toString("dd/MM/yyyy")

        texto = f"Cita: {fecha}"
        item = QListWidgetItem(texto)

        # 👉 guardar datos reales
        item.setData(1, {"fecha": fecha})

        self.lista.addItem(item)

    # ❌ Eliminar cita seleccionada
    def eliminar_cita(self):
        item = self.lista.currentItem()
        if item:
            self.lista.takeItem(self.lista.row(item))

    # 🖱️ Click simple
    def seleccionar_cita(self, item):
        print("Seleccionaste:", item.text())

    # ✏️ Doble click para editar
    def editar_cita(self, item):
        data = item.data(1)

        fecha_actual = data["fecha"]

        nuevo_texto, ok = QInputDialog.getText(
            self,
            "Editar cita",
            "Nueva fecha:",
            text=fecha_actual
        )

        if ok and nuevo_texto:
            data["fecha"] = nuevo_texto
            item.setData(1, data)
            item.setText(f"Cita: {nuevo_texto}")

    # 🔥 Escalado dinámico
    def resizeEvent(self, event):
        tamaño = max(10, min(self.width(), self.height()) // 35)

        # Botones
        for b in self.botones:
            f = b.font()
            f.setPointSize(tamaño)
            b.setFont(f)

        # Calendario
        f_cal = self.calendario.font()
        f_cal.setPointSize(tamaño)
        self.calendario.setFont(f_cal)

        # Lista
        f_lista = self.lista.font()
        f_lista.setPointSize(tamaño)
        self.lista.setFont(f_lista)

        # Título
        f_titulo = QFont()
        f_titulo.setPointSize(tamaño + 6)
        f_titulo.setBold(True)
        self.titulo.setFont(f_titulo)

        super().resizeEvent(event)


# 🚀 Ejecutar app
app = QApplication([])

ventana = Ventana()
ventana.resize(900, 500)
ventana.show()

app.exec()