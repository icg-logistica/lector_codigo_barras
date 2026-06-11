/* ── Utilidades globales compartidas ──────────────────────── */

/**
 * Muestra un toast de notificación en la esquina inferior derecha.
 * @param {string} msg  Texto del mensaje
 * @param {'success'|'error'|'warn'} type Tipo visual
 * @param {number} duration Milisegundos hasta desaparecer
 */
function showToast(msg, type = 'success', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), duration);
}

/** Hace visible un elemento (quita hidden) */
function show(id) {
  const el = typeof id === 'string' ? document.getElementById(id) : id;
  if (el) el.hidden = false;
}

/** Oculta un elemento (pone hidden) */
function hide(id) {
  const el = typeof id === 'string' ? document.getElementById(id) : id;
  if (el) el.hidden = true;
}
