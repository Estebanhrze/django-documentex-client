import csv

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from .forms import DocumentForm, DocumentVersionForm
from .models import Document, DocumentVersion


class DashboardView(TemplateView):
    template_name = "documents/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "document_count": Document.objects.count(),
            "version_count": DocumentVersion.objects.count(),
            "user_count": Document.objects.values("uploaded_by").distinct().count(),
            "recent_documents": Document.objects.select_related("uploaded_by")[:5],
        })
        return context


class DocumentListView(ListView):
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 12

    def get_queryset(self):
        return Document.objects.select_related("uploaded_by").annotate(version_total=Count("versions"))


class DocumentDetailView(DetailView):
    model = Document
    template_name = "documents/document_detail.html"

    def get_queryset(self):
        return Document.objects.select_related("uploaded_by").prefetch_related("versions__uploaded_by")


class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


class DocumentVersionCreateView(LoginRequiredMixin, CreateView):
    model = DocumentVersion
    form_class = DocumentVersionForm
    template_name = "documents/version_form.html"

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


def document_report(request):
    """Public aggregate report; it contains no uploader identities."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="reporte-documentos.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Métrica", "Valor"])
    writer.writerow(["Documentos", Document.objects.count()])
    writer.writerow(["Versiones", DocumentVersion.objects.count()])
    writer.writerow(["Documentos activos", Document.objects.filter(status=Document.Status.ACTIVE).count()])
    writer.writerow(["Documentos archivados", Document.objects.filter(status=Document.Status.ARCHIVED).count()])
    return response
