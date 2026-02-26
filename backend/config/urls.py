from django.conf import settings
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.knowledge.urls")),
    path("api/", include("apps.search.urls")),
    path("api/", include("apps.bookmarks.urls")),
    path("api/", include("apps.tokens.urls")),
    # OpenAPI schema + interactive docs (public — no auth required)
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[]), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema", permission_classes=[]), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema", permission_classes=[]), name="redoc"),
]

if settings.DEBUG:
    from django.contrib import admin
    urlpatterns = [path("django-admin/", admin.site.urls)] + urlpatterns
