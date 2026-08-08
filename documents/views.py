import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import DocumentForm, DocumentVersionForm, ReportForm
from .models import Document, DocumentVersion, Report
from .services import DocumentsAPIError, create_download_url, upload_document


class DocumentexLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.has_perm("documents.add_document"):
            return super().get_success_url()
        if self.request.user.has_perm("documents.view_reports"):
            return reverse("report-list")
        if self.request.user.has_perm("documents.view_document"):
            return reverse("document-list")
        return reverse("report-list")


class DashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "documents/dashboard.html"
    permission_required = "documents.add_document"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "document_count": Document.objects.count(),
            "version_count": DocumentVersion.objects.count(),
            "user_count": get_user_model().objects.filter(is_active=True).count(),
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


class RemoteUploadMixin:
    def store_remote_file(self, form) -> bool:
        uploaded_file = form.cleaned_data.get("file")
        if not uploaded_file:
            return True
        try:
            remote_file = upload_document(uploaded_file, self.request.user.pk)
        except DocumentsAPIError as exc:
            form.add_error("file", str(exc))
            return False

        instance = form.instance
        instance.file = None
        instance.file_path = remote_file["file_path"]
        instance.file_name = remote_file["file_name"] or uploaded_file.name
        instance.file_type = remote_file["file_type"] or uploaded_file.content_type or "application/octet-stream"
        instance.file_size_kb = remote_file["file_size_kb"]
        return True


class DocumentCreateView(LoginRequiredMixin, PermissionRequiredMixin, RemoteUploadMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    permission_required = "documents.add_document"

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        if not self.store_remote_file(form):
            return self.form_invalid(form)
        return super().form_valid(form)


class DocumentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, RemoteUploadMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"
    permission_required = "documents.change_document"

    def form_valid(self, form):
        if not self.store_remote_file(form):
            return self.form_invalid(form)
        return super().form_valid(form)


class DocumentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Document
    template_name = "documents/document_confirm_delete.html"
    success_url = reverse_lazy("document-list")
    permission_required = "documents.delete_document"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.reports.exists():
            messages.error(
                request,
                "No se puede eliminar el documento porque tiene reportes vinculados. Puedes archivarlo para conservar la trazabilidad.",
            )
            return redirect(self.object.get_absolute_url())
        return super().post(request, *args, **kwargs)


class DocumentVersionCreateView(LoginRequiredMixin, PermissionRequiredMixin, RemoteUploadMixin, CreateView):
    model = DocumentVersion
    form_class = DocumentVersionForm
    template_name = "documents/version_form.html"
    permission_required = "documents.add_documentversion"

    def dispatch(self, request, *args, **kwargs):
        self.document = get_object_or_404(Document, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        latest_number = self.document.versions.order_by("-number").values_list("number", flat=True).first() or 0
        form.instance.document = self.document
        form.instance.number = latest_number + 1
        form.instance.uploaded_by = self.request.user
        if not self.store_remote_file(form):
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return self.document.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document"] = self.document
        return context


@login_required
@permission_required("documents.view_document", raise_exception=True)
def document_download(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if document.file_path:
        try:
            return redirect(create_download_url(document.file_path, request.user.pk))
        except DocumentsAPIError as exc:
            messages.error(request, str(exc))
            return redirect(document.get_absolute_url())
    if document.file:
        return redirect(document.file.url)
    messages.error(request, "El documento no tiene un archivo disponible.")
    return redirect(document.get_absolute_url())


@login_required
@permission_required("documents.view_document", raise_exception=True)
def document_preview(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if document.file_path:
        try:
            return redirect(create_download_url(document.file_path, request.user.pk))
        except DocumentsAPIError as exc:
            messages.error(request, str(exc))
            return redirect(document.get_absolute_url())
    if document.file:
        return redirect(document.file.url)
    messages.error(request, "El documento no tiene un archivo disponible.")
    return redirect(document.get_absolute_url())


@login_required
@permission_required("documents.view_document", raise_exception=True)
def version_download(request, pk):
    version = get_object_or_404(DocumentVersion.objects.select_related("document"), pk=pk)
    if version.file_path:
        try:
            return redirect(create_download_url(version.file_path, request.user.pk))
        except DocumentsAPIError as exc:
            messages.error(request, str(exc))
            return redirect(version.document.get_absolute_url())
    if version.file:
        return redirect(version.file.url)
    messages.error(request, "La versión no tiene un archivo disponible.")
    return redirect(version.document.get_absolute_url())


class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """Report catalogue for users explicitly allowed to consult reports."""

    template_name = "documents/report_list.html"
    permission_required = "documents.view_reports"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reports"] = Report.objects.select_related("created_by", "document")
        return context


class ReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm
    template_name = "documents/report_form.html"
    permission_required = "documents.add_report"
    success_url = reverse_lazy("report-list")

    def get_initial(self):
        initial = super().get_initial()
        document_id = self.request.GET.get("document")
        if document_id and Document.objects.filter(pk=document_id).exists():
            initial["document"] = document_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["report_documents"] = [
            {
                "id": document.pk,
                "title": document.title,
                "file_name": document.filename,
                "file_type": document.file_type,
                "updated_at": document.updated_at.strftime("%d/%m/%Y %H:%M"),
                "preview_url": reverse("document-preview", args=[document.pk]),
                "download_url": reverse("document-download", args=[document.pk]),
                "preview_kind": (
                    "pdf"
                    if document.file_type == "application/pdf" or document.filename.lower().endswith(".pdf")
                    else "text"
                    if document.file_type.startswith("text/") or document.filename.lower().endswith(".txt")
                    else "download"
                ),
            }
            for document in Document.objects.order_by("title")
            if document.file_path or document.file
        ]
        return context

    def form_valid(self, form):
        document = form.cleaned_data["document"]
        form.instance.document = document
        form.instance.reviewed_file_path = document.file_path
        form.instance.reviewed_file_name = document.filename
        form.instance.reviewed_document_updated_at = document.updated_at
        form.instance.created_by = self.request.user
        return super().form_valid(form)


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


@login_required
@permission_required("documents.view_reports", raise_exception=True)
def document_report(request):
    return csv_response("reporte-resumen-documentos.csv", ["Métrica", "Valor"], [
        ["Documentos", Document.objects.count()],
        ["Versiones", DocumentVersion.objects.count()],
        ["Documentos activos", Document.objects.filter(status=Document.Status.ACTIVE).count()],
        ["Documentos archivados", Document.objects.filter(status=Document.Status.ARCHIVED).count()],
    ])


@login_required
@permission_required("documents.view_reports", raise_exception=True)
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
