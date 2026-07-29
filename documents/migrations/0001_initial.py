# Generated manually to keep the initial schema under version control.
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="título")),
                ("file", models.FileField(upload_to="documents/%Y/%m/", validators=[django.core.validators.FileExtensionValidator(["pdf", "doc", "docx", "txt"])], verbose_name="archivo")),
                ("status", models.CharField(choices=[("active", "Activo"), ("archived", "Archivado")], default="active", max_length=10, verbose_name="estado")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="fecha de carga")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="última actualización")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_documents", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "documento", "verbose_name_plural": "documentos", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DocumentVersion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField(verbose_name="versión")),
                ("file", models.FileField(upload_to="document_versions/%Y/%m/", validators=[django.core.validators.FileExtensionValidator(["pdf", "doc", "docx", "txt"])], verbose_name="archivo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="fecha de carga")),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="documents.document")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_versions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "versión de documento", "verbose_name_plural": "versiones de documentos", "ordering": ["-number"]},
        ),
        migrations.AddConstraint(model_name="documentversion", constraint=models.UniqueConstraint(fields=("document", "number"), name="unique_document_version")),
    ]
