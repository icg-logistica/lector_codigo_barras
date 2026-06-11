"""Módulo de interfaz: componentes visuales y CSS responsivo."""

import streamlit as st
from datetime import datetime


# ---------- CSS global ----------

CUSTOM_CSS = """
<style>
/* ── Reset y tipografía ──────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

.block-container {
    padding: 1rem 1rem 2rem !important;
    max-width: 1100px !important;
}

/* ── Header ──────────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #1a2e4a 0%, #2471a3 100%);
    color: white;
    padding: 18px 24px;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 14px;
}
.app-header .icon  { font-size: 2.2rem; line-height: 1; }
.app-header h1     { margin: 0; font-size: clamp(1.1rem, 3.5vw, 1.65rem); font-weight: 700; }
.app-header p      { margin: 4px 0 0; opacity: .82; font-size: .88rem; }

/* ── Tarjetas de métricas ─────────────────────────────────── */
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 14px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
}
.metric-card .mv { font-size: 2rem; font-weight: 800; color: #1a2e4a; }
.metric-card .ml { font-size: .82rem; color: #64748b; margin-top: 4px; }

/* ── Info de código escaneado ─────────────────────────────── */
.bc-info-card {
    background: #eaf4fb;
    border-left: 4px solid #2471a3;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 10px 0;
}
.bc-info-card h4 { margin: 0 0 10px; color: #1a2e4a; font-size: 1rem; }
.bc-info-card table { width: 100%; border-collapse: collapse; font-size: .9rem; }
.bc-info-card td { padding: 4px 8px; color: #1e293b !important; }
.bc-info-card td:first-child { font-weight: 600; color: #1a2e4a !important; white-space: nowrap; }
.bc-info-card h4 { color: #1a2e4a !important; }
.bc-info-card p  { color: #334155 !important; }
.bc-info-card b  { color: #0f172a !important; }
.bc-info-card small { color: #475569 !important; }

/* ── Alertas — fondo oscuro para compatibilidad con tema dark ─ */
.alert { padding: 12px 16px; border-radius: 8px; margin: 8px 0; font-size: .92rem; border-left-width: 4px; border-style: solid; }
.alert-success { background: #052e16; border-color: #22c55e; color: #bbf7d0 !important; }
.alert-error   { background: #2d0f0f; border-color: #ef4444; color: #fecaca !important; }
.alert-warn    { background: #2d1f00; border-color: #f59e0b; color: #fde68a !important; }
.alert-info    { background: #0c1a2e; border-color: #3b82f6; color: #bfdbfe !important; }
.alert b       { color: #ffffff !important; }

/* ── Tabla de registros ───────────────────────────────────── */
.records-table-wrap { overflow-x: auto; }
.records-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: .88rem;
    min-width: 520px;
}
.records-table-wrap th {
    background: #1a2e4a;
    color: white;
    padding: 9px 12px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
}
.records-table-wrap td {
    padding: 8px 12px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: middle;
}
.records-table-wrap tr:hover td { background: #f0f7ff; }
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: .78rem;
    font-weight: 600;
    background: #dbeafe;
    color: #1e40af;
}

/* ── Responsivo móvil ─────────────────────────────────────── */
@media (max-width: 640px) {
    .block-container { padding: 0.5rem 0.5rem 1.5rem !important; }
    .app-header { padding: 14px 16px; }
    .app-header h1 { font-size: 1.1rem; }
    .metric-card .mv { font-size: 1.6rem; }
}
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------- Componentes ─────────────────────────────────────


def render_header():
    st.markdown("""
    <div class="app-header">
        <span class="icon">🔍</span>
        <div>
            <h1>Lector de Códigos de Barras</h1>
            <p>ICG – Logística | Registro y control de productos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(total: int, today: int):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="mv">{total}</div>
            <div class="ml">📦 Total registros</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="mv">{today}</div>
            <div class="ml">📅 Escaneados hoy</div>
        </div>""", unsafe_allow_html=True)


def render_barcode_info(info: dict, producto_api: dict | None = None):
    """
    Muestra la información del producto y datos técnicos del código.
    Usa fondos oscuros para garantizar legibilidad en cualquier tema de Streamlit.
    """
    # Estilos comunes para celdas — texto blanco sobre fondo oscuro
    _tdl = "style='color:#94a3b8;font-size:.8rem;font-weight:600;padding:5px 10px;white-space:nowrap;text-transform:uppercase;letter-spacing:.05em;'"
    _tdv = "style='color:#f1f5f9;font-size:.92rem;padding:5px 10px;'"

    # ── Tarjeta de producto (API encontró resultado) ───────────────────────
    if producto_api and producto_api.get("encontrado"):
        nombre  = producto_api.get("nombre", "") or "—"
        marca   = producto_api.get("marca", "")
        fuente  = producto_api.get("fuente", "")
        cats    = producto_api.get("categorias", "")
        cant    = producto_api.get("cantidad", "")
        nutri   = producto_api.get("nutriscore", "")
        img_url = producto_api.get("imagen_url", "")
        desc    = producto_api.get("descripcion", "")

        extra_rows = ""
        if marca:  extra_rows += f"<tr><td {_tdl}>Marca</td><td {_tdv}>{marca}</td></tr>"
        if cats:   extra_rows += f"<tr><td {_tdl}>Categoría</td><td {_tdv}>{cats}</td></tr>"
        if cant:   extra_rows += f"<tr><td {_tdl}>Cantidad</td><td {_tdv}>{cant}</td></tr>"
        if nutri:  extra_rows += f"<tr><td {_tdl}>Nutriscore</td><td {_tdv}><b style='color:#4ade80'>{nutri}</b></td></tr>"
        if desc:   extra_rows += f"<tr><td {_tdl}>Descripción</td><td {_tdv}>{desc[:120]}…</td></tr>"

        img_tag = (
            f'<img src="{img_url}" style="max-height:80px;border-radius:6px;float:right;margin-left:12px;margin-bottom:8px;">'
            if img_url else ""
        )

        st.markdown(f"""
        <div style="background:#1a2e1a;border-left:4px solid #22c55e;border-radius:10px;padding:16px 18px;margin:10px 0;">
            {img_tag}
            <div style="color:#86efac;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;">
                🛒 Producto identificado &nbsp;·&nbsp; {fuente}
            </div>
            <div style="color:#ffffff;font-size:1.2rem;font-weight:700;margin-bottom:10px;">{nombre}</div>
            <table style="width:100%;border-collapse:collapse;">
                {extra_rows}
            </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Tarjeta de advertencia (producto no encontrado) ────────────────────
    elif producto_api and not producto_api.get("encontrado"):
        st.markdown("""
        <div style="background:#2d1f00;border-left:4px solid #f59e0b;border-radius:10px;padding:14px 18px;margin:10px 0;">
            <div style="color:#fcd34d;font-size:.88rem;font-weight:700;margin-bottom:6px;">
                ⚠️ Producto no encontrado en bases de datos externas
            </div>
            <div style="color:#fde68a;font-size:.83rem;">
                El código es válido pero no está registrado en Open Food Facts ni UPC Item DB.
                Puedes escribir el nombre manualmente antes de guardar.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Tarjeta de datos técnicos del código ──────────────────────────────
    labels = {
        "codigo":           "Código",
        "tipo":             "Tipo",
        "longitud":         "Longitud",
        "pais_fabricacion": "País fabricación (GS1)",
        "fabricante":       "Cód. fabricante",
        "producto":         "Cód. producto",
        "digito_control":   "Dígito control",
        "url":              "URL",
    }
    rows = ""
    for key, label in labels.items():
        if key in info:
            rows += f"<tr><td {_tdl}>{label}</td><td {_tdv}>{info[key]}</td></tr>"

    if rows:
        st.markdown(f"""
        <div style="background:#0f1e2d;border-left:4px solid #3b82f6;border-radius:10px;padding:16px 18px;margin:10px 0;">
            <div style="color:#93c5fd;font-size:.78rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">
                🔢 Datos técnicos del código
            </div>
            <table style="width:100%;border-collapse:collapse;">{rows}</table>
        </div>
        """, unsafe_allow_html=True)


def alert(msg: str, kind: str = "info"):
    """kind: success | error | warn | info"""
    icons = {"success": "✅", "error": "❌", "warn": "⚠️", "info": "ℹ️"}
    icon = icons.get(kind, "ℹ️")
    st.markdown(
        f'<div class="alert alert-{kind}">{icon} {msg}</div>',
        unsafe_allow_html=True,
    )


def format_datetime(dt) -> str:
    if dt is None:
        return "—"
    if isinstance(dt, str):
        return dt
    return dt.strftime("%d/%m/%Y %H:%M")


def render_records_table(records: list[dict]):
    """Renderiza la tabla HTML de registros incluyendo nombre del producto."""
    if not records:
        alert("No hay registros en la base de datos todavía.", "info")
        return

    rows = ""
    for r in records:
        info    = r.get("informacion", {})
        tipo    = info.get("tipo", "—")
        fecha   = format_datetime(r.get("fecha_hora"))
        peso    = r.get("peso", "—")
        peso_str = f"{peso} kg" if isinstance(peso, (int, float)) else str(peso)
        codigo  = r.get("codigo_barras", "—")

        # Nombre: del campo raíz o dentro de informacion
        nombre = (
            r.get("nombre_producto")
            or info.get("nombre_producto")
            or "—"
        )
        marca = (
            r.get("producto_api", {}).get("marca")
            or info.get("marca")
            or ""
        )
        nombre_display = nombre
        if marca and nombre != "—":
            nombre_display = f"{nombre} <small style='color:#64748b;'>({marca})</small>"

        rows += f"""
        <tr>
            <td><code>{codigo}</code></td>
            <td>{nombre_display}</td>
            <td><span class="badge">{tipo}</span></td>
            <td>{peso_str}</td>
            <td>{fecha}</td>
        </tr>"""

    st.markdown(f"""
    <div class="records-table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Código de barras</th>
                    <th>Nombre del producto</th>
                    <th>Tipo</th>
                    <th>Peso</th>
                    <th>Fecha / Hora</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
