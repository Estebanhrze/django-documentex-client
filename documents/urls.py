from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("documentos/", views.DocumentListView.as_view(), name="document-list"),
    path("documentos/nuevo/", views.DocumentCreateView.as_view(), name="document-create"),
    path("documentos/<int:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
    path("documentos/<int:pk>/version/", views.DocumentVersionCreateView.as_view(), name="version-create"),
    path("reportes/documentos.csv", views.document_report, name="document-report"),
]
