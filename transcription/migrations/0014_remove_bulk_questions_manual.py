# Generated manually to fix bulk_questions field issue

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("transcription", "0013_alter_interpersonalquestion_audio_file"),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE transcription_assignment DROP COLUMN IF EXISTS bulk_questions;",
            reverse_sql="ALTER TABLE transcription_assignment ADD COLUMN bulk_questions TEXT;"
        ),
    ] 