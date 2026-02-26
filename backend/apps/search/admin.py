from django.contrib import admin

from apps.search.models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "query", "created_at"]
    list_filter = ["user"]
    search_fields = ["query", "user__username"]
    raw_id_fields = ["user"]
    readonly_fields = ["user", "query", "kb_ids", "created_at"]
    date_hierarchy = "created_at"
