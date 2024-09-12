from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0002_remove_old_tables'),  # Make sure this matches your initial migration
    ]

    operations = [

        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_team CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_team_players CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_teammember CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
    