from rest_framework import serializers
from apps.bookmarks.models import Bookmark, BookmarkCategory


class BookmarkCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookmarkCategory
        fields = ["id", "name", "description", "tags", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class BookmarkSerializer(serializers.ModelSerializer):
    chunk_text = serializers.CharField(source="chunk.text", read_only=True)
    source_title = serializers.CharField(source="chunk.source.title", read_only=True)
    source_id = serializers.UUIDField(source="chunk.source.id", read_only=True)

    class Meta:
        model = Bookmark
        fields = ["id", "chunk", "chunk_text", "source_title", "source_id", "category", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "chunk_text", "source_title", "source_id", "created_at", "updated_at"]
