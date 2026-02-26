import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("knowledge", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="APIToken",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("token_prefix", models.CharField(max_length=9)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("last_used_ip", models.GenericIPAddressField(blank=True, null=True, unpack_ipv4=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="api_tokens", to=settings.AUTH_USER_MODEL)),
                ("knowledge_bases", models.ManyToManyField(blank=True, related_name="api_tokens", to="knowledge.knowledgebase")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
