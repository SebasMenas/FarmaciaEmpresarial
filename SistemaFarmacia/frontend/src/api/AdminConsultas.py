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
    def obtener_productos_disponibles():
        """
        Catálogo de venta restringido a lotes DISPONIBLE con stock real.
        Usado por la tabla de inventario del Técnico (y por el Auxiliar
        Diplomado para insumos de receta).
        """
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
    def registrar_producto(datos):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/admin/productos",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {
                    "exito": True,
                    "datos": respuesta.json()
                }
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", respuesta.text)
            except Exception:
                mensaje = respuesta.text
            return {
                "exito": False,
                "error": mensaje
            }
        except Exception as e:
            return {
                "exito": False,
                "error": str(e)
            }

    @staticmethod
    def listar_catalogo_productos():
        """
        Catálogo real de productos (GET /admin/productos), independiente de
        si ya tienen lotes ingresados o no. Usado para poblar el combo de
        'Reabastecer' sin depender de que ya exista stock físico, y para
        validar nombres duplicados antes de solicitar un producto nuevo.
        """
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/admin/productos",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

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
    def listar_zonas():
        """
        Catálogo cerrado de las 4 zonas físicas (A, B refrigerado; C, D
        ambiente). Se usa para poblar el selector de zona del Auxiliar
        Mayor en vez de un campo de texto libre.
        """
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/monitoreo/zonas",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def recalibrar_capacidad_zona(zona_id, capacidad_maxima_unidades):
        """Permite al Admin ajustar manualmente el techo de capacidad de una zona."""
        try:
            respuesta = requests.put(
                f"{API_BASE_URL}/admin/zonas/{zona_id}/capacidad",
                json={"capacidad_maxima_unidades": capacidad_maxima_unidades},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", respuesta.text)
            except Exception:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
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
    def atender_cliente():
        """
        Simula la llegada de un nuevo cliente con su pedido completo
        (productos deseados y, si aplica, receta ya emitida). El Técnico
        no provee ningún dato — todo lo genera el backend.
        """
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/atender",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", respuesta.text)
            except Exception:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def obtener_pedido_solicitado(venta_id):
        """Lo que el cliente pidió originalmente, para mostrarlo en la pantalla."""
        try:
            respuesta = requests.get(
                f"{API_BASE_URL}/operaciones/ventas/{venta_id}/pedido",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def agregar_producto_pedido(venta_id, producto_id, cantidad):
        """
        Confirma un producto del pedido del cliente al carrito. El backend
        resuelve automáticamente el lote; el Técnico no elige ninguno.
        """
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{venta_id}/items/por-producto",
                json={"producto_id": producto_id, "cantidad": cantidad},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                mensaje = err_json.get("detail", {}).get("mensaje", respuesta.text)
            except Exception:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def finalizar_facturacion(venta_id):
        """
        Cierra la venta. No envía ningún dato de receta: el backend ya
        sabe si la venta requiere receta desde que el cliente fue atendido.
        """
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{venta_id}/factura",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def cancelar_venta(venta_id):
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{venta_id}/cancelar",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

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
    def validar_credencial_empleado(credencial):
        """
        Verifica el código de empleado contra el backend sin reservar
        ningún insumo. Se usa al ingresar el código por primera vez en
        la pantalla del Auxiliar Diplomado.
        """
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/validar-credencial-empleado",
                json={"credencial_operacion": credencial},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                detalle = err_json.get("detail", {})
                mensaje = detalle.get("mensaje", respuesta.text) if isinstance(detalle, dict) else (detalle or respuesta.text)
            except Exception:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def iniciar_manufactura_por_producto(receta_id, producto_id, cantidad, credencial):
        """
        Reserva un insumo de manufactura sin elegir lote: el backend
        resuelve automáticamente el primer lote disponible con stock
        suficiente para ese producto, y valida que el producto realmente
        forme parte de los insumos requeridos de esta receta.
        """
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/manufactura/iniciar-por-producto",
                json={
                    "receta_id": receta_id,
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "credencial_operacion": credencial
                },
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                detalle = err_json.get("detail", {})
                if isinstance(detalle, dict):
                    mensaje = detalle.get("mensaje", respuesta.text)
                    codigo_error = detalle.get("codigo_error")
                else:
                    mensaje = detalle or respuesta.text
                    codigo_error = None
            except Exception:
                mensaje = respuesta.text
                codigo_error = None
            return {"exito": False, "error": mensaje, "codigo_error": codigo_error}
        except Exception as e:
            return {"exito": False, "error": str(e), "codigo_error": None}

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
                detalle = err_json.get("detail", {})
                if isinstance(detalle, dict):
                    mensaje = detalle.get("mensaje", respuesta.text)
                    codigo_error = detalle.get("codigo_error")
                else:
                    mensaje = detalle or respuesta.text
                    codigo_error = None
            except Exception:
                mensaje = respuesta.text
                codigo_error = None
            return {"exito": False, "error": mensaje, "codigo_error": codigo_error}
        except Exception as e:
            return {"exito": False, "error": str(e), "codigo_error": None}