# Documentex

Dashboard de gestión documental construido con Django. Los visitantes pueden revisar documentos y descargar el reporte general; los usuarios autenticados pueden cargar documentos y registrar nuevas versiones.

## Inicio rápido

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. El panel administrativo está disponible en `/admin/`.

## Permisos

- Visitantes: consultan el panel, los documentos y el reporte CSV.
- Usuarios autenticados: además cargan documentos y versiones.
- Administradores: administran todos los registros desde Django Admin.
