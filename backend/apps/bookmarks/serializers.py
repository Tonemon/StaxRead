from rest_framework import serializers
from apps.bookmarks.models import Bookmark, BookmarkCategory


class BookmarkCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkCategory
        fields = ["id", "name", "description", "tags", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["id", "chunk", "category", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
