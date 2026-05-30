import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Esta URL vendrá de tu .env (localhost ahora, Render después)
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

class ClienteAuth:
    @staticmethod
    def iniciar_sesion(username, password):
        url = f"{API_BASE_URL}/auth/login"
        datos = {"username": username, "password": password}
        
        print("\n--- DEBUG LOGIN ---")
        print(f"1. Intentando conectar a: {url}")
        
        try:
            respuesta = requests.post(url, data=datos, timeout=5)
            print(f"2. Conexión exitosa. Código HTTP: {respuesta.status_code}")
            print(f"3. Contenido crudo del servidor: {respuesta.text}")
            
            if respuesta.status_code == 200:
                print("4. Login correcto. Convirtiendo a JSON...")
                datos_json = respuesta.json()
                print(f"5. JSON parseado con éxito: {datos_json}")
                return {"exito": True, "datos": datos_json}
            else:
                return {"exito": False, "error": f"Error del servidor: {respuesta.text}"}
                
        except Exception as e:
            print(f"Error en el frontend")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Detalle: {str(e)}")
            return {"exito": False, "error": f"Fallo interno: {str(e)}"}