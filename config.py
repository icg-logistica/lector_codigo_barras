from dotenv import load_dotenv
import os

load_dotenv()  # solo actúa localmente; en Render las vars vienen del dashboard

MONGODB_URI = os.environ["MONGODB_URI"]          # obligatorio — falla si no está definida
DATABASE_NAME   = os.getenv("DATABASE_NAME",   "lector_barcode")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "registros")
