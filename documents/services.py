from typing import Any

import requests
from django.conf import settings


class DocumentsAPIError(Exception):
    """An expected error while communicating with the document API."""


def _headers(user_id: int) -> dict[str, str]:
    if not settings.DOCUMENTS_API_SHARED_SECRET:
        raise DocumentsAPIError(
            "Falta configurar DOCUMENTS_API_SHARED_SECRET en el servidor Django."
        )
    return {
        "Accept": "application/json",
        "X-Documentex-Internal-Key": settings.DOCUMENTS_API_SHARED_SECRET,
        "X-Documentex-User-Id": str(user_id),
    }


def _error_detail(response: requests.Response) -> str:
    try:
        payload: Any = response.json()
    except ValueError:
        return "La API documental devolvió una respuesta no válida."
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("message")
        if detail:
            return str(detail)
    return "La API documental no pudo completar la solicitud."


def upload_document(uploaded_file, user_id: int) -> dict[str, Any]:
    """Uploads an uploaded Django file through the trusted FastAPI channel."""
    try:
        uploaded_file.seek(0)
        content = uploaded_file.read()
        response = requests.post(
            f"{settings.DOCUMENTS_API_BASE_URL}/api/v1/uploads/",
            headers=_headers(user_id),
            files={
                "file": (
                    uploaded_file.name,
                    content,
                    uploaded_file.content_type or "application/octet-stream",
                )
            },
            timeout=settings.DOCUMENTS_API_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise DocumentsAPIError(
            "No fue posible conectar con el servicio de documentos."
        ) from exc
    finally:
        uploaded_file.seek(0)

    if response.status_code != 201:
        raise DocumentsAPIError(_error_detail(response))

    try:
        payload = response.json()
    except ValueError as exc:
        raise DocumentsAPIError(
            "La API documental no devolvió la información del archivo."
        ) from exc

    if not isinstance(payload, dict):
        raise DocumentsAPIError("La respuesta de la API documental no es válida.")

    file_path = payload.get("file_path")
    file_name = payload.get("file_name")
    file_type = payload.get("file_type")
    file_size_kb = payload.get("file_size_kb")
    if not isinstance(file_path, str) or not file_path.strip():
        raise DocumentsAPIError("La API documental no devolvió la ruta del archivo.")
    if not isinstance(file_name, str) or not file_name.strip():
        # El navegador ya entregó el nombre original; evita guardar NULL en Django.
        file_name = uploaded_file.name
    if not isinstance(file_type, str) or not file_type.strip():
        file_type = uploaded_file.content_type or "application/octet-stream"
    if not isinstance(file_size_kb, int) or file_size_kb < 0:
        raise DocumentsAPIError("La API documental no devolvió el tamaño del archivo.")

    return {
        "file_path": file_path,
        "file_name": file_name,
        "file_type": file_type,
        "file_size_kb": file_size_kb,
    }


def create_download_url(file_path: str, user_id: int) -> str:
    try:
        response = requests.get(
            f"{settings.DOCUMENTS_API_BASE_URL}/api/v1/uploads/signed-url",
            headers=_headers(user_id),
            params={"file_path": file_path},
            timeout=settings.DOCUMENTS_API_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise DocumentsAPIError(
            "No fue posible preparar la descarga del archivo."
        ) from exc

    if response.status_code != 200:
        raise DocumentsAPIError(_error_detail(response))

    try:
        signed_url = response.json().get("signed_url")
    except ValueError as exc:
        raise DocumentsAPIError("La API documental devolvió una respuesta no válida.") from exc
    if not isinstance(signed_url, str) or not signed_url.startswith(("https://", "http://")):
        raise DocumentsAPIError("La API documental no devolvió un enlace de descarga válido.")
    return signed_url