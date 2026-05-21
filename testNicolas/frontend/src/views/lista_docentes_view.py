from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                               QTableWidgetItem, QMessageBox, QPushButton, QHeaderView)
from api.cliente_usuarios import ClienteUsuarios

class ListaDocentesView(QWidget):
    def __init__(self, token_activo):
        super().__init__()
        self.token = token_activo
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout()
        
        self.btn_actualizar = QPushButton("Actualizar Lista de Doctores")
        self.btn_actualizar.clicked.connect(self.cargar_datos)
        
        # Configuración de la tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Apellidos", "RUT", "Sexo"])
        
        # Hacer que las columnas se estiren para llenar el espacio
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.btn_actualizar)
        layout.addWidget(self.tabla)
        self.setLayout(layout)
        
        # Cargar los datos automáticamente al abrir la vista
        self.cargar_datos()

    def cargar_datos(self):
        resultado = ClienteUsuarios.obtener_doctores(self.token)
        
        if resultado["exito"]:
            lista_doctores = resultado["datos"]
            
            # Limpia y prepara la tabla según la cantidad de doctores
            self.tabla.setRowCount(len(lista_doctores))
            
            for fila, doc in enumerate(lista_doctores):
                self.tabla.setItem(fila, 0, QTableWidgetItem(doc["nombre"]))
                self.tabla.setItem(fila, 1, QTableWidgetItem(doc["apellidos"]))
                self.tabla.setItem(fila, 2, QTableWidgetItem(doc["rut"]))
                self.tabla.setItem(fila, 3, QTableWidgetItem(doc["sexo"]))
        else:
            QMessageBox.warning(self, "Error", resultado["error"])