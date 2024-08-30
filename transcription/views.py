from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tempfile import NamedTemporaryFile
import base64
import json
import string
import re

from openai import OpenAI
from .models import Assignment, ClassCode, FlashcardSet, Flashcard, UserClassEnrollment, UserFlashcardProgress, Question, UserQuestionProgress
from .forms import CreateUserForm

from django.contrib.auth.models import User


def registerPage(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get("username")
            messages.success(request, f"Account was created for {user}")
            return redirect("login")
    context = {"form": form}
    return render(request, "transcription/register.html", context)


def loginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.info(request, "Username or password is incorrect")
    return render(request, "transcription/login.html")


def logoutUser(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home(request):
    if hasattr(request.user, 'class_enrollments') and request.user.class_enrollments.exists():
        class_code = request.user.class_enrollments.last().class_code
        assignments = class_code.assignments.all()
        flashcard_sets = class_code.flashcard_sets.all()
        return render(request, 'transcription/index.html', {'assignments': assignments, 'flashcard_sets': flashcard_sets})

    if request.method == "POST":
        code = request.POST.get("class_code").upper()
        try:
            class_code = ClassCode.objects.get(code=code)
            if not UserClassEnrollment.objects.filter(user=request.user, class_code=class_code).exists():
                UserClassEnrollment.objects.create(user=request.user, class_code=class_code)
            assignments = class_code.assignments.all()
            flashcard_sets = class_code.flashcard_sets.all()
            return render(request, 'transcription/index.html', {'assignments': assignments, 'flashcard_sets': flashcard_sets})
        except ClassCode.DoesNotExist:
            return render(request, 'transcription/home.html', {'error': 'Invalid class code'})
    
    return render(request, 'transcription/home.html')


@login_required(login_url="login")
def index(request, assignment_id=None):
    if assignment_id:
        assignment = get_object_or_404(Assignment, id=assignment_id)
        assignments = [assignment]
    else:
        assignments = Assignment.objects.all()
    return render(request, 'transcription/index.html', {'assignments': assignments})


@login_required(login_url="login")
def record_audio(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = assignment.questions.all()

    user_progress, created = UserQuestionProgress.objects.get_or_create(
        user=request.user, assignment=assignment
    )

    completed_question_ids = user_progress.completed_questions.values_list('id', flat=True)

    questions_data = []
    for question in questions:
        questions_data.append({
            'id': question.id,
            'question_text': question.question_text,
            'has_done': question.id in completed_question_ids
        })

    context = {
        'assignment': assignment,
        'questions': questions_data,
    }
    return render(request, "transcription/questions.html", context)

from django.http import JsonResponse


from django.http import JsonResponse

def save_audio(request):
    if request.method == "POST":
        audio_data = request.POST.get('audio_data')
        assignment_id = request.POST.get('assignment_id')
        question_id = request.POST.get('question_id')

        if not all([audio_data, assignment_id, question_id]):
            return JsonResponse({"error": "Missing audio data, assignment ID, or question ID"}, status=400)

        try:
            audio_bytes = base64.b64decode(audio_data)
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                temp_audio_file.write(audio_bytes)
                temp_audio_file.flush()

                client = OpenAI(api_key="sk-J2RNSZ1E4guMaqT5AMG7MVpL4WQUfdcf7TRTtSQY7nT3BlbkFJ6JnQAvpAboZjLyl9hiwTR2Fkf7D2IhFCM6cZyrnloA")
                with open(temp_audio_file.name, "rb") as wav_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=wav_file,
                        response_format="text",
                        language="fr",
                    )

            transcribed_text = transcription.strip()
            assignment = get_object_or_404(Assignment, id=assignment_id)
            selected_question = get_object_or_404(Question, id=question_id, assignment=assignment)
            reference_answer = selected_question.answer

            missing_words, score = compare_texts(transcribed_text, reference_answer)

            return JsonResponse({
                "transcribed_text": transcribed_text,
                "answer": reference_answer,
                "score": score,
                "question": selected_question.question_text,
                "missing_words": missing_words,
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def compare_texts(transcribed_text, answer):
    def normalize_text(text):
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text

    transcribed_text = normalize_text(transcribed_text)
    answer = normalize_text(answer)
    
    transcribed_words = set(transcribed_text.split())
    answer_words = set(answer.split())
    
    missing_words = answer_words - transcribed_words
    correct_words = answer_words & transcribed_words
    score = len(correct_words) / len(answer_words) * 100
    return ", ".join(missing_words), round(score, 2)


@login_required(login_url="login")
def recording(request, assignment_id, question_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    question = get_object_or_404(Question, id=question_id)
    return render(request, "transcription/recording.html", {"assignment": assignment, "question": question})


@login_required(login_url="login")
def flashcards(request, set_id):
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id)
    flashcards = flashcard_set.flashcards.all()
    current_flashcard = flashcards.first() if flashcards else None

    user_progress, created = UserFlashcardProgress.objects.get_or_create(
        user=request.user,
        flashcard_set=flashcard_set,
        defaults={
            'completed_flashcards': 0,
            'completed_percentage': 0,
            'has_completed': False
        }
    )

    if request.method == "POST":
        flashcard_id = request.POST.get("flashcard_id")
        if flashcard_id:
            flashcard = get_object_or_404(Flashcard, id=flashcard_id)

            user_progress.completed_flashcards += 1
            user_progress.save()

            next_flashcard = flashcards.filter(id__gt=flashcard_id).first()
            if next_flashcard:
                current_flashcard = next_flashcard
            else:
                current_flashcard = None

    total_flashcards = flashcards.count()
    completion_percentage = (user_progress.completed_flashcards / total_flashcards) * 100 if total_flashcards > 0 else 0

    return render(request, 'transcription/flashcards.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
        'flashcard': current_flashcard,
        'completion_percentage': round(completion_percentage, 2),
    })


def remove_punctuation_and_accents(text):
    translation_table = str.maketrans('', '', '…?')
    normalized_text = text.translate(translation_table)
    normalized_text = re.sub(r'[^\w\s]', '', normalized_text)
    normalized_text = normalized_text.strip().lower()
    return normalized_text


def check_pronunciation(request):
    if request.method == "POST":
        audio_data = request.POST.get("audio_data", "")
        flashcard_id = request.POST.get("flashcard_id", "")

        if not flashcard_id.isdigit():
            return JsonResponse({"error": "Invalid ID format"})
        
        flashcard_id = int(flashcard_id)

        try:
            if audio_data:
                audio_bytes = base64.b64decode(audio_data)

                with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                    temp_audio_file.write(audio_bytes)
                    temp_audio_file.flush()

                    client = OpenAI(api_key="sk-J2RNSZ1E4guMaqT5AMG7MVpL4WQUfdcf7TRTtSQY7nT3BlbkFJ6JnQAvpAboZjLyl9hiwTR2Fkf7D2IhFCM6cZyrnloA")

                    with open(temp_audio_file.name, "rb") as media_file:
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            language="fr",
                            file=media_file,
                            response_format="text"
                        )

                transcribed_text = response.strip()
                
                flashcard = Flashcard.objects.get(id=flashcard_id)
                correct_text = flashcard.french_word.strip()

                correct_text = remove_punctuation_and_accents(correct_text)
                transcribed_text = remove_punctuation_and_accents(transcribed_text)

                is_correct = correct_text == transcribed_text

                return JsonResponse({"correct": is_correct, "transcribed_text": transcribed_text})
            else:
                return JsonResponse({"error": "Invalid audio data format"})
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Invalid request method"})
@login_required(login_url="login")
def update_progress(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data.get('user_id')
        flashcard_set_id = data.get('flashcard_set_id')
        percentage = data.get('percentage')

        try:
            user = User.objects.get(id=user_id)
            flashcard_set = FlashcardSet.objects.get(id=flashcard_set_id)

            progress, created = UserFlashcardProgress.objects.get_or_create(
                user=user,
                flashcard_set=flashcard_set,
                defaults={
                    'completed_percentage': 0,
                    'has_completed': False
                }
            )

            if percentage > progress.completed_percentage:
                progress.completed_percentage = percentage
            
            if percentage >= 100 or progress.has_completed:
                progress.has_completed = True

            progress.save()

            return JsonResponse({"status": "success"})

        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found"})
        except FlashcardSet.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Flashcard set not found"})

    return JsonResponse({"status": "error", "message": "Invalid request"})
def save_flashcard_index(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user
        flashcard_set_id = data.get('flashcard_set_id')
        index = data.get('index')

        progress, created = UserFlashcardProgress.objects.get_or_create(
            user=user,
            flashcard_set_id=flashcard_set_id,
            defaults={'current_flashcard_index': index}
        )
        if not created:
            progress.current_flashcard_index = index
            progress.save()

        return JsonResponse({'status': 'success'})

def get_flashcard_index(request):
    if request.method == 'GET':
        user = request.user
        flashcard_set_id = request.GET.get('flashcard_set_id')

        try:
            progress = UserFlashcardProgress.objects.get(
                user=user,
                flashcard_set_id=flashcard_set_id
            )
            return JsonResponse({'index': progress.current_flashcard_index})
        except UserFlashcardProgress.DoesNotExist:
            return JsonResponse({'index': 0})
        
def update_question_status(request):
    if request.method == "POST":
        question_id = request.POST.get("question_id")
        has_done = request.POST.get("question_has_done") == "true"

        question = get_object_or_404(Question, id=question_id)
        user_progress, created = UserQuestionProgress.objects.get_or_create(
            user=request.user, assignment=question.assignment
        )

        if has_done:
            user_progress.completed_questions.add(question)
        else:
            user_progress.completed_questions.remove(question)

        user_progress.update_progress()

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error", "message": "Invalid request"})

def assignment_progress_view(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    students = UserClassEnrollment.objects.filter(class_code=assignment.class_code).select_related('user')

    data = []
    headers = ['Username', 'Completion Percentage']

    for student in students:
        progress, _ = UserQuestionProgress.objects.get_or_create(
            user=student.user,
            assignment=assignment
        )
        data.append({
            'Username': student.user.username,
            'Completion Percentage': f"{round(progress.completion_percentage)}%"
        })

    context = {
        'assignment': assignment,
        'data': data,
        'headers': headers,
    }
    return render(request, 'transcription/assignment_progress.html', context)

def update_question_progress(request):
    data = json.loads(request.body)
    assignment_id = data.get('assignment_id')
    completed_questions = data.get('completed_questions')
    total_questions = data.get('total_questions')

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        progress, created = UserQuestionProgress.objects.get_or_create(
            user=request.user,
            assignment=assignment
        )
        
        progress.completed_percentage = (completed_questions / total_questions) * 100
        if progress.completed_percentage == 100:
            progress.has_completed = True
        progress.save()

        return JsonResponse({'status': 'success', 'message': 'Progress updated'})
    except Assignment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Assignment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)