from django.urls import path, include


urlpatterns = [
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.knowledge.urls")),
    path("api/", include("apps.search.urls")),
    path("api/", include("apps.bookmarks.urls")),
]
