/* ── Utilidades globales compartidas ──────────────────────── */

/* Actualiza métricas (total / hoy) cada 10 s si los elementos existen */
(function startMetricsPoller() {
  const totalEl = document.getElementById('metric-total');
  const todayEl = document.getElementById('metric-today');
  if (!totalEl && !todayEl) return;   // no estamos en la página de inicio

  async function fetchMetrics() {
    try {
      const res  = await fetch('/api/metrics');
      const data = await res.json();
      if (totalEl) totalEl.textContent = data.total ?? totalEl.textContent;
      if (todayEl) todayEl.textContent = data.today ?? todayEl.textContent;
    } catch { /* silencioso si hay error de red */ }
  }

  document.addEventListener('DOMContentLoaded', () => {
    fetchMetrics();
    setInterval(fetchMetrics, 10_000);
  });
})();


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
