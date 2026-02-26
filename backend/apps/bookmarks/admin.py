from django.contrib import admin

from apps.bookmarks.models import Bookmark, BookmarkCategory


@admin.register(BookmarkCategory)
class BookmarkCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "created_at"]
    list_filter = ["user"]
    search_fields = ["name", "user__username"]
    raw_id_fields = ["user"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ["user", "chunk", "category", "created_at"]
    list_filter = ["category"]
    search_fields = ["user__username", "note", "query"]
    raw_id_fields = ["user", "chunk", "category"]
    readonly_fields = ["created_at", "updated_at"]
