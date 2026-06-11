/* ══════════════════════════════════════════════════════════
   records.js  –  Editar y eliminar registros (modal + DELETE)
   ══════════════════════════════════════════════════════════ */

/* ── Abrir modal de edición ────────────────────────────────── */
async function openEdit(id) {
  try {
    const res    = await fetch(`/api/records/${id}`);
    if (!res.ok) { showToast('No se pudo cargar el registro', 'error'); return; }
    const record = await res.json();

    document.getElementById('edit-id').value     = id;
    document.getElementById('edit-code').value   = record.codigo_barras || '';
    document.getElementById('edit-nombre').value = record.nombre_producto || '';
    document.getElementById('edit-peso').value   = record.peso || '';

    hide('edit-errors');
    show('edit-modal');
  } catch {
    showToast('Error de conexión', 'error');
  }
}

/* ── Guardar edición ────────────────────────────────────────── */
async function saveEdit() {
  const id     = document.getElementById('edit-id').value;
  const code   = document.getElementById('edit-code').value.trim();
  const nombre = document.getElementById('edit-nombre').value.trim();
  const peso   = document.getElementById('edit-peso').value.trim();
  const errEl  = document.getElementById('edit-errors');

  hide(errEl);

  if (!code || !nombre || !peso) {
    errEl.textContent = 'Todos los campos son obligatorios.';
    show(errEl); return;
  }
  if (isNaN(Number(peso)) || Number(peso) <= 0) {
    errEl.textContent = 'El peso debe ser un número mayor a 0.';
    show(errEl); return;
  }

  try {
    const res  = await fetch(`/api/records/${id}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo_barras: code, nombre_producto: nombre, peso }),
    });
    const data = await res.json();
    if (data.success) {
      showToast('✅ Registro actualizado', 'success');
      closeModal();
      setTimeout(() => location.reload(), 900);
    } else {
      const msgs = data.errors || [data.error || 'Error desconocido'];
      errEl.textContent = msgs.join(' | ');
      show(errEl);
    }
  } catch {
    errEl.textContent = 'Error de conexión al guardar.';
    show(errEl);
  }
}

/* ── Eliminar registro ──────────────────────────────────────── */
async function deleteRecord(id, btn) {
  if (!confirm('¿Eliminar este registro? Esta acción no se puede deshacer.')) return;

  const row = btn.closest('tr');
  if (row) row.style.opacity = '.4';

  try {
    const res  = await fetch(`/api/records/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Registro eliminado', 'warn');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast('No se pudo eliminar el registro', 'error');
      if (row) row.style.opacity = '1';
    }
  } catch {
    showToast('Error de conexión al eliminar', 'error');
    if (row) row.style.opacity = '1';
  }
}

/* ── Cerrar modal ───────────────────────────────────────────── */
function closeModal() {
  hide('edit-modal');
}

/* Cerrar modal al hacer clic fuera de la caja */
document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('edit-modal');
  if (overlay) {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeModal();
    });
  }
});
