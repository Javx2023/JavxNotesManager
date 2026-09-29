let notaActual = null;

document.addEventListener('DOMContentLoaded', () => {
    cargarNotas();
    setupEventListeners();
    agregarBotonesPDF();
});

function setupEventListeners() {
    document.getElementById('btnCrearNota').onclick = () => abrirModalCrear();
    document.getElementById('searchInput').oninput = () => cargarNotas();
    document.getElementById('exactSearch').onchange = () => cargarNotas();
    document.getElementById('formNota').onsubmit = guardarNota;
    document.getElementById('btnEditarNota').onclick = editarNotaDesdeModal;
    document.getElementById('btnEliminarNota').onclick = eliminarNotaDesdeModal;
}

async function cargarNotas() {
    const query = document.getElementById('searchInput').value;
    const exacto = document.getElementById('exactSearch').checked;

    let url = '/api/notas';
    if (query) {
        url += `?q=${encodeURIComponent(query)}&exacto=${exacto}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error al cargar notas');
        const notas = await response.json();
        renderNotas(notas);
        actualizarEstadisticas(notas);
        renderTags(notas);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('notasGrid').innerHTML =
            `<div class="error">❌ Error al cargar notas: ${error.message}</div>`;
    }
}

function renderNotas(notas) {
    const grid = document.getElementById('notasGrid');

    if (!notas || notas.length === 0) {
        grid.innerHTML = '<div class="loading">📭 No hay notas disponibles</div>';
        return;
    }

    grid.innerHTML = notas.map(nota => `
        <div class="nota-card" onclick="verNota('${nota.id}')">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <h3 style="flex: 1;">${escapeHtml(nota.titulo)}</h3>
                <button class="btn-pdf-icon" onclick="event.stopPropagation(); exportarPDF('${nota.id}')" title="Exportar a PDF">
                    📄
                </button>
            </div>
            <div class="nota-meta">
                <span>👤 ${escapeHtml(nota.autor)}</span>
                <span>📅 ${nota.fecha || 'Sin fecha'}</span>
            </div>
            <div class="nota-tags">
                ${(nota.tags || []).map(tag => `<span class="nota-tag">#${escapeHtml(tag)}</span>`).join('')}
            </div>
            <div class="nota-resumen">${escapeHtml(nota.resumen || 'Sin contenido')}</div>
            ${nota.contexto ? `<div class="contexto">🔍 ...${escapeHtml(nota.contexto)}...</div>` : ''}
        </div>
    `).join('');
}

function actualizarEstadisticas(notas) {
    const totalNotas = notas.length;
    const todasTags = new Set();
    notas.forEach(nota => {
        (nota.tags || []).forEach(tag => todasTags.add(tag));
    });

    document.getElementById('totalNotas').textContent = totalNotas;
    document.getElementById('totalTags').textContent = todasTags.size;
}

function renderTags(notas) {
    const tagCount = new Map();
    notas.forEach(nota => {
        (nota.tags || []).forEach(tag => {
            tagCount.set(tag, (tagCount.get(tag) || 0) + 1);
        });
    });

    const tagsOrdenadas = Array.from(tagCount.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15);

    const container = document.getElementById('tagsList');
    if (tagsOrdenadas.length === 0) {
        container.innerHTML = '<span style="color: #666; font-size: 12px;">Sin tags</span>';
        return;
    }

    container.innerHTML = tagsOrdenadas.map(([tag, count]) => `
        <span class="tag" onclick="buscarPorTag('${escapeHtml(tag)}')">${escapeHtml(tag)} (${count})</span>
    `).join('');
}

function buscarPorTag(tag) {
    document.getElementById('searchInput').value = tag;
    cargarNotas();
}

async function verNota(id) {
    try {
        const response = await fetch(`/api/notas/${id}`);
        if (!response.ok) throw new Error('Nota no encontrada');
        const nota = await response.json();

        notaActual = nota;
        document.getElementById('verTitulo').textContent = nota.titulo;
        document.getElementById('verMeta').innerHTML = `
            <div>👤 ${escapeHtml(nota.autor)}</div>
            <div>📅 ${nota.fecha || 'Sin fecha'}</div>
            <div>🏷️ ${(nota.tags || []).map(t => '#' + escapeHtml(t)).join(' ')}</div>
        `;

        document.getElementById('verContenido').innerHTML = marked.parse(nota.contenido);
        abrirModal('modalVerNota');
    } catch (error) {
        alert('Error cargando la nota: ' + error.message);
    }
}

function abrirModalCrear() {
    document.getElementById('modalTitle').textContent = 'Crear Nueva Nota';
    document.getElementById('formNota').reset();
    document.getElementById('notaId').value = '';
    abrirModal('modalNota');
}

async function guardarNota(e) {
    e.preventDefault();

    const id = document.getElementById('notaId').value;
    const nombre = document.getElementById('nombreNota').value.trim().replace(/\s+/g, '_').toLowerCase();
    const titulo = document.getElementById('tituloNota').value;
    const autor = document.getElementById('autorNota').value || 'Anónimo';
    const tags = document.getElementById('tagsNota').value.split(',').map(t => t.trim()).filter(t => t);
    const contenido = document.getElementById('contenidoNota').value;

    const url = id ? `/api/notas/${id}` : '/api/notas';
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, titulo, autor, tags, contenido })
        });

        const result = await response.json();

        if (response.ok && (result.success || result.id)) {
            cerrarModal('modalNota');
            cargarNotas();
        } else {
            alert(result.error || 'Error al guardar');
        }
    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
}

function editarNotaDesdeModal() {
    if (!notaActual) return;
    cerrarModal('modalVerNota');

    document.getElementById('modalTitle').textContent = 'Editar Nota';
    document.getElementById('notaId').value = notaActual.id;
    document.getElementById('nombreNota').value = notaActual.id;
    document.getElementById('tituloNota').value = notaActual.titulo;
    document.getElementById('autorNota').value = notaActual.autor;
    document.getElementById('tagsNota').value = (notaActual.tags || []).join(', ');
    document.getElementById('contenidoNota').value = notaActual.contenido;
    abrirModal('modalNota');
}

async function eliminarNotaDesdeModal() {
    if (!notaActual) return;
    if (!confirm(`¿Eliminar la nota "${notaActual.titulo}"?`)) return;

    try {
        const response = await fetch(`/api/notas/${notaActual.id}`, { method: 'DELETE' });
        const result = await response.json();

        if (result.success) {
            cerrarModal('modalVerNota');
            cargarNotas();
        } else {
            alert('Error al eliminar');
        }
    } catch (error) {
        alert('Error de conexión');
    }
}

async function exportarPDF(id) {
    window.open(`/api/notas/${id}/pdf`, '_blank');
}

function abrirModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function cerrarModal(id) {
    document.getElementById(id).style.display = 'none';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function exportarNotaPDF(id) {
    window.open(`/api/notas/${id}/pdf`, '_blank');
}

function exportarNotasSeleccionadas() {
    const checkboxes = document.querySelectorAll('.select-nota:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);

    if (ids.length === 0) {
        alert('Selecciona al menos una nota');
        return;
    }

    const titulo = prompt('Título del documento PDF:', `Mis Notas (${ids.length})`);
    if (!titulo) return;

    fetch('/api/notas/pdf/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: ids, titulo: titulo })
    })
    .then(response => {
        if (response.ok) return response.blob();
        throw new Error('Error generando PDF');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `notas_${new Date().toISOString().slice(0,19)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        alert('Error: ' + error.message);
    });
}

