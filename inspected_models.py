# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class TranscriptionAssignment(models.Model):
    id = models.BigAutoField(primary_key=True)
    class_code = models.ForeignKey('TranscriptionClasscode', models.DO_NOTHING)
    description = models.TextField()
    due_date = models.DateField()
    title = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'transcription_assignment'


class TranscriptionClasscode(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'transcription_classcode'


class TranscriptionClasscodeAssignments(models.Model):
    id = models.BigAutoField(primary_key=True)
    classcode = models.ForeignKey(TranscriptionClasscode, models.DO_NOTHING)
    assignment = models.ForeignKey(TranscriptionAssignment, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'transcription_classcode_assignments'
        unique_together = (('classcode', 'assignment'),)


class TranscriptionClasscodeFlashcardSets(models.Model):
    id = models.BigAutoField(primary_key=True)
    classcode = models.ForeignKey(TranscriptionClasscode, models.DO_NOTHING)
    flashcardset = models.ForeignKey('TranscriptionFlashcardset', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'transcription_classcode_flashcard_sets'
        unique_together = (('classcode', 'flashcardset'),)


class TranscriptionFlashcard(models.Model):
    id = models.BigAutoField(primary_key=True)
    french_word = models.CharField(max_length=200)
    english_translation = models.CharField(max_length=200)
    flashcard_set = models.ForeignKey('TranscriptionFlashcardset', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'transcription_flashcard'


class TranscriptionFlashcardset(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    class_code = models.ForeignKey(TranscriptionClasscode, models.DO_NOTHING)
    bulk_flashcards = models.TextField()

    class Meta:
        managed = False
        db_table = 'transcription_flashcardset'


class TranscriptionGame(models.Model):
    id = models.BigAutoField(primary_key=True)
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    class_code = models.ForeignKey(TranscriptionClasscode, models.DO_NOTHING)
    flashcard_set = models.ForeignKey(TranscriptionFlashcardset, models.DO_NOTHING)
    is_ended = models.BooleanField()
    started_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transcription_game'


class TranscriptionGameparticipant(models.Model):
    id = models.BigAutoField(primary_key=True)
    joined_at = models.DateTimeField()
    game = models.ForeignKey(TranscriptionGame, models.DO_NOTHING)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'transcription_gameparticipant'
        unique_together = (('user', 'game'),)


class TranscriptionMinigame(models.Model):
    id = models.BigAutoField(primary_key=True)
    game_type = models.CharField(max_length=20)
    game = models.ForeignKey(TranscriptionGame, models.DO_NOTHING)
    winner = models.ForeignKey(AuthUser, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transcription_minigame'


class TranscriptionMinigameresult(models.Model):
    id = models.BigAutoField(primary_key=True)
    medal = models.CharField(max_length=10)
    score = models.IntegerField()
    mini_game = models.ForeignKey(TranscriptionMinigame, models.DO_NOTHING)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'transcription_minigameresult'


class TranscriptionQuestion(models.Model):
    id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(TranscriptionAssignment, models.DO_NOTHING)
    question_text = models.TextField()
    expected_answer = models.TextField()

    class Meta:
        managed = False
        db_table = 'transcription_question'


class TranscriptionReferencetext(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.TextField()

    class Meta:
        managed = False
        db_table = 'transcription_referencetext'


class TranscriptionTeam(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    score = models.IntegerField()
