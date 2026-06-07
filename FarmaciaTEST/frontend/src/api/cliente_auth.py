import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api") # Backend(render, local)

class ClienteAuth:
    # Variables de estado en memoria para persistencia de la sesión
    _access_token = None
    _rol = None
    _username = None

    @classmethod
    def iniciar_sesion(cls, username, password):

        url = f"{API_BASE_URL}/auth/login"
        datos = {"username": username, "password": password}
        
        try:
            respuesta = requests.post(url, data=datos, timeout=5)
            
            if respuesta.status_code == 200:
                datos_json = respuesta.json()
                
                # Persistencia de credenciales en memoria de la aplicación
                cls._access_token = datos_json.get("access_token")
                cls._rol = datos_json.get("rol")
                cls._username = username
                return {"exito": True, "datos": datos_json}
                
            elif respuesta.status_code == 401:
                return {"exito": False, "error": "Credenciales de acceso incorrectas."}
            elif respuesta.status_code == 422:
                return {"exito": False, "error": "Error de formato de datos (Rechazado por OAuth2)."}
            else:
                return {"exito": False, "error": f"Error del servidor HTTP {respuesta.status_code}: {respuesta.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"exito": False, "error": "Fallo de conexión: El servidor backend no está en línea."}
        except Exception as e:
            return {"exito": False, "error": f"Fallo interno del cliente HTTP: {str(e)}"}

    @classmethod
    def obtener_headers(cls) -> dict:
        
        # Genera el diccionario de cabeceras con el JWT.
        if not cls._access_token:
            return {}
        
        return {"Authorization": f"Bearer {cls._access_token}"}

    @classmethod
    def obtener_rol_actual(cls):
        """Retorna el rol para habilitar/deshabilitar modulos en la interfaz grafica."""
        return cls._rol

    @classmethod
    def obtener_username_actual(cls):
        return cls._username

    @classmethod
    def cerrar_sesion(cls):
        """Destruye el token en memoria para forzar un nuevo login"""
        cls._access_token = None
        cls._rol = None
        cls._username = None