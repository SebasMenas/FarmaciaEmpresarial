import requests
import os
from dotenv import load_dotenv

from api.cliente_auth import ClienteAuth

load_dotenv()

API_BASE_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000/api"
)

class ClienteMonitoreo:

    @staticmethod
    def obtener_almacenamiento():

        try:

            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/almacenamiento",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )

            if respuesta.status_code == 200:
                return {
                    "exito": True,
                    "datos": respuesta.json()
                }

            return {
                "exito": False,
                "error": respuesta.text
            }

        except Exception as e:
            return {
                "exito": False,
                "error": str(e)
            }


    @staticmethod
    def obtener_empleados():

        try:

            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/empleados",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )

            if respuesta.status_code == 200:
                return {
                    "exito": True,
                    "datos": respuesta.json()
                }

            return {
                "exito": False,
                "error": respuesta.text
            }

        except Exception as e:
            return {
                "exito": False,
                "error": str(e)
            }