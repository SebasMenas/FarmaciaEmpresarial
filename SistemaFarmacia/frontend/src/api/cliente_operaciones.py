import requests
import os
from dotenv import load_dotenv
from api.cliente_auth import ClienteAuth

load_dotenv()

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api")

class ClienteOperaciones:

    @staticmethod
    def obtener_cola_recetas():
        """GET /api/operaciones/recetas/cola. Retorna lista de recetas en espera/elaboración (RecetaMagistralDTO)."""
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
        """POST /api/operaciones/recetas/{id}/generar-ticket. Valida insumos de receta y genera ticket."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/recetas/{id_receta}/generar-ticket",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            # Capturar errores controlados de calidad o duplicidad
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
        """POST /api/operaciones/recetas/{id}/dispensar. Registra la receta como dispensada."""
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
        """POST /api/operaciones/manufactura/iniciar. Reserva lote de insumo para manufactura."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/manufactura/iniciar",
                json={"lote_id": lote_id, "credencial_operacion": credencial},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                if isinstance(err_json.get("detail"), dict):
                    mensaje = err_json["detail"].get("mensaje", respuesta.text)
                else:
                    mensaje = err_json.get("detail", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def almacenar_lote(lote_id, datos):
        """PUT /api/operaciones/almacenar/{lote_id}. Actualiza ubicación y zona ambiental de un lote."""
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
                if isinstance(err_json.get("detail"), dict):
                    mensaje = err_json["detail"].get("mensaje", respuesta.text)
                else:
                    mensaje = err_json.get("detail", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def iniciar_venta(id_cliente):
        """POST /api/operaciones/ventas/atender. Inicia orden de venta para un cliente."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/atender",
                json={"id_cliente": id_cliente},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def agregar_item_venta(id_venta, lote_id, cantidad):
        """POST /api/operaciones/ventas/{id}/items. Agrega ítem con cantidad al carrito."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{id_venta}/items",
                json={"lote_id": lote_id, "cantidad": cantidad},
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                if isinstance(err_json.get("detail"), dict):
                    mensaje = err_json["detail"].get("mensaje", respuesta.text)
                else:
                    mensaje = err_json.get("detail", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def finalizar_venta(id_venta, datos):
        """POST /api/operaciones/ventas/{id}/factura. Finaliza venta y genera recetas magistrales si requiere."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{id_venta}/factura",
                json=datos,
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code in (200, 201):
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                if isinstance(err_json.get("detail"), dict):
                    mensaje = err_json["detail"].get("mensaje", respuesta.text)
                else:
                    mensaje = err_json.get("detail", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def cancelar_venta(id_venta):
        """POST /api/operaciones/ventas/{id}/cancelar. Cancela venta activa restituyendo el stock."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{id_venta}/cancelar",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            return {"exito": False, "error": respuesta.text}
        except Exception as e:
            return {"exito": False, "error": str(e)}

    @staticmethod
    def resolver_falta_stock(id_venta, id_item):
        """POST /api/operaciones/ventas/{id}/items/{item_id}/resolver-falta-stock."""
        try:
            respuesta = requests.post(
                f"{API_BASE_URL}/operaciones/ventas/{id_venta}/items/{id_item}/resolver-falta-stock",
                headers=ClienteAuth.obtener_headers(),
                timeout=5
            )
            if respuesta.status_code == 200:
                return {"exito": True, "datos": respuesta.json()}
            try:
                err_json = respuesta.json()
                if isinstance(err_json.get("detail"), dict):
                    mensaje = err_json["detail"].get("mensaje", respuesta.text)
                else:
                    mensaje = err_json.get("detail", respuesta.text)
            except:
                mensaje = respuesta.text
            return {"exito": False, "error": mensaje}
        except Exception as e:
            return {"exito": False, "error": str(e)}
