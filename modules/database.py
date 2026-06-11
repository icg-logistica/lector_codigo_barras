"""Módulo de base de datos: conexión y operaciones CRUD con MongoDB Atlas."""

import streamlit as st
from pymongo import MongoClient, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from bson import ObjectId
from datetime import datetime
from config import MONGODB_URI, DATABASE_NAME, COLLECTION_NAME


@st.cache_resource(show_spinner=False)
def get_client():
    """Retorna el cliente MongoDB con caché para reutilizar la conexión."""
    return MongoClient(MONGODB_URI, serverSelectionTimeoutMS=8000)


def get_collection():
    """Retorna la colección de MongoDB y garantiza el índice de búsqueda."""
    client = get_client()
    db = client[DATABASE_NAME]
    col = db[COLLECTION_NAME]
    col.create_index([("codigo_barras", 1)])
    col.create_index([("fecha_hora", DESCENDING)])
    return col


def test_connection() -> tuple[bool, str]:
    """Verifica la conexión con MongoDB Atlas."""
    try:
        client = get_client()
        client.admin.command("ping")
        return True, "Conexión exitosa"
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        return False, f"Error de conexión: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def insert_record(
    codigo_barras: str,
    informacion: dict,
    peso: float,
    nombre_producto: str = "",
    producto_info: dict | None = None,
) -> str:
    """Inserta un nuevo registro y retorna su ID como string."""
    col = get_collection()
    doc = {
        "codigo_barras": codigo_barras,
        "nombre_producto": nombre_producto,
        "informacion": informacion,
        "producto_api": producto_info or {},
        "peso": peso,
        "fecha_hora": datetime.now(),
    }
    result = col.insert_one(doc)
    return str(result.inserted_id)


def get_all_records() -> list[dict]:
    """Retorna todos los registros ordenados por fecha descendente."""
    col = get_collection()
    records = list(col.find().sort("fecha_hora", DESCENDING))
    for r in records:
        r["_id"] = str(r["_id"])
    return records


def get_record_by_id(record_id: str) -> dict | None:
    """Retorna un registro por su ID."""
    col = get_collection()
    record = col.find_one({"_id": ObjectId(record_id)})
    if record:
        record["_id"] = str(record["_id"])
    return record


def update_record(
    record_id: str,
    codigo_barras: str,
    peso: float,
    informacion: dict,
    nombre_producto: str = "",
    producto_info: dict | None = None,
) -> bool:
    """Actualiza un registro existente. Retorna True si fue modificado."""
    col = get_collection()
    update_data: dict = {
        "codigo_barras": codigo_barras,
        "peso": peso,
        "informacion": informacion,
        "nombre_producto": nombre_producto,
        "actualizado_en": datetime.now(),
    }
    if producto_info is not None:
        update_data["producto_api"] = producto_info
    result = col.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": update_data},
    )
    return result.modified_count > 0


def delete_record(record_id: str) -> bool:
    """Elimina un registro por su ID. Retorna True si fue eliminado."""
    col = get_collection()
    result = col.delete_one({"_id": ObjectId(record_id)})
    return result.deleted_count > 0


def barcode_exists(codigo_barras: str, exclude_id: str | None = None) -> bool:
    """Verifica si ya existe un registro con ese código de barras."""
    col = get_collection()
    query: dict = {"codigo_barras": codigo_barras}
    if exclude_id:
        query["_id"] = {"$ne": ObjectId(exclude_id)}
    return col.count_documents(query) > 0


def count_today() -> int:
    """Cuenta los registros creados hoy."""
    col = get_collection()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return col.count_documents({"fecha_hora": {"$gte": today}})
