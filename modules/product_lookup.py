"""
Módulo de consulta de productos por código de barras.

Cadena de fuentes (en orden de prioridad):
  1. Open Food Facts     – alimentos (global, sin clave)
  2. Open Beauty Facts   – cosméticos y cuidado personal (sin clave)
  3. Open Pet Food Facts – alimentos para mascotas (sin clave)
  4. Open Products Facts – productos del hogar, limpieza, etc. (sin clave)
  5. UPC Item DB         – productos generales (sin clave, 100 req/día)
"""

import traceback
import requests

_TIMEOUT = 7
_HEADERS = {"User-Agent": "ICG-Logistica/1.0 (contact@icg.com.mx)"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _safe(val, default=""):
    """Convierte cualquier valor a string limpio sin lanzar AttributeError."""
    return str(val).strip() if val is not None else default


def _first_tag(tags, prefix=""):
    """Devuelve el primer tag de una lista quitando prefijos como 'en:'."""
    clean = [t for t in (tags or []) if isinstance(t, str)]
    if not clean:
        return ""
    return clean[0].replace(prefix, "").replace("-", " ").title()


# ── Familia Open*Facts (misma estructura de API) ───────────────────────────────

_OFF_SOURCES = [
    ("Open Food Facts",     "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"),
    ("Open Beauty Facts",   "https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"),
    ("Open Pet Food Facts", "https://world.openpetfoodfacts.org/api/v0/product/{barcode}.json"),
    ("Open Products Facts", "https://world.openproductsfacts.org/api/v0/product/{barcode}.json"),
]


def _query_off(barcode: str, source: str, url: str) -> dict:
    """Consulta cualquier API de la familia Open*Facts (esquema idéntico)."""
    try:
        r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        r.raise_for_status()
        data = r.json()

        if data.get("status") != 1:
            return {"encontrado": False}

        p = data.get("product") or {}

        nombre = _safe(
            p.get("product_name_es")
            or p.get("product_name_en")
            or p.get("product_name")
            or p.get("abbreviated_product_name")
        )

        categorias = (
            _first_tag(p.get("categories_tags"), "en:")
            or _safe(p.get("categories")).split(",")[0].strip()
        )

        imagen = (
            _safe(p.get("image_front_url"))
            or _safe(p.get("image_url"))
            or _safe(p.get("image_small_url"))
        )

        return {
            "encontrado":  True,
            "fuente":      source,
            "nombre":      nombre,
            "marca":       _safe(p.get("brands")).split(",")[0].strip(),
            "categorias":  categorias,
            "cantidad":    _safe(p.get("quantity")),
            "paises_venta":_safe(p.get("countries")).split(",")[0].strip(),
            "imagen_url":  imagen,
            "nutriscore":  _safe(p.get("nutriscore_grade")).upper() or None,
        }

    except requests.RequestException:
        return {"encontrado": False}
    except Exception:
        print(f"[product_lookup] ERROR {source} barcode={barcode}:\n{traceback.format_exc()}")
        return {"encontrado": False}


# ── UPC Item DB ────────────────────────────────────────────────────────────────

def _query_upc_item_db(barcode: str) -> dict:
    try:
        url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
        r = requests.get(url, timeout=_TIMEOUT, headers=_HEADERS)
        r.raise_for_status()
        data = r.json()

        items = data.get("items") or []
        if not items:
            return {"encontrado": False}

        item  = items[0]
        imgs  = item.get("images") or []

        return {
            "encontrado": True,
            "fuente":     "UPC Item DB",
            "nombre":     _safe(item.get("title")),
            "marca":      _safe(item.get("brand")),
            "categorias": _safe(item.get("category")),
            "cantidad":   "",
            "imagen_url": imgs[0] if imgs else "",
            "nutriscore": None,
        }

    except requests.RequestException:
        return {"encontrado": False}
    except Exception:
        print(f"[product_lookup] ERROR UPC Item DB barcode={barcode}:\n{traceback.format_exc()}")
        return {"encontrado": False}


# ── Función pública ────────────────────────────────────────────────────────────

def lookup_product(barcode: str) -> dict:
    """
    Intenta encontrar el producto recorriendo todas las fuentes en orden.
    Retorna el primer resultado positivo, o encontrado=False si ninguna lo tiene.
    """
    # 1–4: familia Open*Facts
    for source, url_tpl in _OFF_SOURCES:
        url = url_tpl.format(barcode=barcode)
        result = _query_off(barcode, source, url)
        if result.get("encontrado"):
            return result

    # 5: UPC Item DB (fallback general)
    result = _query_upc_item_db(barcode)
    if result.get("encontrado"):
        return result

    return {
        "encontrado": False,
        "mensaje": "Producto no encontrado en ninguna base de datos.",
    }
