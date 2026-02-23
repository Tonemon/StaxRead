from rest_framework import status
from rest_framework.response import Response
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
        qs = Bookmark.objects.filter(user=self.request.user).select_related("chunk__source")
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        obj, created = Bookmark.objects.update_or_create(
            user=request.user,
            chunk=validated["chunk"],
            defaults={
                "category": validated.get("category"),
                "note": validated.get("note", ""),
                "query": validated.get("query", ""),
            },
        )
        out = self.get_serializer(obj)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(out.data, status=code)
