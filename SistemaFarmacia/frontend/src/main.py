import sys
import os
from PySide6.QtWidgets import QApplication
from views.login_view import LoginWindow

def cargar_estilos_globales(app: QApplication):
    """Carga y aplica el archivo QSS global a la aplicación."""
    ruta_base = os.path.dirname(os.path.abspath(__file__))
    ruta_qss = os.path.join(ruta_base, "assets", "css", "estilo_global.qss")
    
    try:
        with open(ruta_qss, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"Advertencia: No se encontró la hoja de estilos en {ruta_qss}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicar la hoja de estilos global antes de instanciar ventanas
    cargar_estilos_globales(app)

    ventana_inicial = LoginWindow()
    ventana_inicial.show()
    
    sys.exit(app.exec())