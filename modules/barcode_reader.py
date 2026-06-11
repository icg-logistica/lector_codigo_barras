"""Módulo lector de códigos de barras: decodificación de imágenes y extracción de información."""

import io
from PIL import Image


# Prefijos EAN/GS1 → país
_EAN_COUNTRY_MAP = {
    "000": "EE. UU.", "019": "EE. UU.", "050": "Reino Unido",
    "070": "Noruega", "073": "Finlandia", "076": "Suiza",
    "080": "Italia", "084": "España", "380": "Bulgaria",
    "400": "Alemania", "471": "Taiwán", "489": "Hong Kong",
    "490": "Japón", "499": "Japón", "500": "Reino Unido",
    "539": "Irlanda", "560": "Portugal", "569": "Islandia",
    "590": "Polonia", "600": "Sudáfrica", "611": "Marruecos",
    "619": "Túnez", "621": "Siria", "628": "Arabia Saudita",
    "629": "Emiratos Árabes", "640": "Finlandia", "690": "China",
    "699": "China", "750": "México", "754": "Canadá", "755": "Canadá",
    "759": "Venezuela", "770": "Colombia", "773": "Uruguay",
    "775": "Perú", "777": "Bolivia", "779": "Argentina",
    "780": "Chile", "784": "Paraguay", "786": "Ecuador",
    "789": "Brasil", "790": "Brasil", "800": "Italia",
    "840": "España", "850": "Cuba", "858": "Eslovaquia",
    "859": "Rep. Checa", "860": "Serbia", "880": "Corea del Sur",
    "885": "Tailandia", "888": "Singapur", "899": "Indonesia",
    "900": "Austria", "940": "Nueva Zelanda", "945": "Australia",
}


def _lookup_country(prefix13: str) -> str:
    for length in (3, 2):
        key = prefix13[:length]
        if key in _EAN_COUNTRY_MAP:
            return _EAN_COUNTRY_MAP[key]
    return "Desconocido"


def extract_barcode_info(codigo: str) -> dict:
    """
    Extrae información descriptiva del código de barras.
    Soporta EAN-13, EAN-8, UPC-A, UPC-E, y formatos genéricos (QR, CODE-128, etc.).
    """
    codigo = codigo.strip()
    info: dict = {"codigo": codigo}

    if codigo.startswith(("http://", "https://")):
        info["tipo"] = "QR Code – URL"
        info["url"] = codigo
        return info

    if codigo.isdigit():
        n = len(codigo)
        if n == 13:
            info["tipo"] = "EAN-13"
            info["pais_fabricacion"] = _lookup_country(codigo[:3])
            info["fabricante"] = codigo[3:8]
            info["producto"] = codigo[8:12]
            info["digito_control"] = codigo[12]
        elif n == 12:
            info["tipo"] = "UPC-A"
            info["fabricante"] = codigo[1:6]
            info["producto"] = codigo[6:11]
            info["digito_control"] = codigo[11]
        elif n == 8:
            info["tipo"] = "EAN-8 / UPC-E"
        elif n == 14:
            info["tipo"] = "GTIN-14 (caja/palet)"
        else:
            info["tipo"] = "Código numérico"
    else:
        info["tipo"] = "Alfanumérico (CODE-128 / QR / otro)"

    info["longitud"] = len(codigo)
    return info


def decode_from_image(image_bytes: bytes) -> dict:
    """
    Decodifica un código de barras a partir de bytes de imagen (JPEG/PNG).
    Requiere pyzbar instalado. Retorna dict con 'success', 'code', 'format'.
    """
    try:
        from pyzbar import pyzbar  # noqa: PLC0415

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        barcodes = pyzbar.decode(img)
        if not barcodes:
            return {"success": False, "message": "No se detectó ningún código de barras en la imagen"}
        bc = barcodes[0]
        return {
            "success": True,
            "code": bc.data.decode("utf-8"),
            "format": bc.type,
        }
    except ImportError:
        return {
            "success": False,
            "message": (
                "pyzbar no está instalado. "
                "En Windows instala 'zbar' (https://github.com/NaturalHistoryMuseum/pyzbar#installation) "
                "y luego 'pip install pyzbar'."
            ),
        }
    except Exception as exc:
        return {"success": False, "message": str(exc)}
