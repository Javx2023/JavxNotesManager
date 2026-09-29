# Guia de Instalacion - JavxNotesManager

Pasos para instalar y usar JavxNotesManager en tu computadora.

---

## Prerequisito: Instalar Docker

Docker es el programa que ejecuta la App sin complicaciones. Solo se instala una vez.

### Windows

1. Abre tu navegador y ve a: **https://www.docker.com/products/docker-desktop/**
2. Haz clic en **"Download for Windows"**
3. Abre el archivo `.exe` que se descargó
4. Sigue el asistente con valores por defecto (Next, Next, Install)
5. Reinicia el computador cuando te lo pida
6. Despues de reiniciar, abre Docker Desktop y esperar a que diga "Docker Desktop is running"

### Mac

1. Abre tu navegador y ve a: **https://www.docker.com/products/docker-desktop/**
2. Haz clic en **"Download for Mac"**
   - Si tienes chip M1/M2/M3: descarga la version **"Apple Silicon"**
   - Si tienes chip Intel: descarga la version **"Intel Chip"**
3. Abre el archivo `.dmg` descargado
4. Arrastra el icono de Docker a la carpeta Aplicaciones
5. Abre Docker desde Launchpad y esperar a que diga "Docker Desktop is running"

### Linux (Ubuntu/Debian/Mint)

Abre la Terminal y copia linea por linea:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

Despues **cierra sesion y vuelve a iniciar** para que los cambios tengan efecto.

---

## Instalacion de JavxNotesManager

### Paso 1: Descargar la App

**Opcion A - Desde GitHub (recomendado):**

1. Ve a la pagina del proyecto en GitHub
2. Haz clic en el boton verde **"Code"**
3. Selecciona **"Download ZIP"**
4. Guarda el archivo en tu escritorio

**Opcion B - Archivo .zip:**

Si te compartieron el archivo `JavxNotesManager.zip`, guardalo en tu escritorio.

### Paso 2: Descomprimir

- **Windows:** Clic derecho sobre el archivo ZIP > "Extraer todo" > "Extraer"
- **Mac:** Haz doble clic sobre el archivo ZIP
- **Linux:** Clic derecho > "Extraer aqui"

Esto creara una carpeta llamada `JavxNotesManager` en tu escritorio.

### Paso 3: Abrir terminal en la carpeta

- **Windows:** Abre la carpeta, haz clic derecho en el espacio vacio > "Abrir en Terminal" o "Open in Terminal"
- **Mac:** Abre la carpeta, haz clic derecho > "Nueva ventana del terminal aqui"
- **Linux:** Abre la carpeta, haz clic derecho > "Abrir en terminal"

### Paso 4: Configurar tu carpeta de notas

Necesitas decirle a la App donde estan tus notas. Ejecuta estos comandos uno por uno:

**Windows:**
```cmd
copy .env.example .env
notepad .env
```

**Mac/Linux:**
```bash
cp .env.example .env
nano .env
```

Se abrira un editor de texto. Busca la linea que dice:

```
HOST_NOTAS_DIR=/home/usuario/Documentos/Notas
```

Cambiala por la ruta de TU carpeta de notas:

**Windows:**
```
HOST_NOTAS_DIR=C:\Users\TU_USUARIO\Documents\Notas
```

**Mac:**
```
HOST_NOTAS_DIR=/Users/TU_USUARIO/Documents/Notas
```

**Linux:**
```
HOST_NOTAS_DIR=/home/TU_USUARIO/Documentos/Notas
```

> **No tienes carpeta de notas?** No te preocupes. Crea una carpeta vacia en Documents/Notas y la App creara una nota de ejemplo automaticamente.

Guarda y cierra el editor:
- **Windows (Notepad):** Ctrl+S y cierra
- **Mac/Linux (nano):** Ctrl+X, luego Y, luego Enter

### Paso 5: Arrancar la App

Ejecuta este comando en la terminal:

**Windows:**
```cmd
docker compose up -d
```

**Mac/Linux:**
```bash
docker compose up -d
```

Espera a que veas algo como:

```
[+] Running 1/1
 ✔ Container javxnotesmanager  Started
```

### Paso 6: Abrir en el navegador

Abre tu navegador (Chrome, Firefox, Edge) y ve a:

**http://localhost:5000**

Listo! Ya puedes usar JavxNotesManager.

---

## Uso Basico

### Ver tus notas

Al abrir la App, veras todas tus notas en pantalla. Puedes:

- **Buscar:** Escribe en la caja de busqueda de la izquierda
- **Ver una nota:** Haz clic sobre ella
- **Crear nota:** Haz clic en "+ Nueva Nota"

### Editar una nota

1. Haz clic sobre la nota que quieres editar
2. Haz clic en "Editar"
3. Modifica lo que quieras
4. Haz clic en "Guardar"

### Exportar a PDF

- **Una nota:** Haz clic en el icono de PDF ( ) en la esquina de la nota
- **Variass notas:** Selecciona las notas con las casillas y usa "Exportar seleccionadas a PDF"

---

## Cerrar la App

Para cerrar JavxNotesManager:

```bash
docker compose down
```

Para volver a abrirla, repite el Paso 5.

---

## Solucion de Problemas

### "Docker no esta instalado" o "docker: no se encuentra"

Significa que Docker no esta instalado o no esta corriendo.

**Solucion:**
1. Abre Docker Desktop (Windows/Mac) o verifica que este corriendo (Linux)
2. Espera a que diga "Docker Desktop is running"
3. Intenta de nuevo

### "Puerto 5000 ocupado"

Si ves un error de que el puerto esta en uso, cambia el puerto en el archivo `.env`:

```
FLASK_PORT=5001
```

Despues reinicia:
```bash
docker compose down
docker compose up -d
```

Y abre **http://localhost:5001**

### "No se ven mis notas"

Verifica que la ruta en `.env` sea correcta:
1. Abre el archivo `.env`
2. Revisa que `HOST_NOTAS_DIR` apunte a tu carpeta real
3. Reinicia la App:
```bash
docker compose down
docker compose up -d
```

### "Error al generar PDF"

La exportacion a PDF puede fallar si faltan dependencias. La App funciona normalmente, solo no podra exportar PDF. Si necesitas PDF, reinstala:

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### "Ya no me funciona nada"

Reinicia todo:

```bash
docker compose down
docker compose up -d --build
```

---

## Preguntas Frecuentes

**Mis notas se guardan en la nube?**
No. Todo queda en tu computadora. Las notas estan en la carpeta que configuraste.

**Puedo usar mis notas en otra computadora?**
Si. Copia tu carpeta de notas a la otra computadora y sigue la instalacion ahi.

**Como actualizo la App?**
1. Descarga la nueva version
2. Reemplaza los archivos (excepto tu carpeta de notas y el archivo `.env`)
3. Ejecuta `docker compose up -d --build`

**Que pasa si borro la carpeta JavxNotesManager?**
Tus notas estan seguras en la carpeta que configuraste en `.env`. Solo vuelve a descargar y configurar.

---

## Comandos Utiles

| Comando | Que hace |
|---------|----------|
| `docker compose up -d` | Arranca la App |
| `docker compose down` | Detiene la App |
| `docker compose up -d --build` | Reconstruye y arranca |
| `docker compose logs` | Muestra errores si algo falla |
