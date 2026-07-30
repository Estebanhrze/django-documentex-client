from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Document, DocumentVersion, Report


class DocumentAccessTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.user = get_user_model().objects.create_user(username="editor", password="safe-password-123")
        self.user.groups.add(Group.objects.get(name="Editor documental"))
        self.document = Document.objects.create(
            title="Contrato",
            file=SimpleUploadedFile("contrato.pdf", b"test content", content_type="application/pdf"),
            uploaded_by=self.user,
        )

    def tearDown(self):
        self.override.disable()
        self.media_dir.cleanup()

    def test_guest_cannot_access_reports_or_documents(self):
        self.assertRedirects(self.client.get(reverse("dashboard")), f"{reverse('login')}?next={reverse('dashboard')}")
        self.assertRedirects(self.client.get(reverse("document-list")), f"{reverse('login')}?next={reverse('document-list')}")
        self.assertRedirects(self.client.get(reverse("report-list")), f"{reverse('login')}?next={reverse('report-list')}")
        self.assertRedirects(self.client.get(reverse("document-report")), f"{reverse('login')}?next={reverse('document-report')}")

    def test_reviewer_can_view_documents_and_create_reports_but_cannot_modify_documents(self):
        reviewer = get_user_model().objects.create_user(username="reviewer", password="safe-password-123")
        reviewer.groups.add(Group.objects.get(name="Revisor documental"))
        response = self.client.post(reverse("login"), {"username": "reviewer", "password": "safe-password-123"})
        self.assertRedirects(response, reverse("report-list"))
        self.assertEqual(self.client.get(reverse("report-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("document-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("document-detail", args=[self.document.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("document-report")).status_code, 200)
        response = self.client.post(reverse("report-create"), {
            "title": "Revisión mensual",
            "description": "Reporte creado por el revisor.",
        })
        self.assertRedirects(response, reverse("report-list"))
        report = Report.objects.get(title="Revisión mensual")
        self.assertEqual(report.created_by, reviewer)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("document-create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("version-create", args=[self.document.pk])).status_code, 403)

    def test_root_displays_login_screen(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Iniciar sesión")
        self.assertNotContains(response, "Ir a modo revisión")

    @patch("documents.views.upload_document", return_value={"file_path": "documents/1/test.pdf", "file_name": "test.pdf", "file_type": "application/pdf", "file_size_kb": 1})
    def test_editor_can_create_version_edit_and_delete_document(self, _upload_document):
        self.client.force_login(self.user)
        response = self.client.post(reverse("document-create"), {
            "title": "Manual", "status": Document.Status.ACTIVE,
            "file": SimpleUploadedFile("manual.pdf", b"pdf", content_type="application/pdf"),
        })
        self.assertEqual(response.status_code, 302)
        uploaded = Document.objects.get(title="Manual")
        response = self.client.post(reverse("version-create", args=[uploaded.pk]), {
            "file": SimpleUploadedFile("manual-v2.pdf", b"pdf", content_type="application/pdf"),
        })
        self.assertRedirects(response, uploaded.get_absolute_url())
        self.assertEqual(DocumentVersion.objects.get(document=uploaded).number, 1)
        response = self.client.post(reverse("document-update", args=[uploaded.pk]), {
            "title": "Manual actualizado", "status": Document.Status.ARCHIVED,
        })
        self.assertRedirects(response, uploaded.get_absolute_url())
        response = self.client.post(reverse("document-delete", args=[uploaded.pk]))
        self.assertRedirects(response, reverse("document-list"))
        self.assertFalse(Document.objects.filter(pk=uploaded.pk).exists())