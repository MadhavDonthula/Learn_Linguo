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
from django.views.decorators.http import require_http_methods
from django.core.files import File

import logging


from openai import OpenAI
from .models import Assignment, ClassCode, FlashcardSet, Flashcard, UserClassEnrollment, UserFlashcardProgress, Question, UserQuestionProgress, UserQuestionAttempts, InterpersonalSession, InterpersonalQuestion
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
        interpersonal_sessions = InterpersonalSession.objects.filter(class_code=class_code)

        return render(request, 'transcription/index.html', {
            'assignments': assignments,
            'flashcard_sets': flashcard_sets,
            'interpersonal_sessions': interpersonal_sessions
        })


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
from django.core.serializers.json import DjangoJSONEncoder

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def interpersonal_session_details(request, session_id):
    session = get_object_or_404(InterpersonalSession, id=session_id)
    questions = session.questions.all().order_by('order')
    user_progress, created = UserInterpersonalProgress.objects.get_or_create(
        user=request.user,
        session=session
    )
    
    questions_data = []
    transcriptions = []  # Array to hold all transcriptions
    for question in questions:
        # Use the URL directly, no need to encode
        audio_data = question.audio_file if question.audio_file else ''
        
        # Append transcription to the separate array
        transcriptions.append(question.transcription if question.transcription else 'No transcription available')
        
        questions_data.append({
            'id': question.id,
            'order': question.order,
            'audio_data': audio_data,  # This is now a URL
        })
    
    logger.info(f"Prepared {len(questions_data)} questions for session {session_id}")
    
    context = {
        'session': session,
        'questions_data': json.dumps(questions_data, cls=DjangoJSONEncoder),
        'transcriptions': json.dumps(transcriptions, cls=DjangoJSONEncoder),
        'is_completed': user_progress.has_completed,
    }
    
    return render(request, 'transcription/interpersonal_session.html', context)

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
from django.views.decorators.http import require_POST

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
@require_POST
def save_interpersonal_audio(request):
    if request.method == "POST":
        audio_data = request.POST.get('audio_data')
        session_id = request.POST.get('session_id')
        question_id = request.POST.get('question_id')
        
        if not all([audio_data, session_id, question_id]):
            return JsonResponse({"error": "Missing audio data, session ID, or question ID"}, status=400)
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                temp_audio_file.write(audio_bytes)
                temp_audio_file.flush()
                
                client = OpenAI(api_key="sk-qtvZYUkCq-UovQC1v3ZvTzMeRSHgs_8TLZOM9HO88-T3BlbkFJ2FFPiJVX_qfjtsaUKBH-GJQtz9uQsdjdGoz8jmq1cA")
                
                # Retrieve the session and question
                session = get_object_or_404(InterpersonalSession, id=session_id)
                selected_question = get_object_or_404(InterpersonalQuestion, id=question_id, session=session)
                
                # Use the session's language for transcription
                transcription_language = session.language
                
                with open(temp_audio_file.name, "rb") as wav_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=wav_file,
                        response_format="text",
                        language=transcription_language,
                    )
            
            transcribed_text = transcription.strip()
            
            # Perform AI evaluation
            evaluation = get_ai_evaluation(client, selected_question.transcription, transcribed_text, session.language)
            
            # Parse the evaluation response
            evaluation_lines = evaluation.split('\n')
            score = evaluation_lines[0].split(':')[1].strip()
            feedback = evaluation_lines[1].split(':')[1].strip()
            
            return JsonResponse({
                "transcribed_text": transcribed_text,
                "score": score,
                "feedback": feedback,
                "question": selected_question.transcription,
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

def update_interpersonal_question_status(request):
    if request.method == "POST":
        question_id = request.POST.get('question_id')
        attempts_left = request.POST.get('attempts_left')
        
        question = get_object_or_404(InterpersonalQuestion)
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

def interpersonal_view(request):
    sessions = InterpersonalSession.objects.all()
    return render(request, 'transcription/interpersonal.html', {'sessions': sessions})

def create_interpersonal_view(request):
    class_codes = ClassCode.objects.all()
    context = {
        'class_codes': class_codes,
    }
    return render(request, 'transcription/create_interpersonal.html', context)
import json
import base64
import boto3
from botocore.exceptions import ClientError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import ClassCode, InterpersonalSession, InterpersonalQuestion
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

def add_interpersonal(request):
    if request.method == "GET":
        class_codes = ClassCode.objects.all()
        return render(request, 'transcription/create_interpersonal.html', {'class_codes': class_codes})

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get('title')
            class_code = data.get('class_code')
            language = data.get('language')
            questions = data.get('questions', [])

            if not all([title, class_code, language, questions]):
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

            class_code_obj = get_object_or_404(ClassCode, code=class_code)

            session = InterpersonalSession.objects.create(
                title=title,
                class_code=class_code_obj,
                language=language
            )

            for question_data in questions:
                audio_data = question_data.get('audio_data')
                if not audio_data:
                    return JsonResponse({'status': 'error', 'message': f"Missing audio data for question {question_data.get('order')}"}, status=400)

                # Process the base64 audio data
                if audio_data.startswith('data:audio'):
                    format, audio_str = audio_data.split(';base64,')
                    ext = format.split('/')[-1]
                    audio_bytes = base64.b64decode(audio_str)

                    # Upload to B2
                    file_name = f'interpersonal_questions/question_{session.id}_{question_data.get("order")}.{ext}'
                    try:
                        logger.info(f"Attempting to upload file: {file_name}")
                        s3_client.upload_fileobj(
                            BytesIO(audio_bytes),
                            settings.AWS_STORAGE_BUCKET_NAME,
                            file_name,
                            ExtraArgs={'ContentType': f'audio/{ext}'}
                        )
                        logger.info(f"Successfully uploaded file: {file_name}")
                    except ClientError as e:
                        logger.error(f"ClientError uploading file to B2: {str(e)}")
                        return JsonResponse({'status': 'error', 'message': f'Failed to upload audio file: {str(e)}'}, status=500)
                    except Exception as e:
                        logger.error(f"Unexpected error uploading file to B2: {str(e)}")
                        return JsonResponse({'status': 'error', 'message': f'Unexpected error uploading audio file: {str(e)}'}, status=500)

                    # Create the InterpersonalQuestion object
                    question = InterpersonalQuestion.objects.create(
                        session=session,
                        order=question_data.get('order'),
                        transcription=question_data.get('transcription', ''),
                        audio_file=f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_STORAGE_BUCKET_NAME}/{file_name}"
                    )

            return JsonResponse({'status': 'success', 'message': 'Session created successfully'})

        except Exception as e:
            logger.error(f"Error in add_interpersonal: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
@login_required
@require_http_methods(["GET", "POST"])
def edit_interpersonal(request, session_id):
    session = get_object_or_404(InterpersonalSession, id=session_id)

    if request.method == "GET":
        class_codes = ClassCode.objects.all()
        questions = session.questions.all().order_by('order')
        questions_data = []
        for question in questions:
            questions_data.append({
                'id': question.id,
                'order': question.order,
                'transcription': question.transcription,
                'audio_url': question.audio_file.url if question.audio_file else None,
            })
        context = {
            'session': session,
            'class_codes': class_codes,
            'questions': questions_data,
        }
        return render(request, 'transcription/edit_interpersonal.html', context)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            session.title = data.get('title')
            session.class_code = get_object_or_404(ClassCode, code=data.get('class_code'))
            session.language = data.get('language')
            session.save()

            existing_question_ids = set(session.questions.values_list('id', flat=True))
            updated_question_ids = set()

            for question_data in data.get('questions', []):
                question_id = question_data.get('id')
                if question_id:
                    question = session.questions.get(id=question_id)
                    updated_question_ids.add(question_id)
                else:
                    question = InterpersonalQuestion(session=session)
                
                question.order = question_data.get('order')
                question.transcription = question_data.get('transcription', '')

                audio_data = question_data.get('audio_data')
                if audio_data and audio_data.startswith('data:audio'):
                    format, audio_str = audio_data.split(';base64,')
                    ext = format.split('/')[-1]
                    audio_file = ContentFile(base64.b64decode(audio_str), name=f'question_{question.order}.{ext}')
                    question.audio_file = audio_file

                question.save()

            # Delete questions that weren't updated
            questions_to_delete = existing_question_ids - updated_question_ids
            InterpersonalQuestion.objects.filter(id__in=questions_to_delete).delete()

            return JsonResponse({'status': 'success', 'message': 'Session updated successfully'})

        except Exception as e:
            logger.error(f"Error in edit_interpersonal: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
from .models import InterpersonalSession, UserInterpersonalProgress


@login_required
@require_POST
def update_interpersonal_progress(request):
    session_id = request.POST.get('session_id')

    try:
        session = InterpersonalSession.objects.get(id=session_id)
        
        progress, created = UserInterpersonalProgress.objects.get_or_create(
            user=request.user,
            session=session
        )
        
        progress.has_completed = True
        progress.save()

        logger.debug(f"Updated progress for user {request.user.username}, session {session.title}: has_completed = {progress.has_completed}")

        return JsonResponse({'status': 'success', 'message': 'Session completed'})
    except InterpersonalSession.DoesNotExist:
        logger.error(f"InterpersonalSession with id {session_id} not found")
        return JsonResponse({'status': 'error', 'message': 'Interpersonal Session not found'}, status=404)
    except Exception as e:
        logger.error(f"Error updating interpersonal progress: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)