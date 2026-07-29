from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from documents.views import DocumentexLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", DocumentexLoginView.as_view(), name="login"),
    path("", include("documents.urls")),
    path("cuenta/iniciar-sesion/", RedirectView.as_view(pattern_name="login")),
    path("cuenta/cerrar-sesion/", auth_views.LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
