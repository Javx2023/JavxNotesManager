# JavxNotesManager

Gestor de notas Markdown con interfaz web, busqueda full-text y exportacion a PDF.

## Caracteristicas

- Crear, editar y eliminar notas en formato Markdown
- Frontmatter para metadata (titulo, tags, autor, fecha)
- Busqueda full-text con opcion de frase exacta
- Exportacion a PDF (individual, multiple y por busqueda)
- Interfaz dark mode responsiva
- API REST completa

## Instalacion

### Windows/Mac/Linux (con Docker)

1. [Instalar Docker Desktop](https://www.docker.com/products/docker-desktop/) (si aun no lo tienes)
2. Descargar o clonar este repositorio
3. Seguir la guia paso a paso: **[INSTALL.md](INSTALL.md)**

### Linux (sin Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
```

## Documentacion

- **[INSTALL.md](INSTALL.md)** - Guia de instalacion para usuarios inexpertos
- **[README.md](README.md)** - Esta pagina (documentacion tecnica)

## Estructura del proyecto

```
JavxNotesManager/
├── server.py            # Servidor Flask (API)
├── requirements.txt     # Dependencias Python
├── Dockerfile           # Imagen Docker
├── docker-compose.yml   # Orquestacion Docker
├── .env.example         # Variables de entorno de ejemplo
├── INSTALL.md           # Guia de instalacion para usuarios
├── static/
│   ├── style.css        # Estilos
│   ├── script.js        # Logica frontend
│   └── *.svg            # Logo
├── templates/
│   └── index.html       # Interfaz principal
└── notas_ejemplo/       # Nota de ejemplo
```

## Variables de entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `HOST_NOTAS_DIR` | Ruta en el HOST de tus notas (Docker) | `/home/usuario/Documentos/Notas` |
| `FLASK_PORT` | Puerto del servidor | `5000` |
| `FLASK_DEBUG` | Modo debug | `false` |

## API Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `GET` | `/api/notas` | Listar todas las notas |
| `GET` | `/api/notas?q=&exacto=` | Buscar notas |
| `GET` | `/api/notas/:id` | Obtener una nota |
| `POST` | `/api/notas` | Crear nota |
| `PUT` | `/api/notas/:id` | Actualizar nota |
| `DELETE` | `/api/notas/:id` | Eliminar nota |
| `GET` | `/api/notas/:id/pdf` | Exportar nota a PDF |
| `POST` | `/api/notas/pdf/batch` | Exportar multiples notas a PDF |
| `GET` | `/api/health` | Estado del sistema |

## Licencia

MIT
