from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("documentos/", views.DocumentListView.as_view(), name="document-list"),
    path("documentos/nuevo/", views.DocumentCreateView.as_view(), name="document-create"),
    path("documentos/<int:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
    path("documentos/<int:pk>/editar/", views.DocumentUpdateView.as_view(), name="document-update"),
    path("documentos/<int:pk>/eliminar/", views.DocumentDeleteView.as_view(), name="document-delete"),
    path("documentos/<int:pk>/descargar/", views.document_download, name="document-download"),
    path("documentos/<int:pk>/version/", views.DocumentVersionCreateView.as_view(), name="version-create"),
    path("versiones/<int:pk>/descargar/", views.version_download, name="version-download"),
    path("reportes/", views.ReportListView.as_view(), name="report-list"),
    path("reportes/resumen-documentos.csv", views.document_report, name="document-report"),
    path("reportes/documentos-activos.csv", views.active_document_report, name="active-document-report"),
]