from django.contrib import admin
from .models import APIToken


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "token_prefix", "is_active", "created_at", "last_used_at", "expires_at"]
    list_filter = ["is_active", "user"]
    readonly_fields = ["token_prefix", "created_at", "last_used_at", "last_used_ip"]
    exclude = ["token_hash"]
