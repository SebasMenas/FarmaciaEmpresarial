from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from api.cliente_usuarios import ClienteUsuarios

class DialogoCambiarPassword(QDialog):
    def __init__(self, token, parent=None):
        super().__init__(parent)
        self.token = token
        self.setWindowTitle("Cambiar Contraseña")
        self.setFixedSize(300, 200)
        self.inicializar_ui()

    def inicializar_ui(self):
        layout = QVBoxLayout(self)

        self.txt_actual = QLineEdit()
        self.txt_actual.setPlaceholderText("Contraseña Actual")
        self.txt_actual.setEchoMode(QLineEdit.EchoMode.Password) # Oculta los caracteres

        self.txt_nueva = QLineEdit()
        self.txt_nueva.setPlaceholderText("Nueva Contraseña")
        self.txt_nueva.setEchoMode(QLineEdit.EchoMode.Password)

        self.btn_guardar = QPushButton("Actualizar Contraseña")
        self.btn_guardar.setStyleSheet("background-color: #27AE60; color: white; padding: 5px;")
        self.btn_guardar.clicked.connect(self.procesar_cambio)

        layout.addWidget(QLabel("Por seguridad, actualice su clave:"))
        layout.addWidget(self.txt_actual)
        layout.addWidget(self.txt_nueva)
        layout.addWidget(self.btn_guardar)

    def procesar_cambio(self):
        actual = self.txt_actual.text().strip()
        nueva = self.txt_nueva.text().strip()

        if not actual or not nueva:
            QMessageBox.warning(self, "Error", "Debe llenar ambos campos.")
            return
        
        if len(nueva) < 6:
            QMessageBox.warning(self, "Error", "La nueva contraseña debe tener al menos 6 caracteres.")
            return

        res = ClienteUsuarios.cambiar_password(self.token, actual, nueva)
        
        if res["exito"]:
            QMessageBox.information(self, "Éxito", "Contraseña actualizada correctamente.")
            self.accept() # Cierra el pop-up
        else:
            QMessageBox.critical(self, "Error", res["error"])