/* ══════════════════════════════════════════════════════════
   records.js  –  Eliminar registros
   ══════════════════════════════════════════════════════════ */

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
