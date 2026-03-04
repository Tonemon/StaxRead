from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_greeting_prefs"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="theme",
            field=models.CharField(
                choices=[("system", "System"), ("light", "Light"), ("dark", "Dark")],
                default="system",
                max_length=10,
            ),
        ),
    ]
