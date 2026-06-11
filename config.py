from dotenv import load_dotenv
import os

load_dotenv()  # solo actúa localmente; en Render las vars vienen del dashboard

MONGODB_URI = os.environ["MONGODB_URI"]          # obligatorio — falla si no está definida
DATABASE_NAME   = os.getenv("DATABASE_NAME",   "lector_barcode")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "registros")

# Cloudinary (opcional — sin estas vars la foto no se sube pero el resto funciona)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY",    "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
