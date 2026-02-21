from rest_framework.viewsets import ModelViewSet

from apps.bookmarks.models import Bookmark, BookmarkCategory
from apps.bookmarks.serializers import BookmarkCategorySerializer, BookmarkSerializer


class BookmarkCategoryViewSet(ModelViewSet):
    serializer_class = BookmarkCategorySerializer

    def get_queryset(self):
        return BookmarkCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookmarkViewSet(ModelViewSet):
    serializer_class = BookmarkSerializer

    def get_queryset(self):
        qs = Bookmark.objects.filter(user=self.request.user)
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
