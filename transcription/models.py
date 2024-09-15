from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re
import html
import unicodedata
import random
import string
from django.core.exceptions import ValidationError
models.SlugField(max_length=255)

from django.db import models

class ClassCode(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100, default="French Class")
    assignments = models.ManyToManyField('Assignment', blank=True, related_name='class_codes')
    flashcard_sets = models.ManyToManyField('FlashcardSet', blank=True, related_name='class_codes')

    def save(self, *args, **kwargs):
        if not self.code:
            # Generate a new 5-digit uppercase code
            while True:
                new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                if not ClassCode.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        else:
            # Ensure the code is always 5 characters and uppercase
            self.code = self.code[:5].upper()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code
class Assignment(models.Model):
    LANGUAGE_CHOICES = [
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]

    title = models.CharField(max_length=200, default="Language Assignment")
    description = models.TextField(default="This is a default description.")
    due_date = models.DateField(default="2024-08-26")
    class_code = models.ForeignKey(ClassCode, related_name='assignments_set', on_delete=models.CASCADE, default=2)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')

    def __str__(self):
        return self.title
class Question(models.Model):
    assignment = models.ForeignKey(Assignment, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField(default="What is your name?")
    expected_answer = models.TextField(default="My name is [NAME].")
    
    def __str__(self):
        return self.question_text
class FlashcardSet(models.Model):
    LANGUAGE_CHOICES = [
        ('fr', 'French'),
        ('es', 'Spanish'),
    ]
    name = models.CharField(max_length=200, default="Basic Language Words")
    class_code = models.ForeignKey(ClassCode, related_name='flashcard_sets_set', on_delete=models.CASCADE, default=2)
    bulk_flashcards = models.TextField(max_length=100000, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='fr')
    free_flow = models.BooleanField(default=False)  # New field for Free Flow option

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.bulk_flashcards = unicodedata.normalize('NFKC', self.bulk_flashcards)
        super().save(*args, **kwargs)
        if self.bulk_flashcards:
            self.create_flashcards_from_bulk()

    def create_flashcards_from_bulk(self):
        self.flashcards.all().delete()
        flashcard_pairs = re.split(r';\s*', self.bulk_flashcards.strip())
        for pair in flashcard_pairs:
            if ',' in pair:
                french_word, english_translation = pair.split(',', 1)
                french_word = self.clean_text(french_word)
                english_translation = self.clean_text(english_translation)
                Flashcard.objects.create(
                    flashcard_set=self,
                    french_word=french_word,
                    english_translation=english_translation
                )

    @staticmethod
    def clean_text(text):
        text = html.unescape(text)
        text = unicodedata.normalize('NFKC', text)
        text = text.replace('&#x27;', "'").replace('&apos;', "'")
        return text.strip()


class Flashcard(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, related_name='flashcards', on_delete=models.CASCADE)
    french_word = models.TextField()
    english_translation = models.TextField()

    def __str__(self):
        return f"{self.french_word} - {self.english_translation}"

    def save(self, *args, **kwargs):
        self.french_word = FlashcardSet.clean_text(self.french_word)
        self.english_translation = FlashcardSet.clean_text(self.english_translation)
        super().save(*args, **kwargs)



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

class UserQuestionProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assignment = models.ForeignKey('Assignment', on_delete=models.CASCADE)
    completed_questions = models.ManyToManyField('Question', related_name='completed_by_users')
    completed_percentage = models.FloatField(default=0)
    has_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'assignment')

    def update_progress(self):
        total_questions = self.assignment.questions.count()
        completed_questions = self.completed_questions.count()
        if total_questions > 0:
            self.completed_percentage = (completed_questions / total_questions) * 100
        else:
            self.completed_percentage = 0
        
        if self.completed_percentage == 100:
            self.has_completed = True
        
        self.save()

    def __str__(self):
        return f"{self.user.username}'s progress on {self.assignment.title}"
class UserQuestionAttempts(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    attempts_left = models.IntegerField(default=2)

    class Meta:
        unique_together = ('user', 'question')

    def __str__(self):
        return f"{self.user.username}'s attempts for question {self.question.id}"
    
class Game1(models.Model):
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='games')
    code = models.CharField(max_length=5, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        while True:
            code = ''.join([str(random.randint(0, 9)) for _ in range(5)])
            if not Game1.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f"Game for {self.flashcard_set.name} (Code: {self.code})"
    
class GameParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey('Game1', on_delete=models.CASCADE, related_name='participants')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.username} in {self.game.code}"