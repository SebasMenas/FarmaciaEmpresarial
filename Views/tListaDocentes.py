from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QVBoxLayout,  QWidget)


class ListaDocentesWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre Completo", "RUT", "Sexo", "Rol"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.tabla)
        self.actualizar_tabla()

    def actualizar_tabla(self): # Consulta base de datos y actualiza la tabla

        from localDb import obtener_todos_docentes
        docentes = obtener_todos_docentes()
        
        self.tabla.setRowCount(len(docentes))
        for i, d in enumerate(docentes):
            self.tabla.setItem(i, 0, QTableWidgetItem(str(d.id)))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"{d.nombre} {d.apellidos}"))
            self.tabla.setItem(i, 2, QTableWidgetItem(d.rut))
            self.tabla.setItem(i, 3, QTableWidgetItem(d.sexo))
            self.tabla.setItem(i, 4, QTableWidgetItem(d.rol))