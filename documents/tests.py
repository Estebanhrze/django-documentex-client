from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Document, DocumentVersion


class DocumentAccessTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.override.enable()
        self.user = get_user_model().objects.create_user(username="editor", password="safe-password-123")
        self.document = Document.objects.create(
            title="Contrato",
            file=SimpleUploadedFile("contrato.pdf", b"test content", content_type="application/pdf"),
            uploaded_by=self.user,
        )

    def tearDown(self):
        self.override.disable()
        self.media_dir.cleanup()

    def test_visitor_can_review_dashboard_and_download_report(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        report = self.client.get(reverse("document-report"))
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report["Content-Type"], "text/csv; charset=utf-8")

    def test_root_displays_login_screen(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Iniciar sesión")
        self.assertContains(response, "Ingresar al sistema")

    def test_visitor_cannot_upload(self):
        response = self.client.get(reverse("document-create"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('document-create')}")

    def test_authenticated_user_can_upload_document_and_version(self):
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
