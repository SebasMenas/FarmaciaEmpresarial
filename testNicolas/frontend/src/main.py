import sys
from PySide6.QtWidgets import QApplication
from views.login_view import LoginWindow 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana_login = LoginWindow()
    ventana_login.show()
    
    sys.exit(app.exec())