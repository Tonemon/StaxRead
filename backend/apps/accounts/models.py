import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class GreetingDisplay(models.TextChoices):
        USERNAME = "username", "Username"
        FULL_NAME = "full_name", "Full name"
        FIRST_NAME = "first_name", "First name only"

    class Theme(models.TextChoices):
        SYSTEM = "system", "System"
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"

    show_greeting = models.BooleanField(default=True)
    greeting_display = models.CharField(
        max_length=20,
        choices=GreetingDisplay.choices,
        default=GreetingDisplay.USERNAME,
    )
    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.SYSTEM,
    )
