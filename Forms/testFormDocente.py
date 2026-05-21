from PySide6.QtWidgets import (
    QWidget, QLineEdit, QPushButton, QFormLayout, QMessageBox, QComboBox
)
import sqlite3

class FormularioDocente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Nuevo Docente")
        self.setFixedSize(400, 300)
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QFormLayout()

        # Campos de texto
        self.txt_username = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_nombre = QLineEdit()
        self.txt_apellidos = QLineEdit()
        self.txt_rut = QLineEdit()
        
        self.cbx_sexo = QComboBox()
        self.cbx_sexo.addItems(["Hombre", "Mujer", "N/A"])

        # Añadir al layout
        layout.addRow("Usuario (Login):", self.txt_username)
        layout.addRow("Contraseña:", self.txt_password)
        layout.addRow("Nombre:", self.txt_nombre)
        layout.addRow("Apellidos:", self.txt_apellidos)
        layout.addRow("RUT:", self.txt_rut)
        layout.addRow("Sexo:", self.cbx_sexo)

        self.btn_guardar = QPushButton("Registrar Docente")
        self.btn_guardar.clicked.connect(self.guardar_docente)
        layout.addRow(self.btn_guardar)

        self.setLayout(layout)

    def guardar_docente(self):
        # Captura de datos
        datos = (
            self.txt_username.text().strip(),
            self.txt_password.text().strip(),
            self.txt_nombre.text().strip(),
            self.txt_apellidos.text().strip(),
            self.txt_rut.text().strip(),
            self.cbx_sexo.currentText(),
            "DOCENTE" # Rol predefinido
        )

        if not all(datos[:3]): # Validación mínima
            QMessageBox.warning(self, "Error", "Los campos Usuario, Contraseña y Nombre son obligatorios.")
            return

        try:
            conn = sqlite3.connect("sistema_citas.db")
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO usuarios 
                              (username, password, nombre, apellidos, rut, sexo, rol) 
                              VALUES (?,?,?,?,?,?,?)''', datos)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", f"Docente {datos[2]} registrado correctamente.")
            self.limpiar_campos()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "El nombre de usuario ya existe.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de base de datos: {e}")

    def limpiar_campos(self):
        self.txt_username.clear()
        self.txt_password.clear()
        self.txt_nombre.clear()
        self.txt_apellidos.clear()
        self.txt_rut.clear()