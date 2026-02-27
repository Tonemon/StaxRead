import uuid
from django.conf import settings
from django.db import models


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        created_by = kwargs.pop("created_by", None)
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and created_by:
            TeamMembership.objects.create(team=self, user=created_by, role="owner")

    @classmethod
    def create(cls, name, created_by, **kwargs):
        """Use this instead of objects.create() to pass created_by."""
        team = cls(name=name, **kwargs)
        team.save(created_by=created_by)
        return team


class TeamMembership(models.Model):
    ROLE_CHOICES = [
        ("guest", "Guest"),
        ("member", "Member"),
        ("manager", "Manager"),
        ("admin", "Admin"),
        ("owner", "Owner"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="sent_team_invites",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("team", "user")]
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user} → {self.team} ({self.role})"
