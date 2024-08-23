from django.contrib import admin, messages
from .models import Assignment, QuestionAnswer, ClassCode, FlashcardSet, Flashcard

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

class ClassCodeAdmin(admin.ModelAdmin):
    filter_horizontal = ('assignments', 'flashcard_sets')

    def save_model(self, request, obj, form, change):
        # Ensure that at least one assignment and one flashcard set are associated with this class code
 
        super().save_model(request, obj, form, change)

admin.site.register(ClassCode, ClassCodeAdmin)
