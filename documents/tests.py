from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
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
        permissions = Permission.objects.filter(codename__in=[
            "view_document", "add_document", "change_document", "delete_document", "add_documentversion",
        ])
        self.user.user_permissions.add(*permissions)
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

    def test_report_only_user_is_redirected_to_reports_after_login(self):
        report_user = get_user_model().objects.create_user(username="reporter", password="safe-password-123")
        response = self.client.post(reverse("login"), {"username": "reporter", "password": "safe-password-123"})
        self.assertRedirects(response, reverse("report-list"))
        self.assertEqual(self.client.get(reverse("report-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)

    def test_root_displays_login_screen(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Iniciar sesión")
        self.assertNotContains(response, "Ir a modo revisión")

    def test_authorized_user_can_create_version_edit_and_delete_document(self):
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
