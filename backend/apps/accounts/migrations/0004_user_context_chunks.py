from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_theme"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="context_chunks",
            field=models.PositiveSmallIntegerField(default=1),
        ),
    ]
