from django.contrib import admin

from apps.knowledge.models import Chunk, GitCredential, KBAccess, KnowledgeBase, Source


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name", "description", "owner__username"]
    raw_id_fields = ["owner"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"


@admin.register(KBAccess)
class KBAccessAdmin(admin.ModelAdmin):
    list_display = ["kb", "user", "status", "granted_at"]
    list_filter = ["status"]
    search_fields = ["kb__name", "user__username"]
    raw_id_fields = ["kb", "user"]


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ["title", "kb", "source_type", "status", "created_at"]
    list_filter = ["source_type", "status"]
    search_fields = ["title", "kb__name", "git_url"]
    raw_id_fields = ["kb", "git_credential"]
    readonly_fields = ["storage_key", "error_message", "last_synced_at", "created_at", "updated_at"]
    date_hierarchy = "created_at"


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ["id", "source", "kb", "chunk_index", "created_at"]
    list_filter = ["kb"]
    search_fields = ["text", "source__title", "kb__name"]
    raw_id_fields = ["source", "kb"]
    readonly_fields = ["text", "metadata", "created_at", "updated_at"]
    # Avoid expensive COUNT(*) on potentially large tables
    show_full_result_count = False


@admin.register(GitCredential)
class GitCredentialAdmin(admin.ModelAdmin):
    list_display = ["label", "user", "created_at"]
    search_fields = ["label", "user__username"]
    raw_id_fields = ["user"]
    # Never expose the encrypted PAT value
    exclude = ["pat_encrypted"]
    readonly_fields = ["created_at", "updated_at"]
