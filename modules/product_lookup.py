"""
Módulo de consulta de productos por código de barras.

Fuentes (en orden de prioridad):
  1. Open Food Facts  – libre, sin clave, ideal para alimentos
  2. UPC Item DB      – libre (100 req/día), cubre productos generales
"""

import requests

_TIMEOUT = 6
_HEADERS = {"User-Agent": "ICG-Logistica/1.0 (contact@icg.com.mx)"}


# ── Open Food Facts ────────────────────────────────────────────────────────────

def _safe(val, default=""):
    """Convierte cualquier valor a string limpio, evitando AttributeError con None."""
    return str(val).strip() if val is not None else default


def _query_open_food_facts(barcode: str) -> dict:
    try:
        url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        r.raise_for_status()
        data = r.json()

        if data.get("status") != 1:
            return {"encontrado": False}

        p = data["product"]

        nombre = _safe(
            p.get("product_name_es")
            or p.get("product_name_en")
            or p.get("product_name")
            or p.get("abbreviated_product_name")
        )

        tags = [t for t in (p.get("categories_tags") or []) if isinstance(t, str)]
        if tags:
            categorias = tags[0].replace("en:", "").replace("-", " ").title()
        else:
            categorias = _safe(p.get("categories")).split(",")[0].strip()

        countries_raw = _safe(p.get("countries"))
        paises = countries_raw.split(",")[0].strip()

        return {
            "encontrado": True,
            "fuente": "Open Food Facts",
            "nombre": nombre,
            "marca": _safe(p.get("brands")),
            "categorias": categorias,
            "cantidad": _safe(p.get("quantity")),
            "paises_venta": paises,
            "imagen_url": _safe(p.get("image_front_url")),
            "nutriscore": _safe(p.get("nutriscore_grade")).upper() or None,
        }

    except requests.RequestException as e:
        return {"encontrado": False, "error": f"Open Food Facts: {e}"}
    except Exception as e:
        import traceback
        print(f"[product_lookup] ERROR Open Food Facts barcode={barcode}: {traceback.format_exc()}")
        return {"encontrado": False, "error": str(e)}


# ── UPC Item DB ────────────────────────────────────────────────────────────────

def _query_upc_item_db(barcode: str) -> dict:
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
        r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        r.raise_for_status()
        data = r.json()

        items = data.get("items", [])
        if not items:
            return {"encontrado": False}

        item = items[0]
        imagenes = item.get("images", [])

        return {
            "encontrado": True,
            "fuente": "UPC Item DB",
            "nombre": item.get("title", "").strip(),
            "marca": item.get("brand", "").strip(),
            "categorias": item.get("category", "").strip(),
            "descripcion": item.get("description", "").strip()[:200],
            "imagen_url": imagenes[0] if imagenes else "",
        }

    except requests.RequestException as e:
        return {"encontrado": False, "error": f"UPC Item DB: {e}"}
    except Exception as e:
        import traceback
        print(f"[product_lookup] ERROR UPC Item DB barcode={barcode}: {traceback.format_exc()}")
        return {"encontrado": False, "error": str(e)}


# ── Función pública ────────────────────────────────────────────────────────────

def lookup_product(barcode: str) -> dict:
    """
    Consulta Open Food Facts y, si no encuentra el producto, prueba UPC Item DB.

    Retorna un dict con al menos las claves:
      - encontrado (bool)
      - nombre, marca, fuente  (si encontrado=True)
      - error, mensaje          (si encontrado=False)
    """
    result = _query_open_food_facts(barcode)
    if result.get("encontrado"):
        return result

    result = _query_upc_item_db(barcode)
    if result.get("encontrado"):
        return result

    return {
        "encontrado": False,
        "mensaje": "Producto no encontrado en las bases de datos consultadas.",
    }
