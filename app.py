"""
Aplicación principal – Lector de Códigos de Barras
ICG Logística
Ejecutar: streamlit run app.py
"""

import streamlit as st
from datetime import datetime

# ── Configuración de página (debe ser la primera llamada a Streamlit) ──────────
st.set_page_config(
    page_title="Lector Código Barras – ICG",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Módulos propios ────────────────────────────────────────────────────────────
from modules.ui_components import (
    inject_css, render_header, render_metrics,
    render_barcode_info, alert, render_records_table, format_datetime,
)
from modules.database import (
    get_all_records, get_record_by_id, delete_record,
    barcode_exists, count_today, test_connection,
)
from modules.business_logic import process_new_scan, process_edit
from modules.barcode_reader import extract_barcode_info, decode_from_image
from modules.product_lookup import lookup_product


# ── CSS global ─────────────────────────────────────────────────────────────────
inject_css()


# ══════════════════════════════════════════════════════════════════════════════
#  Estado de sesión
# ══════════════════════════════════════════════════════════════════════════════

def _init_state():
    defaults = {
        "barcode_from_cam": None,
        "barcode_confirmed": None,
        "scan_info": None,
        "producto_api": None,       # resultado de lookup_product()
        "photo_barcode": None,
        "edit_id": None,
        "delete_confirm_id": None,
        "active_tab": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ══════════════════════════════════════════════════════════════════════════════
#  Header y métricas
# ══════════════════════════════════════════════════════════════════════════════

render_header()

# Verificar conexión (solo si no se ha verificado en esta sesión)
if "db_ok" not in st.session_state:
    ok, msg = test_connection()
    st.session_state["db_ok"] = ok
    st.session_state["db_msg"] = msg

if not st.session_state["db_ok"]:
    alert(
        f"Sin conexión a MongoDB Atlas. Verifica tu cadena de conexión en .env<br>"
        f"Detalle: {st.session_state['db_msg']}",
        "error",
    )

# Métricas en tiempo real
try:
    records = get_all_records()
    today_n = count_today()
    render_metrics(len(records), today_n)
except Exception as e:
    alert(f"Error al obtener datos: {e}", "error")
    records = []

st.write("")

# ══════════════════════════════════════════════════════════════════════════════
#  Pestañas principales
# ══════════════════════════════════════════════════════════════════════════════

tab_scan, tab_records, tab_manage = st.tabs(
    ["📷  Escanear", "📋  Registros", "✏️  Gestión"]
)


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 1 – ESCANEAR
# ─────────────────────────────────────────────────────────────────────────────
with tab_scan:
    st.subheader("Escanear código de barras")

    col_photo, col_res = st.columns([1, 1], gap="large")

    with col_photo:
        st.markdown("**Toma una foto o sube una imagen con el código de barras**")
        img_file = st.camera_input("Capturar con cámara", key="cam_photo", label_visibility="collapsed")
        uploaded = st.file_uploader("O sube una imagen", type=["jpg", "jpeg", "png"], key="upload_photo")
        src = img_file or uploaded

    with col_res:
        if src:
            img_bytes = src.read()
            decode_result = decode_from_image(img_bytes)

            if decode_result["success"]:
                codigo = decode_result["code"]

                with st.spinner("Buscando información del producto…"):
                    producto_api = lookup_product(codigo)

                info = extract_barcode_info(codigo)
                alert(f"Código detectado: <b>{codigo}</b> ({decode_result.get('format', '')})", "success")
                render_barcode_info(info, producto_api)

                nombre_sugerido = producto_api.get("nombre", "") if producto_api.get("encontrado") else ""
                nombre_photo = st.text_input(
                    "Nombre del producto (editable)",
                    value=nombre_sugerido,
                    placeholder="Escribe o corrige el nombre…",
                    key="nombre_photo",
                )

                is_dup = barcode_exists(codigo)
                allow_dup = False
                if is_dup:
                    alert("Este código ya existe en la base de datos.", "warn")
                    allow_dup = st.checkbox("Permitir duplicado", key="allow_dup_photo")

                peso_photo = st.text_input("Peso (kg)", placeholder="Ej: 0.500", key="peso_photo")

                if st.button("💾 Guardar", type="primary", use_container_width=True):
                    api_guardada = dict(producto_api)
                    api_guardada["nombre"] = nombre_photo or nombre_sugerido
                    ok, result = process_new_scan(
                        codigo, peso_photo,
                        allow_duplicate=allow_dup,
                        producto_info=api_guardada,
                    )
                    if ok:
                        nombre_guardado = api_guardada.get("nombre", "") or codigo
                        st.toast(f"✅ Producto guardado con éxito: **{nombre_guardado}**", icon="✅")
                        st.rerun()
                    else:
                        alert(result, "error")
            else:
                alert(decode_result["message"], "error")
        else:
            st.info("Toma una foto o sube una imagen para decodificar el código.")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 2 – REGISTROS
# ─────────────────────────────────────────────────────────────────────────────
with tab_records:
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.subheader("Registros almacenados")
    with col_refresh:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    if records:
        # Búsqueda
        search = st.text_input(
            "🔍 Buscar por código o nombre de producto",
            placeholder="Ej: 750… o Leche…",
            key="search_records",
        )
        if search:
            s = search.lower()
            filtered = [
                r for r in records
                if s in r.get("codigo_barras", "").lower()
                or s in (r.get("nombre_producto") or "").lower()
                or s in (r.get("informacion", {}).get("nombre_producto") or "").lower()
                or s in (r.get("informacion", {}).get("marca") or "").lower()
            ]
        else:
            filtered = records
        st.caption(f"Mostrando {len(filtered)} de {len(records)} registros")
        render_records_table(filtered)
    else:
        alert("No hay registros aún. Ve a la pestaña «Escanear» para agregar el primero.", "info")


# ─────────────────────────────────────────────────────────────────────────────
#  TAB 3 – GESTIÓN (Editar / Eliminar)
# ─────────────────────────────────────────────────────────────────────────────
with tab_manage:
    st.subheader("Gestión de registros")

    if not records:
        alert("No hay registros para gestionar.", "info")
    else:
        # Selector de registro (muestra nombre si existe)
        def _record_label(r):
            nombre = r.get("nombre_producto") or r.get("informacion", {}).get("nombre_producto", "")
            nombre_str = f" · {nombre[:30]}" if nombre else ""
            return f"{r.get('codigo_barras','?')}{nombre_str}  |  {format_datetime(r.get('fecha_hora'))}  |  {r.get('peso','?')} kg"

        options = {_record_label(r): r["_id"] for r in records}
        selected_label = st.selectbox("Selecciona un registro", list(options.keys()), key="manage_select")
        selected_id = options[selected_label]

        record = get_record_by_id(selected_id)

        if record:
            col_edit, col_del = st.columns([2, 1], gap="large")

            # ── Editar ──────────────────────────────────────────────────────
            with col_edit:
                st.markdown("#### ✏️ Editar registro")
                with st.form("form_edit"):
                    new_code = st.text_input(
                        "Código de barras",
                        value=record.get("codigo_barras", ""),
                        key="edit_code",
                    )
                    new_nombre = st.text_input(
                        "Nombre del producto",
                        value=record.get("nombre_producto", "")
                              or record.get("informacion", {}).get("nombre_producto", ""),
                        placeholder="Nombre del producto…",
                        key="edit_nombre",
                    )
                    new_peso = st.text_input(
                        "Peso (kg)",
                        value=str(record.get("peso", "")),
                        key="edit_peso",
                    )
                    st.caption(f"Creado: {format_datetime(record.get('fecha_hora'))}")
                    submitted = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)

                if submitted:
                    # Preservar la info de API original y actualizar solo el nombre
                    api_guardada = dict(record.get("producto_api") or {})
                    api_guardada["nombre"] = new_nombre
                    ok, result = process_edit(
                        selected_id, new_code, new_peso,
                        nombre_producto=new_nombre,
                        producto_info=api_guardada,
                    )
                    if ok:
                        st.toast(f"✅ Registro actualizado con éxito: **{new_nombre or new_code}**", icon="✅")
                        st.rerun()
                    else:
                        msgs = result if isinstance(result, list) else [result]
                        for m in msgs:
                            alert(m, "error")

            # ── Eliminar ─────────────────────────────────────────────────────
            with col_del:
                st.markdown("#### 🗑️ Eliminar registro")
                info         = record.get("informacion", {})
                producto_api = record.get("producto_api")
                render_barcode_info(info, producto_api)

                # Doble confirmación para evitar borrados accidentales
                if st.session_state["delete_confirm_id"] == selected_id:
                    alert("¿Confirmas que deseas eliminar este registro? Esta acción no se puede deshacer.", "warn")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Sí, eliminar", type="primary", use_container_width=True):
                            ok = delete_record(selected_id)
                            st.session_state["delete_confirm_id"] = None
                            if ok:
                                st.toast("🗑️ Registro eliminado correctamente.", icon="🗑️")
                                st.rerun()
                            else:
                                alert("No se pudo eliminar el registro.", "error")
                    with cc2:
                        if st.button("❌ Cancelar", use_container_width=True):
                            st.session_state["delete_confirm_id"] = None
                            st.rerun()
                else:
                    if st.button("🗑️ Eliminar registro", use_container_width=True):
                        st.session_state["delete_confirm_id"] = selected_id
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  Footer
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    "<p style='text-align:center;font-size:.8rem;color:#94a3b8;'>"
    "ICG – Logística · Lector de Códigos de Barras · "
    f"{datetime.now().strftime('%Y')}</p>",
    unsafe_allow_html=True,
)
