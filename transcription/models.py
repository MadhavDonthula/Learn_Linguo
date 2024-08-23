from django.db import models
from django.contrib.auth.models import User
import re

class Transcription(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='transcriptions', null=True, blank=True)
    audio_file = models.FileField(upload_to="audio/")
    transcribed_text = models.TextField()

    def __str__(self):
        return f"Transcription {self.id}"

class Assignment(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class QuestionAnswer(models.Model):
    assignment = models.ForeignKey(Assignment, related_name="questions", on_delete=models.CASCADE)
    question = models.TextField(max_length=1000)
    answer = models.TextField(max_length=1000)

    def __str__(self):
        return f"Question: {self.question[:30]}"

class ClassCode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    assignments = models.ManyToManyField(Assignment, related_name="class_codes")
    flashcard_sets = models.ManyToManyField("FlashcardSet", related_name="class_codes")

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        # Ensure that at least one assignment and one flashcard set are associated with this class code

        super().save(*args, **kwargs)

class UserClassEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_enrollments')
    class_code = models.ForeignKey(ClassCode, on_delete=models.CASCADE, related_name='user_enrollments')

    def __str__(self):
        return f"{self.user.username} enrolled in {self.class_code.code}"

class FlashcardSet(models.Model):
    name = models.CharField(max_length=100)
    bulk_flashcards = models.TextField(max_length=100000, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.bulk_flashcards:
            self.create_flashcards_from_bulk()

    def create_flashcards_from_bulk(self):
        self.flashcards.all().delete()
        flashcard_pairs = re.split(r';\s*', self.bulk_flashcards.strip())
        for pair in flashcard_pairs:
            if ',' in pair:
                french, english = pair.split(',', 1)
                Flashcard.objects.create(
                    flashcard_set=self,
                    french_word=french.strip(),
                    english_translation=english.strip()
                )

class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, related_name='flashcards', on_delete=models.CASCADE)
    french_word = models.CharField(max_length=200)
    english_translation = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.french_word} - {self.english_translation}"
