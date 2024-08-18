from django.contrib import admin

from .models import Assignment, QuestionAnswer, ClassCode, FlashcardSet, Flashcard

admin.site.register(Assignment)
admin.site.register(QuestionAnswer)
admin.site.register(ClassCode)


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