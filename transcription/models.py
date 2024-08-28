from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re
from django.db import models

class ClassCode(models.Model):
    code = models.CharField(max_length=10, unique=True, default="ABC1234567")
    name = models.CharField(max_length=100, default="French Class")
    assignments = models.ManyToManyField('Assignment', blank=True, related_name='class_codes')
    flashcard_sets = models.ManyToManyField('FlashcardSet', blank=True, related_name='class_codes')

    def save(self, *args, **kwargs):
        # Save the instance first to get an ID
        super().save(*args, **kwargs)
        # Now the instance has an ID, so you can safely assign many-to-many relationships

    def __str__(self):
        return self.code
class Assignment(models.Model):
    title = models.CharField(max_length=200, default="French Assignment")
    description = models.TextField(default="This is a default description.")
    due_date = models.DateField(default="2024-08-26")
    class_code = models.ForeignKey(ClassCode, related_name='assignments_set', on_delete=models.CASCADE, default=2)

    def __str__(self):
        return self.title

class Question(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField(default="What is your name?")
    answer = models.TextField(default="My name is Jean.")

    def __str__(self):
        return self.question_text

class FlashcardSet(models.Model):
    name = models.CharField(max_length=200, default="Basic French Words")
    class_code = models.ForeignKey(ClassCode, related_name='flashcard_sets_set', on_delete=models.CASCADE, default=2)
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
    french_word = models.CharField(max_length=200, default="Bonjour")
    english_translation = models.CharField(max_length=200, default="Hello")

    def __str__(self):
        return f'{self.french_word} - {self.english_translation}'


class UserClassEnrollment(models.Model):
    user = models.ForeignKey(User, related_name='class_enrollments', on_delete=models.CASCADE)
    class_code = models.ForeignKey(ClassCode, related_name='students', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'class_code')

    def __str__(self):
        return f'{self.user.username} enrolled in {self.class_code.code}'

# models.py
class UserFlashcardProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE)
    completed_flashcards = models.IntegerField(default=0)
    completed_percentage = models.FloatField(default=0)  # Ensure this field exists
    has_completed = models.BooleanField(default=False)
    current_flashcard_index = models.IntegerField(default=0)  # Add this field

    
    class Meta:
        unique_together = ('user', 'flashcard_set')
    def mark_completed(self):
        self.has_completed = True
        self.completed_percentage = 100
        self.save()


    def __str__(self):
        return f'{self.user.username} progress in {self.flashcard_set.name}'

    def reset_progress(self):
        """Resets the progress for practice but retains the completed status and highest percentage."""
        self.completed_flashcards = 0
        self.save()

    def update_progress(self):
        """Updates the completion percentage and highest percentage."""
        total_flashcards = Flashcard.objects.filter(flashcard_set=self.flashcard_set).count()
        if total_flashcards > 0:
            percentage = round((self.completed_flashcards / total_flashcards) * 100)
            if percentage > self.highest_percentage:
                self.highest_percentage = percentage
        self.save()