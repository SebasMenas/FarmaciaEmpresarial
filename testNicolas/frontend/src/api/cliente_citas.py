import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

class ClienteCitas:
    @staticmethod
    def obtener_citas_por_dia(token: str, fecha_iso: str):
        url = f"{API_BASE_URL}/citas/dia/{fecha_iso}" # Pide al servidor las citas de una fecha especifica
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return {"exito": True, "datos": res.json()}
            return {"exito": False, "error": res.json().get("detail", "Error al obtener citas")}
        except Exception as e:
            return {"exito": False, "error": "Error de conexión con el servidor."}

    @staticmethod
    def agendar_cita(token: str, datos_cita: dict):
        url = f"{API_BASE_URL}/citas/"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            res = requests.post(url, json=datos_cita, headers=headers, timeout=5)
            if res.status_code == 201:
                return {"exito": True, "datos": res.json()}
            return {"exito": False, "error": res.json().get("detail", "Error al agendar")}
        except Exception as e:
            return {"exito": False, "error": "Error de conexión con el servidor."}
        
    @staticmethod
    def cancelar_cita(token, id_cita):
        """Llama al endpoint de cancelación lógica"""
        url = f"{API_BASE_URL}/citas/{id_cita}/cancelar"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            res = requests.patch(url, headers=headers, timeout=5)
            if res.status_code == 200:
                return {"exito": True}
            return {"exito": False, "error": res.json().get("detail")}
        except Exception as e:
            return {"exito": False, "error": str(e)}