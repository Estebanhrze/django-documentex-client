# Documentex

Documentex es un sistema de gestión documental construido con Django. La idea es simple: tener un lugar centralizado donde un equipo pueda subir documentos, registrar nuevas versiones de esos documentos y generar reportes de lo que hay almacenado, todo con un control de acceso claro según el rol de cada persona.

El proyecto funciona como **cliente web** que se conecta a un servidor FastAPI separado que se encarga del almacenamiento real de los archivos. Django maneja la lógica de negocio, la autenticación, los permisos y las vistas; FastAPI recibe los archivos y devuelve URLs firmadas para descarga segura. La comunicación entre ambos servicios se hace servidor-a-servidor con un secreto compartido que nunca se expone al navegador.

---

## ¿Qué puede hacer el sistema?

- **Subir documentos** con título y archivo (PDF, DOC, DOCX o TXT). El archivo se envía directamente al servicio de almacenamiento FastAPI.
- **Registrar versiones** de un documento existente. Cada versión se numera automáticamente en orden ascendente.
- **Descargar archivos** a través de URLs firmadas y de corta vida que genera el servidor FastAPI, sin exponer rutas internas.
- **Ver un dashboard** con estadísticas rápidas: total de documentos, versiones y usuarios activos, más los últimos documentos subidos.
- **Consultar reportes** en formato CSV: un resumen general y uno detallado con solo los documentos activos.
- **Archivar documentos** marcándolos como archivados en lugar de eliminarlos, para mantener trazabilidad.

---

## Arquitectura

```
Navegador → Django (este repo) → FastAPI (servidor de archivos)
                ↓
           SQLite / PostgreSQL
```

Django guarda en base de datos los metadatos del archivo (`file_path`, `file_name`, `file_type`, `file_size_kb`) que le retorna FastAPI tras cada subida. El archivo físico vive solo en el servidor FastAPI; Django nunca lo almacena localmente en producción.

---

## Roles y permisos

El sistema tiene dos grupos preconfigurados que se crean automáticamente al ejecutar las migraciones:

| Rol | Qué puede hacer |
|---|---|
| **Editor documental** | Ver, crear, editar y eliminar documentos y versiones; consultar y crear reportes |
| **Revisor documental** | Solo ver documentos y versiones; consultar y crear reportes |

Los **administradores** (superusuarios) tienen acceso total incluyendo el panel de Django Admin en `/admin/`.

Para asignar un rol a un usuario, basta con añadirlo al grupo correspondiente desde Django Admin.

---

## Inicio rápido

### 1. Crear entorno virtual e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y completa los valores:

```powershell
Copy-Item .env.example .env
```

Las variables que **sí o sí** debes configurar son:

```env
DJANGO_SECRET_KEY=una-clave-larga-y-aleatoria
DOCUMENTS_API_BASE_URL=https://url-de-tu-servidor-fastapi
DOCUMENTS_API_SHARED_SECRET=el-mismo-secreto-que-usa-el-servidor-fastapi
```

### 3. Aplicar migraciones y crear el superusuario

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Al correr las migraciones también se crean automáticamente los grupos **Editor documental** y **Revisor documental**.

### 4. Levantar el servidor

```powershell
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El panel administrativo está en `/admin/`.

---

## Variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django. Obligatoria en producción. | Clave de desarrollo insegura |
| `DJANGO_DEBUG` | Activa el modo debug. Nunca usar `True` en producción. | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por coma. | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes de confianza para CSRF (necesario si usas proxy). | vacío |
| `DJANGO_SECURE_SSL_REDIRECT` | Redirige todo el tráfico a HTTPS. | `False` en dev, `True` en prod |
| `DJANGO_SECURE_HSTS_SECONDS` | Tiempo de HSTS en segundos. | `0` en dev, `31536000` en prod |
| `DOCUMENTS_API_BASE_URL` | URL base del servidor FastAPI de documentos. | `https://documents-api.fastapicloud.dev` |
| `DOCUMENTS_API_SHARED_SECRET` | Secreto compartido para autenticar llamadas servidor-a-servidor. | vacío |
| `DOCUMENTS_API_TIMEOUT_SECONDS` | Tiempo máximo de espera por respuesta del servidor FastAPI. | `30` |

---

## Rutas principales

| Ruta | Vista |
|---|---|
| `/dashboard/` | Panel con estadísticas generales |
| `/documentos/` | Listado paginado de documentos |
| `/documentos/nuevo/` | Subir un documento nuevo |
| `/documentos/<id>/` | Detalle de un documento y sus versiones |
| `/documentos/<id>/editar/` | Editar título o archivo |
| `/documentos/<id>/version/` | Registrar una nueva versión |
| `/documentos/<id>/descargar/` | Descargar el archivo principal |
| `/versiones/<id>/descargar/` | Descargar un archivo de versión específica |
| `/reportes/` | Listado de reportes |
| `/reportes/resumen-documentos.csv` | CSV con resumen general |
| `/reportes/documentos-activos.csv` | CSV con documentos activos y sus versiones |

---

## Stack técnico

- **Django 5.1+** — Framework web principal
- **python-dotenv** — Carga de variables de entorno desde `.env`
- **requests** — Comunicación HTTP con el servidor FastAPI
- **SQLite** — Base de datos por defecto (reemplazable por PostgreSQL en producción)
- **Zona horaria**: `America/Bogota` — **Idioma**: `es-co`
