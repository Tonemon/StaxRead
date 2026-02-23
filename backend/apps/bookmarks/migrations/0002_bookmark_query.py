from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmarks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookmark',
            name='query',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
