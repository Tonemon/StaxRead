from django.conf import settings
from django.db import models

from apps.common.models import UUIDModel
from apps.knowledge.encryption import encrypt, decrypt


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
