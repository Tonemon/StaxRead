import hashlib
import secrets
import uuid

from django.conf import settings
from django.db import models


TOKEN_PREFIX = "stax_"


def _generate_token() -> str:
    return TOKEN_PREFIX + secrets.token_hex(32)


# SHA-256 without a salt is acceptable here: tokens carry 256 bits of
# entropy, making rainbow-table and brute-force attacks computationally
# infeasible. This is the standard approach for high-entropy API tokens.
def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class APIToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_tokens",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Stored hash — raw token is NEVER saved
    token_hash = models.CharField(max_length=64, unique=True)
    # First 9 chars of raw token shown in UI for identification (stax_ + 4 hex)
    token_prefix = models.CharField(max_length=9)

    # Scope: empty = all of user's accessible KBs; non-empty = specific KBs only
    knowledge_bases = models.ManyToManyField(
        "knowledge.KnowledgeBase",
        blank=True,
        related_name="api_tokens",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True, unpack_ipv4=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"

    @classmethod
    def create_token(cls, user, name, description="", knowledge_bases=None, expires_at=None):
        """
        Generate a new token. Returns (instance, raw_token).
        raw_token is shown to the user ONCE and never stored.
        """
        raw = _generate_token()
        instance = cls.objects.create(
            user=user,
            name=name,
            description=description,
            token_hash=_hash_token(raw),
            token_prefix=raw[:9],
            expires_at=expires_at,
        )
        if knowledge_bases:
            instance.knowledge_bases.set(knowledge_bases)
        return instance, raw

    @classmethod
    def authenticate(cls, raw_token: str):
        """Look up an active, non-expired token by its raw value. Returns APIToken or None."""
        from django.utils import timezone

        token_hash = _hash_token(raw_token)
        try:
            token = cls.objects.select_related("user").prefetch_related("knowledge_bases").get(
                token_hash=token_hash,
                is_active=True,
            )
        except cls.DoesNotExist:
            return None
        if token.expires_at and token.expires_at < timezone.now():
            return None
        return token
