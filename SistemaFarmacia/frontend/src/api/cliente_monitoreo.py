import requests
import os
from dotenv import load_dotenv
from api.cliente_auth import ClienteAuth

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")


class ClienteMonitoreo:

    @staticmethod
    def obtener_empleados():
        """GET /api/monitoreo/empleados. Retorna lista de empleados (UsuarioDTO)."""
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/empleados",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def editar_empleado(id_empleado, datos):
        """PUT /api/admin/empleados/{id}. Modifica datos de un empleado (EmpleadoUpdate)."""
        try:
            respuesta = requests.put(
                f"{API_BASE_URL}/admin/empleados/{id_empleado}",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def registrar_empleado(datos):
        """POST /api/admin/empleados. Registra un nuevo empleado (EmpleadoCreate)."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/empleados",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", {}).get("mensaje", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_almacenamiento():
        """GET /api/monitoreo/almacenamiento. Retorna inventario completo (LoteMonitoreoDTO)."""
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/almacenamiento",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_alertas_caducidad():
        """GET /api/monitoreo/alertas-caducidad. Retorna lotes próximos a vencer (30 días)."""
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/alertas-caducidad",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_capacidad():
        """GET /api/monitoreo/capacidad. Retorna agregación de capacidad por zona."""
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
        """GET /api/monitoreo/tareas?fecha=YYYY-MM-DD. Retorna agenda de tareas de la fecha."""
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
        """POST /api/monitoreo/tareas. Crea y delega una tarea (TareaCreate)."""
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
        """PATCH /api/monitoreo/tareas/{id}/estado. Cambia estado del checklist (TareaEstadoUpdate)."""
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

    # --- SIMULACIONES EXTERNAS ---

    @staticmethod
    def simular_proveedor_certificado():
        """POST /api/test/simular-proveedor-certificado."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/test/simular-proveedor-certificado",
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def simular_proveedor_no_certificado():
        """POST /api/test/simular-proveedor-no-certificado."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/test/simular-proveedor-no-certificado",
                timeout=5
            )
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return {
                    "exito": datos.get("exito", False),
                    "datos": datos,
                    "error": datos.get("detalle", "")
                }
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def simular_consumo_cliente():
        """POST /api/test/simular-consumo-cliente."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/test/simular-consumo-cliente",
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def cambiar_estado_lote(id_lote, estado):
        """PUT /api/admin/lotes/{id_lote}/estado. Modifica estado del lote (EstadoLoteUpdate)."""
        try:
            respuesta = requests.put(
                f"{API_BASE_URL}/admin/lotes/{id_lote}/estado",
                json={"estado": estado},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def registrar_producto(datos):
        """POST /api/admin/productos. Registra un nuevo tipo de producto (ProductoCreate)."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/productos",
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
    def registrar_lote(datos):
        """POST /api/admin/lotes. Registra un nuevo lote de producto (LoteCreate)."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/lotes",
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
    def configurar_capacidad_almacen(datos):
        """POST /api/admin/capacidad. Define o calibra el límite volumétrico por zona ambiental (CapacidadAlmacenUpdate)."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/capacidad",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_productos_disponibles():
        """GET /api/monitoreo/productos-disponibles. Retorna lotes disponibles para venta/manufactura (LoteVentaDTO)."""
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/productos-disponibles",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}


