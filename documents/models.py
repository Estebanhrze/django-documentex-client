from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


class Document(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        ARCHIVED = "archived", "Archivado"

    title = models.CharField("título", max_length=180)
    # Conservado para compatibilidad con registros locales existentes.
    file = models.FileField(
        "archivo",
        upload_to="documents/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "txt"])],
        blank=True,
        null=True,
    )
    file_path = models.CharField("ruta remota", max_length=500, blank=True)
    file_name = models.CharField("nombre del archivo", max_length=255, blank=True)
    file_type = models.CharField("tipo MIME", max_length=120, blank=True)
    file_size_kb = models.PositiveIntegerField("tamaño (KB)", null=True, blank=True)
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.ACTIVE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents")
    created_at = models.DateTimeField("fecha de carga", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        permissions = [
            ("view_reports", "Puede consultar reportes"),
        ]

    def __str__(self):
        return self.title

    @property
    def filename(self):
        if self.file_name:
            return self.file_name
        if self.file:
            return Path(self.file.name).name
        return "Archivo sin nombre"

    def get_absolute_url(self):
        return reverse("document-detail", kwargs={"pk": self.pk})


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField("versión")
    file = models.FileField(
        "archivo",
        upload_to="document_versions/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "txt"])],
        blank=True,
        null=True,
    )
    file_path = models.CharField("ruta remota", max_length=500, blank=True)
    file_name = models.CharField("nombre del archivo", max_length=255, blank=True)
    file_type = models.CharField("tipo MIME", max_length=120, blank=True)
    file_size_kb = models.PositiveIntegerField("tamaño (KB)", null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_versions")
    created_at = models.DateTimeField("fecha de carga", auto_now_add=True)

    class Meta:
        ordering = ["-number"]
        constraints = [models.UniqueConstraint(fields=["document", "number"], name="unique_document_version")]
        verbose_name = "versión de documento"
        verbose_name_plural = "versiones de documentos"

    def __str__(self):
        return f"{self.document} — v{self.number}"

class Report(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="reports",
        verbose_name="documento revisado",
        null=True,
        blank=True,
    )
    title = models.CharField("título", max_length=180)
    description = models.TextField("descripción")
    reviewed_file_path = models.CharField("ruta del archivo revisado", max_length=500, blank=True)
    reviewed_file_name = models.CharField("archivo revisado", max_length=255, blank=True)
    reviewed_document_updated_at = models.DateTimeField(
        "fecha de la versión revisada",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_reports",
        verbose_name="creado por",
    )
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "reporte"
        verbose_name_plural = "reportes"

    def __str__(self):
        return self.title
