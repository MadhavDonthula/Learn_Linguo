from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0001_initial'),  # Make sure this matches your initial migration
    ]

    operations = [
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_game;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_gameparticipant;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_minigame;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_minigameresult;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_team;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_team_players;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS transcription_teammember;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
    