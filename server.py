#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import glob
import markdown
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import frontmatter

NOTAS_DIR = os.environ.get("NOTAS_DIR", str(Path.home() / "Documentos" / "Notas"))
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

PDF_AVAILABLE = False
try:
    from weasyprint import HTML
    PDF_AVAILABLE = True
except ImportError:
    try:
        import pdfkit
        PDF_AVAILABLE = True
    except ImportError:
        pass

app = Flask(__name__)
CORS(app)


class GestorNotasAPI:
    def __init__(self, carpeta_notas=None):
        if carpeta_notas is None:
            carpeta_notas = NOTAS_DIR
        self.carpeta = Path(carpeta_notas)
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def _parse_frontmatter(self, content):
        result = {
            'titulo': 'Sin título',
            'tags': [],
            'autor': 'Anónimo',
            'fecha': ''
        }

        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            content_body = content[frontmatter_match.end():]

            title_match = re.search(r'title:\s*"([^"]*)"', frontmatter_text)
            if title_match:
                result['titulo'] = title_match.group(1)

            tags_match = re.search(r'tags:\s*\[\s*([^\]]*)\s*\]', frontmatter_text)
            if tags_match:
                tags_text = tags_match.group(1)
                result['tags'] = re.findall(r'"([^"]*)"', tags_text)

            author_match = re.search(r'author:\s*"([^"]*)"', frontmatter_text)
            if author_match:
                result['autor'] = author_match.group(1)

            date_match = re.search(r'date:\s*([^\n;]*)', frontmatter_text)
            if date_match:
                result['fecha'] = date_match.group(1).strip().strip('"')
        else:
            content_body = content

        return result, content_body

    def listar_todas(self) -> List[Dict]:
        archivos = glob.glob(str(self.carpeta / "*.md"))
        resultados = []

        for archivo in archivos:
            with open(archivo, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata, body = self._parse_frontmatter(content)
                resultados.append({
                    'id': Path(archivo).stem,
                    'titulo': metadata['titulo'],
                    'tags': metadata['tags'],
                    'autor': metadata['autor'],
                    'fecha': metadata['fecha'],
                    'resumen': body[:150] + "..." if len(body) > 150 else body
                })

        return sorted(resultados, key=lambda x: x['fecha'], reverse=True)

    def leer_nota(self, nombre: str) -> Dict:
        archivo = self.carpeta / f"{nombre}.md"
        if not archivo.exists():
            return None

        with open(archivo, 'r', encoding='utf-8') as f:
            content = f.read()
            metadata, body = self._parse_frontmatter(content)

        return {
            'id': nombre,
            'titulo': metadata['titulo'],
            'tags': metadata['tags'],
            'autor': metadata['autor'],
            'fecha': metadata['fecha'],
            'contenido': body
        }

    def buscar(self, query: str, exacto: bool = False) -> List[Dict]:
        if not query or len(query.strip()) < 2:
            return self.listar_todas()

        archivos = glob.glob(str(self.carpeta / "*.md"))
        resultados = []
        query_lower = query.lower()

        for archivo in archivos:
            with open(archivo, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata, body = self._parse_frontmatter(content)

            texto_busqueda = f"{metadata['titulo']} {body} {' '.join(metadata['tags'])}".lower()

            if exacto:
                encontrado = query_lower in texto_busqueda
            else:
                palabras = query_lower.split()
                encontrado = all(palabra in texto_busqueda for palabra in palabras if len(palabra) > 2)

            if encontrado:
                contexto = self._extraer_contexto(texto_busqueda, query_lower)
                resultados.append({
                    'id': Path(archivo).stem,
                    'titulo': metadata['titulo'],
                    'tags': metadata['tags'],
                    'autor': metadata['autor'],
                    'fecha': metadata['fecha'],
                    'resumen': body[:150] + "..." if len(body) > 150 else body,
                    'contexto': contexto
                })

        return resultados

    def _extraer_contexto(self, texto: str, query: str) -> str:
        pos = texto.find(query)
        if pos == -1:
            return ""

        inicio = max(0, pos - 60)
        fin = min(len(texto), pos + len(query) + 60)
        contexto = texto[inicio:fin]

        if inicio > 0:
            contexto = "..." + contexto
        if fin < len(texto):
            contexto = contexto + "..."

        return contexto

    def crear_nota(self, nombre: str, titulo: str, contenido: str, tags: List[str], autor: str) -> bool:
        archivo = self.carpeta / f"{nombre}.md"
        if archivo.exists():
            return False

        tags_str = ', '.join([f'"{tag}"' for tag in tags])
        fecha = datetime.now().strftime("%d/%m/%Y")

        frontmatter_content = f"""---
title: "{titulo}"
tags: [ {tags_str} ]
author: "{autor}"
date: {fecha}
---

{contenido}
"""
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(frontmatter_content)

        return True

    def actualizar_nota(self, nombre: str, titulo: str = None, contenido: str = None,
                        tags: List[str] = None, autor: str = None) -> bool:
        archivo = self.carpeta / f"{nombre}.md"
        if not archivo.exists():
            return False

        with open(archivo, 'r', encoding='utf-8') as f:
            content = f.read()
            metadata, body = self._parse_frontmatter(content)

        if titulo:
            metadata['titulo'] = titulo
        if contenido:
            body = contenido
        if tags is not None:
            metadata['tags'] = tags
        if autor:
            metadata['autor'] = autor

        tags_str = ', '.join([f'"{tag}"' for tag in metadata['tags']])
        new_content = f"""---
title: "{metadata['titulo']}"
tags: [ {tags_str} ]
author: "{metadata['autor']}"
date: {metadata['fecha'] if metadata['fecha'] else datetime.now().strftime("%d/%m/%Y")}
---

{body}
"""
        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def eliminar_nota(self, nombre: str) -> bool:
        archivo = self.carpeta / f"{nombre}.md"
        if archivo.exists():
            archivo.unlink()
            return True
        return False


gestor = GestorNotasAPI()

NOTAS_EJEMPLO_DIR = Path(__file__).parent / "notas_ejemplo"


def copiar_notas_ejemplo():
    """Copia notas de ejemplo al directorio de notas si está vacío."""
    archivos_notas = list(gestor.carpeta.glob("*.md"))
    if archivos_notas:
        return

    if not NOTAS_EJEMPLO_DIR.exists():
        return

    for archivo in NOTAS_EJEMPLO_DIR.glob("*.md"):
        destino = gestor.carpeta / archivo.name
        if not destino.exists():
            import shutil
            shutil.copy2(archivo, destino)
            print(f"  📝 Nota de ejemplo copiada: {archivo.name}")


copiar_notas_ejemplo()


def escape_html(text):
    if not text:
        return ""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def get_pdf_styles():
    return """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: counter(page);
                font-family: 'Helvetica', sans-serif;
                font-size: 10pt;
                color: #724eca;
            }
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            background: white;
            color: #1e2333;
            line-height: 1.6;
        }

        .pdf-container { max-width: 100%; }

        .pdf-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #724eca;
        }

        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #724eca;
            margin-bottom: 5px;
        }

        .slogan {
            font-size: 12px;
            color: #9fb800;
            font-family: monospace;
            letter-spacing: 2px;
        }

        .fecha-exportacion {
            font-size: 9px;
            color: #666;
            margin-top: 10px;
        }

        .pdf-content { margin: 20px 0; }

        .pdf-titulo-principal {
            font-size: 24px;
            font-weight: bold;
            color: #724eca;
            text-align: center;
            margin-bottom: 10px;
        }

        .pdf-titulo {
            font-size: 20px;
            color: #ffca28;
            margin-top: 20px;
            margin-bottom: 15px;
            page-break-after: avoid;
        }

        .pdf-subtitulo {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }

        .pdf-query {
            text-align: center;
            background: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
            font-family: monospace;
        }

        .pdf-meta {
            background: #f9f9f9;
            padding: 12px;
            border-left: 3px solid #724eca;
            margin: 15px 0;
            font-size: 11px;
            color: #555;
        }

        .meta-item { margin: 3px 0; }

        .pdf-divider {
            height: 1px;
            background: #ddd;
            margin: 20px 0;
        }

        .pdf-markdown { margin: 20px 0; }
        .pdf-markdown h1 { color: #724eca; font-size: 20px; margin-top: 20px; }
        .pdf-markdown h2 { color: #9fb800; font-size: 18px; margin-top: 15px; }
        .pdf-markdown h3 { color: #ffca28; font-size: 16px; }

        .pdf-markdown code {
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }

        .pdf-markdown pre {
            background: #f4f4f4;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
            font-size: 9pt;
        }

        .pdf-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 8px;
            text-align: center;
            color: #999;
        }

        .pdf-nota-separator {
            page-break-before: always;
            margin-top: 30px;
        }

        .pdf-nota-separator:first-of-type {
            page-break-before: avoid;
        }

        .nota-number {
            font-size: 11px;
            color: #724eca;
            margin-bottom: 10px;
        }

        .pdf-resultado {
            background: #fafafa;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            page-break-inside: avoid;
        }

        .resultado-titulo {
            color: #724eca;
            font-size: 16px;
            margin-bottom: 8px;
        }

        .resultado-meta {
            display: flex;
            gap: 15px;
            font-size: 9px;
            color: #666;
            margin-bottom: 8px;
        }

        .resultado-tags { margin: 8px 0; }

        .tag-pdf {
            display: inline-block;
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 8px;
            margin-right: 5px;
        }

        .resultado-resumen {
            font-size: 10px;
            color: #444;
            margin: 8px 0;
        }

        .resultado-contexto {
            background: #fff3e0;
            padding: 8px;
            border-left: 3px solid #ffca28;
            font-size: 9px;
            margin-top: 8px;
        }
    """


def generar_html_pdf_nota(nota):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{escape_html(nota['titulo'])}</title>
        <style>{get_pdf_styles()}</style>
    </head>
    <body>
        <div class="pdf-container">
            <div class="pdf-header">
                <div class="logo">Javxdesign</div>
                <div class="slogan">] herramientas útiles [</div>
                <div class="fecha-exportacion">Exportado: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
            </div>
            <div class="pdf-content">
                <h1 class="pdf-titulo">{escape_html(nota['titulo'])}</h1>
                <div class="pdf-meta">
                    <div class="meta-item">👤 Autor: {escape_html(nota['autor'])}</div>
                    <div class="meta-item">📅 Fecha: {nota['fecha'] or 'Sin fecha'}</div>
                    <div class="meta-item">🏷️ Tags: {', '.join(nota['tags']) if nota['tags'] else 'Sin tags'}</div>
                </div>
                <div class="pdf-divider"></div>
                <div class="pdf-markdown">
                    {markdown.markdown(nota['contenido'], extensions=['extra', 'codehilite'])}
                </div>
            </div>
            <div class="pdf-footer">
                <div class="footer-text">Documento generado desde Javxdesign Notes</div>
            </div>
        </div>
    </body>
    </html>
    """


def generar_html_pdf_multiple(notas, titulo):
    notas_html = ""
    for i, nota in enumerate(notas, 1):
        notas_html += f"""
        <div class="pdf-nota-separator">
            <div class="nota-number">Nota {i} de {len(notas)}</div>
            <h1 class="pdf-titulo">{escape_html(nota['titulo'])}</h1>
            <div class="pdf-meta">
                <div class="meta-item">👤 Autor: {escape_html(nota['autor'])}</div>
                <div class="meta-item">📅 Fecha: {nota['fecha'] or 'Sin fecha'}</div>
                <div class="meta-item">🏷️ Tags: {', '.join(nota['tags']) if nota['tags'] else 'Sin tags'}</div>
            </div>
            <div class="pdf-divider"></div>
            <div class="pdf-markdown">
                {markdown.markdown(nota['contenido'], extensions=['extra', 'codehilite'])}
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{escape_html(titulo)}</title>
        <style>{get_pdf_styles()}</style>
    </head>
    <body>
        <div class="pdf-container">
            <div class="pdf-header">
                <div class="logo">Javxdesign</div>
                <div class="slogan">] herramientas útiles [</div>
                <div class="fecha-exportacion">Exportado: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
            </div>
            <div class="pdf-content">
                <div class="pdf-titulo-principal">{escape_html(titulo)}</div>
                <div class="pdf-subtitulo">Total de notas: {len(notas)}</div>
                {notas_html}
            </div>
            <div class="pdf-footer">
                <div class="footer-text">Javxdesign Notes - Herramientas útiles</div>
            </div>
        </div>
    </body>
    </html>
    """


def generar_html_pdf_busqueda(resultados, query):
    resultados_html = ""
    for nota in resultados:
        resultados_html += f"""
        <div class="pdf-resultado">
            <h2 class="resultado-titulo">{escape_html(nota['titulo'])}</h2>
            <div class="resultado-meta">
                <span>📁 {escape_html(nota['id'])}.md</span>
                <span>👤 {escape_html(nota['autor'])}</span>
                <span>📅 {nota['fecha'] or 'Sin fecha'}</span>
            </div>
            <div class="resultado-tags">
                {" ".join([f'<span class="tag-pdf">#{escape_html(tag)}</span>' for tag in nota['tags']])}
            </div>
            <div class="resultado-resumen">{escape_html(nota['resumen'])}</div>
            {f'<div class="resultado-contexto">🔍 Contexto: ...{escape_html(nota["contexto"])}...</div>' if nota.get('contexto') else ''}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Búsqueda: {query}</title>
        <style>{get_pdf_styles()}</style>
    </head>
    <body>
        <div class="pdf-container">
            <div class="pdf-header">
                <div class="logo">Javxdesign</div>
                <div class="slogan">] herramientas útiles [</div>
                <div class="fecha-exportacion">Exportado: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
            </div>
            <div class="pdf-content">
                <div class="pdf-titulo-principal">Resultados de búsqueda</div>
                <div class="pdf-query">🔍 "{escape_html(query)}"</div>
                <div class="pdf-subtitulo">{len(resultados)} notas encontradas</div>
                <div class="pdf-divider"></div>
                {resultados_html}
            </div>
            <div class="pdf-footer">
                <div class="footer-text">Javxdesign Notes - Búsqueda avanzada</div>
            </div>
        </div>
    </body>
    </html>
    """


def _generate_pdf(html_content):
    if not PDF_AVAILABLE:
        return None, "PDF no disponible (instala weasyprint o pdfkit)"

    try:
        pdf = HTML(string=html_content).write_pdf()
        return pdf, None
    except Exception as e:
        return None, str(e)


# ============ RUTAS ============

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/notas', methods=['GET'])
def obtener_notas():
    query = request.args.get('q', '')
    exacto = request.args.get('exacto', 'false').lower() == 'true'

    if query:
        notas = gestor.buscar(query, exacto)
    else:
        notas = gestor.listar_todas()

    return jsonify(notas)


@app.route('/api/notas/<nombre>', methods=['GET'])
def obtener_nota(nombre):
    nota = gestor.leer_nota(nombre)
    if nota:
        return jsonify(nota)
    return jsonify({'error': 'Nota no encontrada'}), 404


@app.route('/api/notas', methods=['POST'])
def crear_nota():
    data = request.json
    nombre = data.get('nombre', '').replace(' ', '_').lower()

    if gestor.crear_nota(
        nombre=nombre,
        titulo=data.get('titulo'),
        contenido=data.get('contenido'),
        tags=data.get('tags', []),
        autor=data.get('autor', 'Anónimo')
    ):
        return jsonify({'success': True, 'id': nombre})
    return jsonify({'success': False, 'error': 'La nota ya existe'}), 400


@app.route('/api/notas/<nombre>', methods=['PUT'])
def actualizar_nota(nombre):
    data = request.json
    if gestor.actualizar_nota(
        nombre=nombre,
        titulo=data.get('titulo'),
        contenido=data.get('contenido'),
        tags=data.get('tags'),
        autor=data.get('autor')
    ):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Nota no encontrada'}), 404


@app.route('/api/notas/<nombre>', methods=['DELETE'])
def eliminar_nota(nombre):
    if gestor.eliminar_nota(nombre):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Nota no encontrada'}), 404


@app.route('/api/notas/<nombre>/pdf', methods=['GET'])
def exportar_pdf_nota(nombre):
    nota = gestor.leer_nota(nombre)
    if not nota:
        return jsonify({'error': 'Nota no encontrada'}), 404

    html_content = generar_html_pdf_nota(nota)
    pdf, error = _generate_pdf(html_content)

    if error:
        return jsonify({'error': f'Error generando PDF: {error}'}), 500

    return app.response_class(
        pdf,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{nombre}.pdf"'}
    )


@app.route('/api/notas/pdf/batch', methods=['POST'])
def exportar_pdf_multiple():
    data = request.json
    ids_notas = data.get('ids', [])
    titulo = data.get('titulo', 'Mis Notas')

    if not ids_notas:
        return jsonify({'error': 'No se seleccionaron notas'}), 400

    notas = []
    for nota_id in ids_notas:
        nota = gestor.leer_nota(nota_id)
        if nota:
            notas.append(nota)

    if not notas:
        return jsonify({'error': 'No se encontraron notas'}), 404

    html_content = generar_html_pdf_multiple(notas, titulo)
    pdf, error = _generate_pdf(html_content)

    if error:
        return jsonify({'error': f'Error generando PDF: {error}'}), 500

    return app.response_class(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="notas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"',
            'Content-Type': 'application/pdf'
        }
    )


@app.route('/api/buscar/pdf', methods=['POST'])
def exportar_pdf_busqueda():
    data = request.json
    query = data.get('query', '')
    exacto = data.get('exacto', False)

    resultados = gestor.buscar(query, exacto)
    html_content = generar_html_pdf_busqueda(resultados, query)
    pdf, error = _generate_pdf(html_content)

    if error:
        return jsonify({'error': f'Error generando PDF: {error}'}), 500

    return app.response_class(
        pdf,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="busqueda_{query}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"',
            'Content-Type': 'application/pdf'
        }
    )


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'pdf_available': PDF_AVAILABLE,
        'notas_dir': NOTAS_DIR,
        'notas_count': len(glob.glob(str(gestor.carpeta / "*.md")))
    })


if __name__ == '__main__':
    print(f"🚀 JavxNotesManager iniciado en http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"📁 Notas: {NOTAS_DIR}")
    print(f"📄 PDF: {'✅ Disponible' if PDF_AVAILABLE else '❌ No disponible'}")
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
