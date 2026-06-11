/* ══════════════════════════════════════════════════════════
   scanner.js  –  Escáner ZXing + lookup de producto + guardado
   ══════════════════════════════════════════════════════════ */

const Scanner = (() => {
  /* Estado */
  let reader        = null;
  let selectedDevice = null;
  let scanning      = true;
  let lastBarcode   = null;
  let currentProduct = null;   // datos del último producto buscado
  let isDuplicate   = false;

  /* ── Elementos del DOM ─────────────────────────────────── */
  const video       = () => document.getElementById('video');
  const camSelect   = () => document.getElementById('cam-select');
  const statusEl    = () => document.getElementById('scan-status');
  const resultEl    = () => document.getElementById('scan-result');
  const resultCode  = () => document.getElementById('result-code');
  const resultFmt   = () => document.getElementById('result-format');
  const successFlash= () => document.getElementById('success-flash');
  const uploadInput = () => document.getElementById('img-upload');

  /* ── Estados del panel de formulario ──────────────────── */
  function showIdle() {
    show('state-idle'); hide('state-loading'); hide('state-form');
  }
  function showLoading() {
    hide('state-idle'); show('state-loading'); hide('state-form');
  }
  function showForm() {
    hide('state-idle'); hide('state-loading'); show('state-form');
  }

  /* ── Status del escáner ────────────────────────────────── */
  function setStatus(txt, cls) {
    const el = statusEl();
    if (!el) return;
    el.textContent = txt;
    el.className   = `scan-status ${cls}`;
  }

  /* ── Flash de éxito ────────────────────────────────────── */
  function flashSuccess() {
    const fl = successFlash();
    if (!fl) return;
    fl.style.display  = 'block';
    fl.style.animation = 'flash .7s ease forwards';
    fl.addEventListener('animationend', () => { fl.style.display = 'none'; fl.style.animation = ''; }, { once: true });
  }

  /* ── Listar cámaras (llamar DESPUÉS de obtener permiso) ── */
  async function loadCameras(codeReader) {
    try {
      const devices = await codeReader.listVideoInputDevices();
      const sel = camSelect();
      if (!sel || !devices.length) return;

      // Guardar selección actual antes de repoblar
      const prev = sel.value;
      sel.innerHTML = '';
      let backIdx = -1;
      devices.forEach((d, i) => {
        const opt = document.createElement('option');
        opt.value = d.deviceId;
        opt.text  = d.label || `Cámara ${i + 1}`;
        sel.appendChild(opt);
        if (/back|rear|environment/i.test(d.label)) backIdx = i;
      });

      // Preferir cámara trasera; si ya había una seleccionada, mantenerla
      if (prev && [...sel.options].some(o => o.value === prev)) {
        sel.value = prev;
      } else if (backIdx >= 0) {
        sel.selectedIndex = backIdx;
      }
      selectedDevice = sel.value;

      // Registrar listener de cambio solo una vez
      if (!sel.dataset.listenerAdded) {
        sel.dataset.listenerAdded = '1';
        sel.addEventListener('change', () => {
          selectedDevice = sel.value;
          codeReader.reset();
          startCamera(codeReader);
        });
      }
    } catch (err) {
      console.warn('No se pudo listar cámaras:', err);
    }
  }

  /* ── Iniciar cámara ────────────────────────────────────── */
  async function startCamera(codeReader) {
    try {
      setStatus('⏳ Iniciando cámara…', 'scanning');
      scanning = true;
      await codeReader.decodeFromVideoDevice(
        selectedDevice || undefined,
        video(),
        (result, _err) => {
          if (!scanning) return;
          if (result) {
            onDetected(result.getText(), result.getBarcodeFormat().toString());
          }
          // _err ocurre en cada frame sin código — es normal, ignorar
        }
      );
      setStatus('🟢 Escaneando…', 'scanning');
      // Poblar selector de cámaras ahora que el permiso fue concedido
      await loadCameras(codeReader);
    } catch (err) {
      console.error('Error de cámara:', err);
      const name = err?.name || '';
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setStatus('❌ Permiso de cámara denegado', 'error');
        showToast('Permite el acceso a la cámara en tu navegador y recarga la página.', 'warn', 7000);
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        setStatus('❌ No se encontró ninguna cámara', 'error');
      } else if (name === 'NotReadableError' || name === 'TrackStartError') {
        setStatus('❌ Cámara en uso por otra app', 'error');
        showToast('Cierra otras apps que usen la cámara y recarga.', 'warn', 6000);
      } else if (name === 'SecurityError' ||
                 (location.protocol === 'http:' && location.hostname !== 'localhost')) {
        setStatus('❌ Requiere conexión HTTPS', 'error');
        showToast('La cámara solo funciona por HTTPS. Usa el botón de subir imagen.', 'warn', 8000);
      } else {
        setStatus(`❌ Error de cámara: ${err?.message || name || 'desconocido'}`, 'error');
      }
    }
  }

  /* ── Código detectado ──────────────────────────────────── */
  function onDetected(code, format) {
    if (!scanning || code === lastBarcode) return;
    scanning   = false;
    lastBarcode = code;

    flashSuccess();
    setStatus(`✅ Detectado: ${code}`, 'detected');
    show(resultEl());
    if (resultCode()) resultCode().textContent = code;
    if (resultFmt())  resultFmt().textContent  = `[${format}]`;

    lookupProduct(code);
  }

  /* ── Lookup de producto via API Flask ──────────────────── */
  async function lookupProduct(barcode) {
    showLoading();
    try {
      const res  = await fetch(`/api/product/${encodeURIComponent(barcode)}`);
      const data = await res.json();
      currentProduct = data.product || null;
      isDuplicate    = data.duplicate || false;
      renderProductInfo(barcode, data);
      showForm();
    } catch (err) {
      console.error('Error en lookup:', err);
      showToast('Error al buscar información del producto', 'error');
      showForm();
    }
  }

  /* ── Renderizar info de producto ───────────────────────── */
  function renderProductInfo(barcode, data) {
    const product = data.product || {};
    const info    = data.info    || {};

    /* Tarjeta de producto encontrado / no encontrado */
    hide('product-found');
    hide('product-notfound');

    if (product.encontrado) {
      const img  = document.getElementById('product-img');
      const src  = document.getElementById('product-source');
      const name = document.getElementById('product-name');
      const tbl  = document.getElementById('product-table');

      if (img) {
        if (product.imagen_url) {
          img.src = product.imagen_url; img.hidden = false;
        } else {
          img.hidden = true;
        }
      }
      if (src)  src.textContent  = `Fuente: ${product.fuente || '—'}`;
      if (name) name.textContent = product.nombre || '';

      const rows = [
        ['Marca',      product.marca      || '—'],
        ['Categorías', product.categorias || '—'],
        ['Cantidad',   product.cantidad   || '—'],
        ['Nutriscore', product.nutriscore || '—'],
      ];
      if (tbl) tbl.innerHTML = rows.map(([l, v]) =>
        `<tr><td>${l}</td><td>${v}</td></tr>`
      ).join('');

      show('product-found');

      /* Pre-rellenar nombre */
      const ni = document.getElementById('nombre-input');
      if (ni) ni.value = product.nombre || '';
    } else {
      show('product-notfound');
    }

    /* Datos técnicos del código */
    const techCard = document.getElementById('tech-info');
    const techTbl  = document.getElementById('tech-table');
    const techRows = Object.entries(info || {});
    if (techTbl && techRows.length) {
      techTbl.innerHTML = techRows.map(([k, v]) =>
        `<tr><td>${k.replace(/_/g, ' ')}</td><td>${v}</td></tr>`
      ).join('');
      show(techCard);
    } else {
      hide(techCard);
    }

    /* Aviso de duplicado */
    const dupWarn = document.getElementById('duplicate-warn');
    if (isDuplicate) show(dupWarn); else hide(dupWarn);
  }

  /* ── Guardar registro ──────────────────────────────────── */
  async function saveRecord() {
    const nombre = (document.getElementById('nombre-input')?.value || '').trim();
    const peso   = (document.getElementById('peso-input')?.value   || '').trim();
    const allowD = document.getElementById('allow-dup')?.checked || false;

    if (!nombre) { showToast('Escribe el nombre del producto', 'warn'); return; }
    if (!peso || isNaN(Number(peso)) || Number(peso) <= 0) {
      showToast('Ingresa un peso válido (mayor a 0)', 'warn'); return;
    }

    const btn = document.getElementById('btn-save');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Guardando…'; }

    try {
      const res = await fetch('/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          barcode:         lastBarcode,
          nombre,
          peso,
          producto_api:    currentProduct || {},
          allow_duplicate: allowD,
        }),
      });
      const data = await res.json();
      if (data.success) {
        showToast('✅ Producto guardado con éxito', 'success');
        setTimeout(() => restart(), 1200);
      } else {
        showToast(`Error: ${data.error}`, 'error');
      }
    } catch (err) {
      showToast('Error de conexión al guardar', 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '💾 Guardar'; }
    }
  }

  /* ── Upload de imagen (decodificar en servidor) ─────────── */
  function initUpload() {
    const input = uploadInput();
    if (!input) return;
    input.addEventListener('change', async () => {
      if (!input.files?.length) return;
      const fd = new FormData();
      fd.append('image', input.files[0]);
      setStatus('⏳ Procesando imagen…', 'scanning');
      try {
        const res  = await fetch('/api/decode', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success && data.barcode) {
          onDetected(data.barcode, data.format || 'DESCONOCIDO');
        } else {
          setStatus('❌ No se detectó código en la imagen', 'error');
          showToast('No se encontró código de barras en la imagen', 'warn');
        }
      } catch {
        setStatus('❌ Error al procesar imagen', 'error');
      }
      input.value = '';
    });
  }

  /* ── Reiniciar escáner ─────────────────────────────────── */
  function restart() {
    lastBarcode     = null;
    currentProduct  = null;
    isDuplicate     = false;
    scanning        = true;

    hide(resultEl());
    setStatus('🟢 Escaneando…', 'scanning');
    showIdle();

    /* Limpiar campos */
    const ni = document.getElementById('nombre-input');
    const pi = document.getElementById('peso-input');
    const ad = document.getElementById('allow-dup');
    if (ni) ni.value  = '';
    if (pi) pi.value  = '';
    if (ad) ad.checked = false;
  }

  /* ── Inicialización ────────────────────────────────────── */
  async function init() {
    if (typeof ZXing === 'undefined') {
      setStatus('❌ Librería ZXing no cargó', 'error');
      showToast('No se pudo cargar ZXing. Revisa tu conexión.', 'error', 7000);
      initUpload();
      return;
    }

    // navigator.mediaDevices solo existe en contextos seguros (HTTPS o localhost)
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatus('❌ Cámara no disponible (requiere HTTPS)', 'error');
      showToast('La cámara requiere HTTPS. Puedes usar el botón de subir imagen.', 'warn', 8000);
      initUpload();
      return;
    }

    reader = new ZXing.BrowserMultiFormatReader();
    // startCamera hace getUseMedia → pide permiso → después carga el selector de cámaras
    await startCamera(reader);
    initUpload();
  }

  /* Arrancar cuando el DOM esté listo */
  document.addEventListener('DOMContentLoaded', init);

  return { restart, saveRecord };
})();

/* Exponer saveRecord en el scope global (usada por el onclick del HTML) */
function saveRecord() { Scanner.saveRecord(); }
