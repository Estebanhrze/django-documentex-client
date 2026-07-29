import csv

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import DocumentForm, DocumentVersionForm
from .models import Document, DocumentVersion


class DocumentexLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.has_perm("documents.view_document"):
            return super().get_success_url()
        return reverse("report-list")


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "documents/dashboard.html"
    permission_required = "documents.view_document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "document_count": Document.objects.count(),
            "version_count": DocumentVersion.objects.count(),
            "user_count": Document.objects.values("uploaded_by").distinct().count(),
            "recent_documents": Document.objects.select_related("uploaded_by")[:5],
        })
        return context


class DocumentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 12
    permission_required = "documents.view_document"

    def get_queryset(self):
        return Document.objects.select_related("uploaded_by").annotate(version_total=Count("versions")).order_by("-created_at")


class DocumentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Document
    template_name = "documents/document_detail.html"
    permission_required = "documents.view_document"

    def get_queryset(self):
        return Document.objects.select_related("uploaded_by").prefetch_related("versions__uploaded_by")


class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    permission_required = "documents.add_document"

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    permission_required = "documents.change_document"


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Document
    template_name = "documents/document_confirm_delete.html"
    success_url = reverse_lazy("document-list")
    permission_required = "documents.delete_document"


class DocumentVersionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DocumentVersion
    form_class = DocumentVersionForm
    template_name = "documents/version_form.html"
    permission_required = "documents.add_documentversion"

    def dispatch(self, request, *args, **kwargs):
        self.document = Document.objects.get(pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        latest_number = self.document.versions.order_by("-number").values_list("number", flat=True).first() or 0
        form.instance.document = self.document
        form.instance.number = latest_number + 1
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.document.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        return context


class ReportListView(LoginRequiredMixin, TemplateView):
    """Authenticated report catalogue; a download starts only after selecting one."""

    template_name = "documents/report_list.html"


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


@login_required
def document_report(request):
    """Aggregate report without uploader identities."""
    return csv_response("reporte-resumen-documentos.csv", ["Métrica", "Valor"], [
        ["Documentos", Document.objects.count()],
        ["Versiones", DocumentVersion.objects.count()],
        ["Documentos activos", Document.objects.filter(status=Document.Status.ACTIVE).count()],
        ["Documentos archivados", Document.objects.filter(status=Document.Status.ARCHIVED).count()],
    ])


@login_required
def active_document_report(request):
    documents = Document.objects.filter(status=Document.Status.ACTIVE).annotate(version_total=Count("versions"))
    rows = (
        [document.title, document.get_status_display(), document.version_total, document.created_at.strftime("%d/%m/%Y")]
        for document in documents
    )
    return csv_response(
        "reporte-documentos-activos.csv",
        ["Nombre", "Estado", "Versiones", "Fecha"],
        rows,
    )
