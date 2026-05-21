import sys
from PySide6.QtWidgets import QApplication
from localDb import inicializar_db # Importación de la base de datos
# Importación de los formularios desarrollados
from login import LoginWindow

if __name__ == "__main__":
    inicializar_db()
    app = QApplication(sys.argv)
    ventana_login = LoginWindow()
    ventana_login.show()
    sys.exit(app.exec())