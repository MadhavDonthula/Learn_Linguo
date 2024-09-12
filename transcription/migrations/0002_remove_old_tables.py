from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0001_initial'),  # Make sure this matches your initial migration
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_game CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_gameparticipant CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_minigame CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_minigameresult CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
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
    