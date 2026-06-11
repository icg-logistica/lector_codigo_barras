"""Aplicación Flask – Lector de Códigos de Barras ICG Logística."""

import os
from flask import Flask, render_template, request, jsonify

from modules.database import (
    get_all_records, get_record_by_id, delete_record,
    barcode_exists, count_today, test_connection,
)
from modules.business_logic import process_new_scan, process_edit
from modules.product_lookup import lookup_product
from modules.barcode_reader import extract_barcode_info, decode_from_image

app = Flask(__name__)
app.secret_key = os.urandom(24)


# ── Páginas ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    db_ok, db_msg = test_connection()
    total = len(get_all_records()) if db_ok else 0
    today = count_today() if db_ok else 0
    return render_template("index.html",
                           active="scanner",
                           db_ok=db_ok, db_msg=db_msg,
                           total=total, today=today)


@app.route("/records")
def records_page():
    db_ok, _ = test_connection()
    records = get_all_records() if db_ok else []
    search = request.args.get("q", "").strip()
    if search:
        s = search.lower()
        records = [
            r for r in records
            if s in r.get("codigo_barras", "").lower()
            or s in (r.get("nombre_producto") or "").lower()
            or s in (r.get("informacion", {}).get("marca") or "").lower()
        ]
    return render_template("records.html",
                           active="records",
                           records=records, search=search)


# ── API ────────────────────────────────────────────────────────────────────────

@app.route("/api/product/<barcode>")
def api_product(barcode):
    """Devuelve info del producto (API externa) + datos técnicos del código."""
    product = lookup_product(barcode)
    info = extract_barcode_info(barcode)
    duplicate = barcode_exists(barcode)
    return jsonify({"product": product, "info": info, "duplicate": duplicate})


@app.route("/api/save", methods=["POST"])
def api_save():
    """Guarda un nuevo registro."""
    data = request.get_json(silent=True) or {}
    barcode      = data.get("barcode", "")
    peso_raw     = data.get("peso", "")
    producto_api = data.get("producto_api", {})
    allow_dup    = data.get("allow_duplicate", False)

    # Aplicar nombre editado por el usuario
    nombre = data.get("nombre", "")
    if producto_api:
        producto_api["nombre"] = nombre

    ok, result = process_new_scan(
        barcode, peso_raw,
        allow_duplicate=allow_dup,
        producto_info=producto_api,
    )
    if ok:
        return jsonify({"success": True, "id": result})
    return jsonify({"success": False, "error": result}), 400


@app.route("/api/records/<record_id>", methods=["GET", "PUT", "DELETE"])
def api_record(record_id):
    if request.method == "GET":
        record = get_record_by_id(record_id)
        if not record:
            return jsonify({"error": "No encontrado"}), 404
        return jsonify(record)

    if request.method == "DELETE":
        return jsonify({"success": delete_record(record_id)})

    # PUT – editar
    data         = request.get_json(silent=True) or {}
    barcode      = data.get("codigo_barras", "")
    peso_raw     = data.get("peso", "")
    nombre       = data.get("nombre_producto", "")
    producto_api = data.get("producto_api")

    ok, result = process_edit(
        record_id, barcode, peso_raw,
        nombre_producto=nombre,
        producto_info=producto_api,
    )
    if ok:
        return jsonify({"success": True})
    msgs = result if isinstance(result, list) else [result]
    return jsonify({"success": False, "errors": msgs}), 400


@app.route("/api/decode", methods=["POST"])
def api_decode():
    """Decodifica un código de barras a partir de una imagen enviada."""
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No se envió imagen"}), 400
    img_bytes = request.files["image"].read()
    return jsonify(decode_from_image(img_bytes))


# ── Arranque ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
