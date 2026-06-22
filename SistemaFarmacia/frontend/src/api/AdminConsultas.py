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
    def obtener_UnEmpleado(id_empleado):

        respuesta = requests.get(
            f"{API_BASE_URL}/empleados/{id_empleado}",
            headers=ClienteAuth.obtener_headers()
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

    @staticmethod
    def editar_empleado(id_empleado, datos):

        respuesta = requests.put(
            f"{API_BASE_URL}/admin/empleados/{id_empleado}",
            json=datos,
            headers=ClienteAuth.obtener_headers()
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

    @staticmethod
    def cambiar_estado_lote(id_lote, estado):
        try:
            respuesta = requests.put(
                f"{API_BASE_URL}/admin/lotes/{id_lote}/estado",
                json={"estado": estado},
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
    def registrar_lote(datos):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/lotes",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
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
    def simular_proveedor_certificado():
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/test/simular-proveedor-certificado",
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
    def simular_proveedor_no_certificado():
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/test/simular-proveedor-no-certificado",
                timeout=5
            )
            # El endpoint de simulación retorna un objeto json si se aborta, pero con status HTTP 200
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return {
                    "exito": datos.get("exito", False),
                    "datos": datos,
                    "error": datos.get("detalle", "")
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
    def obtener_capacidad():
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/capacidad",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_tareas(fecha):
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/tareas",
                params={"fecha": fecha},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def crear_tarea(datos):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/monitoreo/tareas",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def actualizar_tarea_estado(id_tarea, completada):
        try:
            respuesta = requests.patch(
                f"{API_BASE_URL}/monitoreo/tareas/{id_tarea}/estado",
                json={"completada": completada},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}


class ClienteOperaciones:
    @staticmethod
    def obtener_cola_recetas():
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/operaciones/recetas/cola",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def generar_ticket_receta(id_receta):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/recetas/{id_receta}/generar-ticket",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            # Si hay un error de negocio como INSUMO_RECHAZADO, FastAPI devuelve un HTTP 400 con los detalles
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", {}).get("mensaje", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def dispensar_receta(id_receta):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/recetas/{id_receta}/dispensar",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def iniciar_manufactura(lote_id, credencial):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/manufactura/iniciar",
                json={"lote_id": lote_id, "credencial_operacion": credencial},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            # En caso de error de concurrencia o PIN inválido
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", {}).get("mensaje", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def almacenar_lote(lote_id, datos):
        try:
            respuesta = requests.put(
                f"{API_BASE_URL}/operaciones/almacenar/{lote_id}",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", {}).get("mensaje", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}