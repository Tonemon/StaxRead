from django.conf import settings
from django.db import models

from apps.common.models import UUIDModel


class BookmarkCategory(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmark_categories",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)

    class Meta:
        ordering = ["name"]
        unique_together = [("user", "name")]

    def __str__(self):
        return f"{self.name} ({self.user})"


class Bookmark(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    chunk = models.ForeignKey(
        "knowledge.Chunk",
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    category = models.ForeignKey(
        BookmarkCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bookmarks",
    )
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("user", "chunk")]

    def __str__(self):
        return f"Bookmark by {self.user} on {self.chunk}"
