from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.bookmarks.views import BookmarkCategoryViewSet, BookmarkViewSet

router = DefaultRouter()
router.register(r"bookmark-categories", BookmarkCategoryViewSet, basename="bookmarkcategory")
router.register(r"bookmarks", BookmarkViewSet, basename="bookmark")

urlpatterns = [
    path("", include(router.urls)),
]
