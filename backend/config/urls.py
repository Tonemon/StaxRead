from django.conf import settings
from django.urls import path, include

urlpatterns = [
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.knowledge.urls")),
    path("api/", include("apps.search.urls")),
    path("api/", include("apps.bookmarks.urls")),
    path("api/", include("apps.tokens.urls")),
]

if settings.DEBUG:
    from django.contrib import admin
    urlpatterns = [path("django-admin/", admin.site.urls)] + urlpatterns
