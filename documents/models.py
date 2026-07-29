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
    file = models.FileField(
        "archivo",
        upload_to="documents/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "txt"])],
    )
    status = models.CharField("estado", max_length=10, choices=Status.choices, default=Status.ACTIVE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents")
    created_at = models.DateTimeField("fecha de carga", auto_now_add=True)
    updated_at = models.DateTimeField("última actualización", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "documento"
        verbose_name_plural = "documentos"

    def __str__(self):
        return self.title

    @property
    def filename(self):
        return Path(self.file.name).name

    def get_absolute_url(self):
        return reverse("document-detail", kwargs={"pk": self.pk})


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField("versión")
    file = models.FileField(
        "archivo",
        upload_to="document_versions/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "txt"])],
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_versions")
    created_at = models.DateTimeField("fecha de carga", auto_now_add=True)

    class Meta:
        ordering = ["-number"]
        constraints = [models.UniqueConstraint(fields=["document", "number"], name="unique_document_version")]
        verbose_name = "versión de documento"
        verbose_name_plural = "versiones de documentos"

    def __str__(self):
        return f"{self.document} — v{self.number}"