async function exportarBusquedaPDF() {
    const query = document.getElementById('searchInput').value;
    const exacto = document.getElementById('exactSearch').checked;

    if (!query) {
        alert('Ingresa un término de búsqueda');
        return;
    }

    try {
        const response = await fetch('/api/buscar/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, exacto: exacto })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `busqueda_${query}_${new Date().toISOString().slice(0,19)}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } else {
            throw new Error('Error generando PDF');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function agregarBotonesPDF() {
    const sidebar = document.querySelector('.sidebar');
    const statsBox = document.querySelector('.stats-box');

    const pdfButtons = document.createElement('div');
    pdfButtons.className = 'pdf-actions';
    pdfButtons.innerHTML = `
        <button class="btn-pdf-export btn-pdf-red" id="btnExportarSeleccionadas">📑 Exportar seleccionadas a PDF</button>
        <button class="btn-pdf-export btn-pdf-blue" id="btnExportarBusqueda">🔍 Exportar resultados de búsqueda a PDF</button>
    `;

    if (statsBox) {
        statsBox.insertAdjacentElement('afterend', pdfButtons);
    }

    document.getElementById('btnExportarSeleccionadas')?.addEventListener('click', exportarNotasSeleccionadas);
    document.getElementById('btnExportarBusqueda')?.addEventListener('click', exportarBusquedaPDF);
}
