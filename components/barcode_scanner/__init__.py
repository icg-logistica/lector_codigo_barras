"""
Escáner de código de barras via cámara.

Usa st.components.v1.html() en lugar de declare_component para evitar
problemas con rutas que contienen espacios o caracteres especiales.
La comunicación Python ↔ JS se hace mediante localStorage + streamlit-js-eval.
"""

import os
import streamlit as st
import streamlit.components.v1 as components

_HTML_PATH = os.path.join(os.path.dirname(__file__), "frontend", "index.html")

_LS_KEY = "icg_scanner_barcode"   # clave usada en localStorage del padre


def _load_html() -> str:
    with open(_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def barcode_scanner_component(height: int = 500, key: str | None = None) -> str | None:
    """
    Renderiza el visor de cámara y devuelve el último código confirmado, o None.

    Flujo:
      1. El HTML del escáner detecta el código y el usuario pulsa «Confirmar».
      2. El JS escribe el código en window.parent.localStorage[icg_scanner_barcode].
      3. streamlit_js_eval lo lee en el contexto de la página Streamlit.
      4. Esta función lo retorna a app.py.
    """
    try:
        from streamlit_js_eval import streamlit_js_eval  # noqa: PLC0415
    except ImportError:
        st.error("Instala streamlit-js-eval: `pip install streamlit-js-eval`")
        return None

    # Renderizar el iframe del escáner
    components.html(_load_html(), height=height, scrolling=False)

    # Leer el código que el JS dejó en localStorage
    raw = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{_LS_KEY}')",
        key=f"bc_read_{key or 'default'}",
    )

    return raw if raw and raw not in (None, "null", "") else None


def clear_scanner_result(key: str | None = None) -> None:
    """Borra el código del localStorage para evitar reprocesarlo."""
    try:
        from streamlit_js_eval import streamlit_js_eval  # noqa: PLC0415

        streamlit_js_eval(
            js_expressions=f"localStorage.removeItem('{_LS_KEY}'); true",
            key=f"bc_clear_{key or 'default'}",
        )
    except ImportError:
        pass
