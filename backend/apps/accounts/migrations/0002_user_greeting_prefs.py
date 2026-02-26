from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='show_greeting',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='greeting_display',
            field=models.CharField(
                choices=[('username', 'Username'), ('full_name', 'Full name'), ('first_name', 'First name only')],
                default='username',
                max_length=20,
            ),
        ),
    ]
