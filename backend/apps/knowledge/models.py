from django.conf import settings
from django.db import models

from apps.common.models import UUIDModel
from apps.knowledge.encryption import encrypt, decrypt


class KnowledgeBase(UUIDModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_knowledge_bases",
    )

    class Meta:
        unique_together = [("name", "owner")]
        ordering = ["name"]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            KBAccess.objects.create(kb=self, user=self.owner)

    def __str__(self) -> str:
        return f"{self.name} ({self.owner})"


class KBAccess(models.Model):
    kb = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="access_entries"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="kb_access_entries",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("kb", "user")]

    def __str__(self) -> str:
        return f"{self.user} → {self.kb}"


class Source(UUIDModel):
    class SourceType(models.TextChoices):
        PDF = "pdf", "PDF"
        EPUB = "epub", "EPUB"
        GIT = "git", "Git Repository"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        ERROR = "error", "Error"

    kb = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="sources"
    )
    title = models.CharField(max_length=500)
    source_type = models.CharField(max_length=10, choices=SourceType.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    # For PDF/EPUB: MinIO object key; for Git: repo URL
    storage_key = models.TextField(blank=True)
    # Git-specific fields
    git_url = models.URLField(blank=True)
    git_credential = models.ForeignKey(
        "GitCredential",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sources",
    )
    git_branch = models.CharField(max_length=255, blank=True, default="main")
    last_synced_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return f"{self.title} ({self.source_type})"


class Chunk(UUIDModel):
    kb = models.ForeignKey(
        KnowledgeBase, on_delete=models.CASCADE, related_name="chunks"
    )
    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, related_name="chunks"
    )
    text = models.TextField()
    chunk_index = models.PositiveIntegerField()
    # Metadata stored as JSON (page number, file path, etc.)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["source", "chunk_index"]
        unique_together = [("source", "chunk_index")]

    def __str__(self) -> str:
        return f"Chunk {self.chunk_index} of {self.source}"


class GitCredential(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="git_credentials",
    )
    label = models.CharField(max_length=255)
    pat_encrypted = models.TextField()

    class Meta:
        ordering = ["label"]

    def set_pat(self, plaintext: str) -> None:
        self.pat_encrypted = encrypt(plaintext)

    def get_pat(self) -> str:
        return decrypt(self.pat_encrypted)

    def __str__(self) -> str:
        return f"{self.label} ({self.user})"
