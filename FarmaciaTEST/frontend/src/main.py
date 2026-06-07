import sys
from PySide6.QtWidgets import QApplication
from views.login_view import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    ventana_inicial = LoginWindow()
    ventana_inicial.show()
    
    sys.exit(app.exec())