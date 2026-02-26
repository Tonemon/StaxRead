from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0002_knowledgebase_source_kbaccess_chunk'),
    ]

    operations = [
        migrations.AddField(
            model_name='kbaccess',
            name='status',
            field=models.CharField(
                choices=[('pending', 'Pending'), ('accepted', 'Accepted')],
                default='accepted',
                max_length=10,
            ),
        ),
    ]
