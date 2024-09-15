from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tempfile import NamedTemporaryFile
import base64
from django.views.decorators.http import require_GET
import unicodedata
import json
import string
import re
from difflib import SequenceMatcher
import pusher


from openai import OpenAI
from .models import Assignment, ClassCode, FlashcardSet, Flashcard, UserClassEnrollment, UserFlashcardProgress, Question, UserQuestionProgress, UserQuestionAttempts, Game1, GameParticipant
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
            if user.is_staff or user.is_superuser:  # Check if user is admin
                return redirect("admin:index")  # Redirect to admin page
            return redirect("home")
        else:
            messages.info(request, "Username or password is incorrect")
    return render(request, "transcription/login.html")


def logoutUser(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home(request):
    # Check if user is admin and redirect if so
    if request.user.is_staff or request.user.is_superuser:
        return redirect("admin:index")

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

    questions_data = []
    for question in questions:
        question_attempts, _ = UserQuestionAttempts.objects.get_or_create(
            user=request.user, question=question, defaults={'attempts_left': 2}
        )
        questions_data.append({
            'id': question.id,
            'question_text': question.question_text,
            'attempts_left': question_attempts.attempts_left
        })

    context = {
        'assignment': assignment,
        'questions': questions_data,
    }
    return render(request, "transcription/questions.html", context)

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

                client = OpenAI(api_key="sk-qtvZYUkCq-UovQC1v3ZvTzMeRSHgs_8TLZOM9HO88-T3BlbkFJ2FFPiJVX_qfjtsaUKBH-GJQtz9uQsdjdGoz8jmq1cA")

                # Retrieve the assignment and question
                assignment = get_object_or_404(Assignment, id=assignment_id)
                selected_question = get_object_or_404(Question, id=question_id, assignment=assignment)

                # Use the assignment's language for transcription
                transcription_language = assignment.language

                with open(temp_audio_file.name, "rb") as wav_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=wav_file,
                        response_format="text",
                        language=transcription_language,
                    )

            transcribed_text = transcription.strip()

            # Perform AI evaluation
            evaluation = get_ai_evaluation(client, selected_question.question_text, transcribed_text, assignment.language)

            # Parse the evaluation response
            evaluation_lines = evaluation.split('\n')
            score = evaluation_lines[0].split(':')[1].strip()
            feedback = evaluation_lines[1].split(':')[1].strip()

            return JsonResponse({
                "transcribed_text": transcribed_text,
                "score": score,
                "feedback": feedback,
                "question": selected_question.question_text,
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_ai_evaluation(client, question, student_answer, language):
    language_name = "French" if language == "fr" else "Spanish"
    
    prompt = f"""As a {language_name} teacher, evaluate:
    Question: {question}
    Answer: {student_answer}
            First, check if an answer was provided:
    If no answer or only whitespace: Score 0
    Otherwise, evaluate as follows:
    Prioritize answering the specific question, but be lenient on grammar for beginners. 

    Scoring guide:
    1-50: Off-topic or barely addresses question, major errors
    51-75: Addresses question with some errors
    76-100: Correctly addresses question, minor errors allowed

    Provide what the user did wrong in English. Do not correct something that is right even though it could be written better.

    Format:
    Score: 
    Feedback: """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are a {language_name} evaluation assistant for beginners."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content


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
    # Remove content within parentheses
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Normalize Unicode characters
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove remaining punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text).lower().strip()
    
    return text
def evaluate_answer(user_answer, expected_answer):
    # Normalize answers: remove punctuation, convert to lowercase
    user_answer = re.sub(r'[^\w\s]', '', user_answer.lower())
    expected_answer = re.sub(r'[^\w\s]', '', expected_answer.lower())

    # Extract the verb and object from both answers
    user_parts = user_answer.split()
    expected_parts = expected_answer.split()

    # Check verb
    user_verb = user_parts[0] if user_parts else ""
    expected_verb = expected_parts[0] if expected_parts else ""
    verb_score = SequenceMatcher(None, user_verb, expected_verb).ratio()

    # Check object (allowing for alternatives)
    user_object = ' '.join(user_parts[1:]) if len(user_parts) > 1 else ""
    expected_object = ' '.join(expected_parts[1:]) if len(expected_parts) > 1 else ""
    
    # Replace placeholders with regex pattern
    expected_object_pattern = re.sub(r'\[.*?\]', r'.*?', expected_object)
    object_match = re.search(expected_object_pattern, user_object)
    
    object_score = 1 if object_match else SequenceMatcher(None, user_object, expected_object).ratio()

    # Calculate final score
    final_score = (verb_score * 0.4 + object_score * 0.6) * 100

    return round(final_score, 2)

def compare_texts(transcribed_text, reference_answer):
    score = evaluate_answer(transcribed_text, reference_answer)
    
    # Identify missing key elements
    missing_words = []
    for word in reference_answer.split():
        if word.startswith('[') and word.endswith(']'):
            if word[1:-1].lower() not in transcribed_text.lower():
                missing_words.append(word[1:-1])
    
    return ", ".join(missing_words), score
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

                    client = OpenAI(api_key="sk-qtvZYUkCq-UovQC1v3ZvTzMeRSHgs_8TLZOM9HO88-T3BlbkFJ2FFPiJVX_qfjtsaUKBH-GJQtz9uQsdjdGoz8jmq1cA")

                    flashcard = get_object_or_404(Flashcard, id=flashcard_id)
                    language = flashcard.flashcard_set.language

                    with open(temp_audio_file.name, "rb") as media_file:
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            language=language,
                            file=media_file,
                            response_format="text"
                        )

                transcribed_text = response.strip()
                correct_text = flashcard.french_word.strip()

                missing_words, score = compare_texts(transcribed_text, correct_text)

                return JsonResponse({
                    "correct": score >= 80,  # Consider it correct if the score is 80% or higher
                    "transcribed_text": transcribed_text,
                    "score": score,
                    "missing_words": missing_words
                })
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
        attempts_left = int(request.POST.get("attempts_left"))

        question = get_object_or_404(Question, id=question_id)
        user_progress, created = UserQuestionProgress.objects.get_or_create(
            user=request.user, assignment=question.assignment
        )

        question_attempt, _ = UserQuestionAttempts.objects.get_or_create(
            user=request.user, question=question
        )
        question_attempt.attempts_left = attempts_left
        question_attempt.save()

        if attempts_left == 0 or attempts_left == 1:
            user_progress.completed_questions.add(question)

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
        
        progress.completed_percentage = ((completed_questions + 1) / total_questions) * 100
        if progress.completed_percentage == 100:
            progress.has_completed = True
        progress.save()

        return JsonResponse({'status': 'success', 'message': 'Progress updated'})
    except Assignment.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Assignment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@require_GET
def check_class_code(request, code):
    exists = ClassCode.objects.filter(code=code).exists()
    return JsonResponse({'exists': exists})

from django.conf import settings

pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)
@login_required
def join_game(request):
    if request.method == 'POST':
        game_code = request.POST.get('game_code')
        game = get_object_or_404(Game1, code=game_code)
        
        participant, created = GameParticipant.objects.get_or_create(user=request.user, game=game)
        
        if created:
            messages.success(request, f"You've successfully joined the game {game_code}!")
            
            # Trigger Pusher event
            pusher_client.trigger(f'game-{game.id}', 'new-participant', {
                'username': request.user.username,
                'joined_at': participant.joined_at.isoformat()
            })
        else:
            messages.info(request, f"You're already in the game {game_code}.")
        
        return redirect('student_view_game', game_id=game.id)
    
    return redirect('index')  # Redirect to home page if not a POST request

@login_required
def student_view_game(request, game_id):
    game = get_object_or_404(Game1, id=game_id)
    participant = get_object_or_404(GameParticipant, user=request.user, game=game)
    
    context = {
        'game': game,
        'participant': participant,
    }
    return render(request, 'transcription/student_view_game.html', context)