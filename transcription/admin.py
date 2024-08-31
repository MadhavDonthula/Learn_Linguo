from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.html import format_html
from .models import Assignment, ClassCode, FlashcardSet, Flashcard, UserFlashcardProgress, UserClassEnrollment, Question, UserQuestionProgress
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import render, get_object_or_404


# Register models


class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 1
@admin.register(FlashcardSet)
class FlashcardSetAdmin(admin.ModelAdmin):
    inlines = [FlashcardInline]
    fields = ('name', 'bulk_flashcards')

    def save_model(self, request, obj, form, change):
        obj.bulk_flashcards = FlashcardSet.clean_text(obj.bulk_flashcards)
        super().save_model(request, obj, form, change)

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('french_word', 'english_translation', 'flashcard_set')
    list_filter = ('flashcard_set',)

    def save_model(self, request, obj, form, change):
        obj.french_word = FlashcardSet.clean_text(obj.french_word)
        obj.english_translation = FlashcardSet.clean_text(obj.english_translation)
        super().save_model(request, obj, form, change)
        
class ClassCodeAdmin(admin.ModelAdmin):
    filter_horizontal = ('assignments', 'flashcard_sets')
    list_display = ('get_class_name', 'get_class_code', 'view_progress_link')

    def get_class_name(self, obj):
        return f"Class with Code: {obj.code}"
    get_class_name.short_description = 'Class Name'

    def get_class_code(self, obj):
        return obj.code
    get_class_code.short_description = 'Class Code'

    def view_progress_link(self, obj):
        url = reverse('admin:class_code_progress', args=[obj.id])
        return format_html('<a class="button" href="{}">View Progress</a>', url)
    view_progress_link.short_description = 'Class Progress'
    view_progress_link.allow_tags = True

    def save_model(self, request, obj, form, change):
        # Save the ClassCode instance to get its ID
        super().save_model(request, obj, form, change)
        # Now save the many-to-many relationships
        form.save_m2m()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('progress/<int:class_code_id>/', self.admin_site.admin_view(class_code_progress_view), name='class_code_progress'),
        ]
        return custom_urls + urls

# Register the ClassCodeAdmin with the model
admin.site.register(ClassCode, ClassCodeAdmin)
def class_code_progress_view(request, class_code_id):
    try:
        class_code = ClassCode.objects.get(id=class_code_id)
    except ClassCode.DoesNotExist:
        raise Http404("Class code not found")
    
    flashcard_sets = class_code.flashcard_sets.all()
    assignments = class_code.assignments.all()
    students = UserClassEnrollment.objects.filter(class_code=class_code).select_related('user')
    
    data = []
    headers = ['Username']
    
    for flashcard_set in flashcard_sets:
        headers.append(f"Flashcards: {flashcard_set.name}")
    
    for assignment in assignments:
        headers.append(f"Assignment: {assignment.title}")
    
    for student in students:
        student_progress = {'Username': student.user.username}
        
        for flashcard_set in flashcard_sets:
            progress = UserFlashcardProgress.objects.filter(user=student.user, flashcard_set=flashcard_set).first()
            if progress is None:
                student_progress[f"Flashcards: {flashcard_set.name}"] = 'Not started'
            else:
                if progress.has_completed:
                    student_progress[f"Flashcards: {flashcard_set.name}"] = "100%"
                elif progress.completed_percentage is not None:
                    student_progress[f"Flashcards: {flashcard_set.name}"] = f"{round(progress.completed_percentage)}%"
                else:
                    student_progress[f"Flashcards: {flashcard_set.name}"] = 'In progress'
        
        for assignment in assignments:
            progress = UserQuestionProgress.objects.filter(user=student.user, assignment=assignment).first()
            if progress is None:
                student_progress[f"Assignment: {assignment.title}"] = 'Not started'
            else:
                total_questions = assignment.questions.count()
                completed_questions = progress.completed_questions.count()
                if total_questions > 0:
                    percentage = round((completed_questions / total_questions) * 100)
                    student_progress[f"Assignment: {assignment.title}"] = f"{completed_questions}/{total_questions} ({percentage}%)"
                else:
                    student_progress[f"Assignment: {assignment.title}"] = 'No questions'
        
        data.append(student_progress)
    
    context = {
        'class_code': class_code,
        'data': data,
        'headers': headers,
    }
    return render(request, 'transcription/class_code_progress.html', context)

# User admin with class progress link
class UserAdmin(BaseUserAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/class-progress/', self.admin_site.admin_view(select_class_view), name='select_class'),
        ]
        return custom_urls + urls

    def class_progress_link(self, obj):
        url = reverse('admin:select_class', args=[obj.id])
        return format_html('<a class="button" href="{}">Class Progress</a>', url)
    class_progress_link.short_description = 'Class Progress'
    class_progress_link.allow_tags = True

    list_display = BaseUserAdmin.list_display + ('class_progress_link',)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Define the select_class_view function
def select_class_view(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404("User not found")

    if request.method == "POST":
        class_code_id = request.POST.get("class_code")
        return redirect(reverse('admin:class_code_progress', args=[class_code_id]))

    class_codes = ClassCode.objects.filter(user_enrollments__user=user)
    return render(request, 'admin/select_class.html', {'user': user, 'class_codes': class_codes})

@admin.register(UserFlashcardProgress)
class UserFlashcardProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'flashcard_set', 'completed_flashcards', 'has_completed')
    list_filter = ('user', 'flashcard_set', 'has_completed')
    search_fields = ('user__username', 'flashcard_set__name')

    def save_model(self, request, obj, form, change):
        if obj.completed_flashcards < 0:
            self.message_user(request, "Completed flashcards cannot be negative", level=messages.ERROR)
            return
        if not obj.has_completed:
            # If progress is marked as completed, ensure completed_flashcards reflects total flashcards
            if obj.completed_flashcards >= Flashcard.objects.filter(flashcard_set=obj.flashcard_set).count():
                obj.mark_completed()
        super().save_model(request, obj, form, change)

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    max_num = 6  # Set the max number of questions per assignment to 6

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    fields = ('title', 'description', 'due_date')