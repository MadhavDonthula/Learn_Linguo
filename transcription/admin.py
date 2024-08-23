from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render
from django.http import Http404
from .models import Assignment, QuestionAnswer, ClassCode, FlashcardSet, Flashcard, UserFlashcardProgress, UserClassEnrollment

# Register models
admin.site.register(Assignment)
admin.site.register(QuestionAnswer)

class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 1

@admin.register(FlashcardSet)
class FlashcardSetAdmin(admin.ModelAdmin):
    inlines = [FlashcardInline]
    fields = ('name', 'bulk_flashcards')

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('french_word', 'english_translation', 'flashcard_set')
    list_filter = ('flashcard_set',)

class ClassCodeAdmin(admin.ModelAdmin):
    filter_horizontal = ('assignments', 'flashcard_sets')

    def save_model(self, request, obj, form, change):
        # Ensure that at least one assignment and one flashcard set are associated with this class code
        if not obj.assignments.exists() or not obj.flashcard_sets.exists():
            self.message_user(request, "Class code must be associated with at least one assignment and one flashcard set", level=messages.ERROR)
            return
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('progress/<int:class_code_id>/', self.admin_site.admin_view(class_code_progress_view), name='class_code_progress'),
        ]
        return custom_urls + urls

# Define the class_code_progress_view outside of ClassCodeAdmin
def class_code_progress_view(request, class_code_id):
    try:
        class_code = ClassCode.objects.get(id=class_code_id)
    except ClassCode.DoesNotExist:
        raise Http404("Class code not found")

    assignments = class_code.assignments.all()
    flashcard_sets = class_code.flashcard_sets.all()
    students = UserClassEnrollment.objects.filter(class_code=class_code)

    data = []
    for enrollment in students:
        student = enrollment.user
        row = {'username': student.username}

        # Process assignment progress
        for assignment in assignments:
            progress = UserFlashcardProgress.objects.filter(user=student, flashcard_set__in=flashcard_sets).first()
            if progress:
                total_flashcards = Flashcard.objects.filter(flashcard_set__in=flashcard_sets).count()
                if total_flashcards > 0:
                    completion_percentage = (progress.completed_flashcards / total_flashcards) * 100
                    row[assignment.name] = f"{completion_percentage:.2f}%"
                else:
                    row[assignment.name] = 'No flashcards'
            else:
                row[assignment.name] = 'Not started'

        # Process flashcard progress
        for flashcard_set in flashcard_sets:
            progress = UserFlashcardProgress.objects.filter(user=student, flashcard_set=flashcard_set).first()
            if progress:
                total_flashcards = Flashcard.objects.filter(flashcard_set=flashcard_set).count()
                if total_flashcards > 0:
                    completion_percentage = (progress.completed_flashcards / total_flashcards) * 100
                    row[flashcard_set.name] = f"{completion_percentage:.2f}%"
                else:
                    row[flashcard_set.name] = 'No flashcards'
            else:
                row[flashcard_set.name] = 'Not started'

        data.append(row)

    context = {
        'class_code': class_code,
        'data': data,
        'assignments': assignments,
        'flashcard_sets': flashcard_sets,
    }
    return render(request, 'transcription/class_code_progress.html', context)

# Register ClassCodeAdmin
admin.site.register(ClassCode, ClassCodeAdmin)

# Optional: Register UserFlashcardProgressAdmin
@admin.register(UserFlashcardProgress)
class UserFlashcardProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'flashcard_set', 'completed_flashcards')
    list_filter = ('user', 'flashcard_set')
    search_fields = ('user__username', 'flashcard_set__name')

    def save_model(self, request, obj, form, change):
        if obj.completed_flashcards < 0:
            self.message_user(request, "Completed flashcards cannot be negative", level=messages.ERROR)
            return
        super().save_model(request, obj, form, change)
