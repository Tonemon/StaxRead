from django.db import migrations, models


def backfill_owner_write_permission(apps, schema_editor):
    KBAccess = apps.get_model("knowledge", "KBAccess")
    # Set write permission for all owner entries on personal KBs
    owner_pks = []
    for entry in KBAccess.objects.select_related("kb").filter(kb__team__isnull=True):
        if str(entry.user_id) == str(entry.kb.owner_id):
            owner_pks.append(entry.pk)
    KBAccess.objects.filter(pk__in=owner_pks).update(permission="write")


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge", "0005_kb_gitcredential_team"),
    ]

    operations = [
        migrations.AddField(
            model_name="kbaccess",
            name="permission",
            field=models.CharField(
                choices=[("read", "Read"), ("write", "Write")],
                default="read",
                max_length=5,
            ),
        ),
        migrations.RunPython(
            backfill_owner_write_permission,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
