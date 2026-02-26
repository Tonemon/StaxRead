from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='file_size_bytes',
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
