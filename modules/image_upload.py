"""Subida de imágenes a Cloudinary usando la REST API (sin SDK)."""

import hashlib
import os
import time

import requests

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
API_KEY    = os.getenv("CLOUDINARY_API_KEY", "")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
FOLDER     = "productos_icg"

_configured = False


def is_configured() -> bool:
    return bool(CLOUD_NAME and API_KEY and API_SECRET)


def upload_photo(image_bytes: bytes) -> str:
    """
    Sube una imagen a Cloudinary.
    Retorna la URL segura (https://...) o '' si no está configurado / falla.
    """
    if not is_configured():
        return ""

    ts     = int(time.time())
    params = f"folder={FOLDER}&timestamp={ts}"
    sig    = hashlib.sha1(f"{params}{API_SECRET}".encode()).hexdigest()

    try:
        resp = requests.post(
            f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/image/upload",
            data={
                "api_key":   API_KEY,
                "timestamp": ts,
                "signature": sig,
                "folder":    FOLDER,
            },
            files={"file": ("product.jpg", image_bytes, "image/jpeg")},
            timeout=20,
        )
        return resp.json().get("secure_url", "")
    except Exception as e:
        print(f"[image_upload] Error Cloudinary: {e}")
        return ""
