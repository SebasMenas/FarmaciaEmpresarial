import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

class ClienteUsuarios:
    @staticmethod
    def registrar_usuario(token: str, datos_usuario: dict):
        """
        Envía los datos al servidor adjuntando el token de seguridad.
        """
        url = f"{API_BASE_URL}/usuarios/"
        
        # Se adjunta el token en las cabeceras HTTP
        cabeceras = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            respuesta = requests.post(url, json=datos_usuario, headers=cabeceras, timeout=5)
            
            if respuesta.status_code == 201:
                return {"exito": True, "datos": respuesta.json()}
            else:
                return {"exito": False, "error": respuesta.json().get("detail", "Error al registrar")}
                
        except requests.exceptions.ConnectionError:
            return {"exito": False, "error": "Error de conexión con el servidor."}
        
    @staticmethod
    def obtener_doctores(token: str):
        """
        Pide al servidor la lista de doctores usando el token de acceso.
        """
        url = f"{API_BASE_URL}/usuarios/doctores"
        cabeceras = {"Authorization": f"Bearer {token}"}

        try:
            respuesta = requests.get(url, headers=cabeceras, timeout=5)
            
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            else:
                return {"exito": False, "error": respuesta.json().get("detail", "Error al obtener datos")}
                
        except requests.exceptions.ConnectionError:
            return {"exito": False, "error": "Error de conexión con el servidor."}
        
    @staticmethod
    def obtener_pacientes(token):
        """Pide al servidor la lista de usuarios con rol PACIENTE"""
        url = f"{API_BASE_URL}/usuarios/pacientes"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return {"exito": True, "datos": res.json()}
            return {"exito": False, "error": "No se pudo obtener la lista de pacientes"}
        except Exception as e:
            return {"exito": False, "error": str(e)}
        
    @staticmethod
    def cambiar_password(token, password_actual, password_nueva):

        url = f"{API_BASE_URL}/usuarios/me/password"
        headers = {"Authorization": f"Bearer {token}"}
        datos = {
            "password_actual": password_actual,
            "password_nueva": password_nueva
        }

        try:
            res = requests.patch(url, json=datos, headers=headers, timeout=5)
            if res.status_code == 200:
                return {"exito": True}
            return {"exito": False, "error": res.json().get("detail", "Error desconocido")}
        except Exception as e:
            return {"exito": False, "error": str(e)}