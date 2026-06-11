"""Módulo de base de datos: conexión y operaciones CRUD con MongoDB Atlas."""

from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from datetime import datetime
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME

_client = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)
    return _client


def get_collection():
    client = get_client()
    db = client[DATABASE_NAME]
    col = db[COLLECTION_NAME]
    col.create_index([("codigo_barras", 1)])
    col.create_index([("fecha_hora", DESCENDING)])
    return col


def test_connection() -> tuple[bool, str]:
    try:
        get_client().admin.command("ping")
        return True, "Conexión exitosa"
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return False, f"Error de conexión: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def _serialize(record: dict) -> dict:
    """Convierte _id y datetime a tipos serializables."""
    r = dict(record)
    r["_id"] = str(r["_id"])
    dt = r.get("fecha_hora")
    if dt and hasattr(dt, "strftime"):
        r["fecha_hora_display"] = dt.strftime("%d/%m/%Y %H:%M")
        r["fecha_hora_iso"] = dt.isoformat()
    return r


def insert_record(codigo_barras, informacion, peso,
                  nombre_producto="", producto_info=None, foto_url="") -> str:
    col = get_collection()
    doc = {
        "codigo_barras":   codigo_barras,
        "nombre_producto": nombre_producto,
        "informacion":     informacion,
        "producto_api":    producto_info or {},
        "peso":            peso,
        "fecha_hora":      datetime.now(),
    }
    if foto_url:
        doc["foto_url"] = foto_url
    result = col.insert_one(doc)
    return str(result.inserted_id)


def get_all_records() -> list[dict]:
    col = get_collection()
    return [_serialize(r) for r in col.find().sort("fecha_hora", DESCENDING)]


def get_record_by_id(record_id: str) -> dict | None:
    col = get_collection()
    r = col.find_one({"_id": ObjectId(record_id)})
    return _serialize(r) if r else None


def update_record(record_id, codigo_barras, peso, informacion,
                  nombre_producto="", producto_info=None) -> bool:
    col = get_collection()
    data = {
        "codigo_barras": codigo_barras,
        "peso": peso,
        "informacion": informacion,
        "nombre_producto": nombre_producto,
        "actualizado_en": datetime.now(),
    }
    if producto_info is not None:
        data["producto_api"] = producto_info
    result = col.update_one({"_id": ObjectId(record_id)}, {"$set": data})
    return result.modified_count > 0


def delete_record(record_id: str) -> bool:
    col = get_collection()
    return col.delete_one({"_id": ObjectId(record_id)}).deleted_count > 0


def barcode_exists(codigo_barras: str, exclude_id: str | None = None) -> bool:
    col = get_collection()
    query: dict = {"codigo_barras": codigo_barras}
    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}
    return col.count_documents(query) > 0


def count_today() -> int:
    col = get_collection()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return col.count_documents({"fecha_hora": {"$gte": today}})
