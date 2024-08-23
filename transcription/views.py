from django.shortcuts import render, redirect, get_object_or_404
import base64
import string
from django.http import HttpResponse, JsonResponse
from .models import Assignment, QuestionAnswer, ClassCode, FlashcardSet, Flashcard, Transcription, UserClassEnrollment, UserFlashcardProgress
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_protect
from .forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from tempfile import NamedTemporaryFile
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import ClassCode, UserClassEnrollment, UserFlashcardProgress, Assignment
from django.http import JsonResponse


from openai import OpenAI

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

    context = {}
    return render(request, "transcription/login.html", context)

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
            return render(request, 'transcription/index.html', {'assignments': assignments, "flashcard_sets": flashcard_sets})
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
    return render(request, "transcription/record_audio.html", {"assignment": assignment, "questions": questions})

def save_audio(request):
    try:
        if request.method == "POST":
            audio_data = request.POST.get('audio_data', None)
            assignment_id = request.POST.get('assignment_id', None)
            question_id = request.POST.get('question_id', None)

            if audio_data:
                # Decode the base64 encoded audio data
                audio_bytes = base64.b64decode(audio_data)

                # Create a temporary file to hold the audio
                with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                    temp_audio_file.write(audio_bytes)
                    temp_audio_file.flush()
                    
                    # Initialize the OpenAI client
                    client = OpenAI(api_key="sk-J2RNSZ1E4guMaqT5AMG7MVpL4WQUfdcf7TRTtSQY7nT3BlbkFJ6JnQAvpAboZjLyl9hiwTR2Fkf7D2IhFCM6cZyrnloA")

                    # Transcribe the audio with Whisper API
                    with open(temp_audio_file.name, "rb") as wav_file:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=wav_file,
                            response_format="text"
                        )

                transcribed_text = transcription.strip()
                assignment = get_object_or_404(Assignment, id=assignment_id)
                selected_question = get_object_or_404(QuestionAnswer, id=question_id, assignment=assignment)
                selected_answer = selected_question.answer

                # If there's no reference answer, use an empty string
                reference_answer = selected_answer if selected_answer else ""

                # Compare the transcribed text with the reference answer
                score = compare_texts(transcribed_text, reference_answer)

                return render(request, 'transcription/result.html', {
                    "transcribed_text": transcribed_text,
                    'answer': reference_answer,
                    'score': score,
                    'assignment': assignment,
                    'question': selected_question,
                })
            else:
                return HttpResponse("Error: Invalid audio data format")
        else:
            return HttpResponse("Invalid request method")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

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
    question = get_object_or_404(QuestionAnswer, id=question_id)
    return render(request, "transcription/recording.html", {"assignment": assignment, "question": question})

@login_required(login_url="login")
def flashcards(request, set_id):
    flashcard_set = get_object_or_404(FlashcardSet, id=set_id)
    flashcards = flashcard_set.flashcards.all()
    current_flashcard = flashcards.first() if flashcards else None

    # Get or create the user's progress on this flashcard set
    user_progress, created = UserFlashcardProgress.objects.get_or_create(
        user=request.user,
        flashcard_set=flashcard_set
    )

    if request.method == "POST":
        flashcard_id = request.POST.get("flashcard_id")
        if flashcard_id:
            flashcard = get_object_or_404(Flashcard, id=flashcard_id)

            # Increment the completed flashcards count
            user_progress.completed_flashcards += 1
            user_progress.save()

            # Get the next flashcard or show completion message
            next_flashcard = flashcards.filter(id__gt=flashcard_id).first()
            if next_flashcard:
                current_flashcard = next_flashcard
            else:
                current_flashcard = None  # This means all flashcards are completed

    # Calculate the completion percentage
    total_flashcards = flashcards.count()
    completion_percentage = (user_progress.completed_flashcards / total_flashcards) * 100 if total_flashcards > 0 else 0

    return render(request, 'transcription/flashcards.html', {
        'flashcard_set': flashcard_set,
        'flashcards': flashcards,
        'flashcard': current_flashcard,
        'completion_percentage': round(completion_percentage, 2),
    })
def check_pronunciation(request):
    if request.method == "POST":
        audio_data = request.POST.get("audio_data", "")
        flashcard_id = request.POST.get("flashcard_id", "")

        if not flashcard_id.isdigit():
            return JsonResponse({"error": "Invalid ID format"})
        
        flashcard_id = int(flashcard_id)

        try:
            if audio_data:
                # Decode audio data and save it as a temporary WAV file
                audio_bytes = base64.b64decode(audio_data)

                with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                    temp_audio_file.write(audio_bytes)
                    temp_audio_file.flush()

                    # Initialize the OpenAI client
                    client = OpenAI(api_key="sk-J2RNSZ1E4guMaqT5AMG7MVpL4WQUfdcf7TRTtSQY7nT3BlbkFJ6JnQAvpAboZjLyl9hiwTR2Fkf7D2IhFCM6cZyrnloA")  # Replace with your actual API key

                    # Transcribe the audio with Whisper API
                    with open(temp_audio_file.name, "rb") as media_file:
                        response = client.audio.transcriptions.create(
                            model="whisper-1",
                            language="fr",
                            file=media_file,
                            response_format="text"  # This returns the transcription as a string
                        )

                # The response is now a string, not an object
                transcribed_text = response.strip()
                
                flashcard = Flashcard.objects.get(id=flashcard_id)
                correct_text = flashcard.french_word.strip().lower()

                is_correct = correct_text in transcribed_text.lower()

                return JsonResponse({"correct": is_correct, "transcribed_text": transcribed_text})
            else:
                return JsonResponse({"error": "Invalid audio data format"})
        except Exception as e:
            return JsonResponse({"error": str(e)})
    return JsonResponse({"error": "No audio data received"})


def save_flashcard_progress(request):
    if request.method == "POST":
        flashcard_set_id = request.POST.get("flashcard_set_id", "")
        flashcard_id = request.POST.get("flashcard_id", "")
        completed = request.POST.get("completed", "")

        if not (flashcard_set_id.isdigit() and flashcard_id.isdigit()):
            return JsonResponse({"error": "Invalid ID format"})
        
        flashcard_set_id = int(flashcard_set_id)
        flashcard_id = int(flashcard_id)

        try:
            flashcard_set = get_object_or_404(FlashcardSet, id=flashcard_set_id)
            flashcard = get_object_or_404(Flashcard, id=flashcard_id, flashcard_set=flashcard_set)

            # Update user progress
            user_progress, created = UserFlashcardProgress.objects.get_or_create(
                user=request.user,
                flashcard_set=flashcard_set
            )
            
            if completed == "true":
                user_progress.completed_flashcards.add(flashcard)
            else:
                user_progress.completed_flashcards.remove(flashcard)

            user_progress.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"error": str(e)})

    return JsonResponse({"error": "Invalid request method"})
# views.py

def update_progress(request):
    if request.method == "POST":
        try:
            # Extract data from the request
            data = json.loads(request.body)
            user_id = data.get('user_id')
            flashcard_set_id = data.get('flashcard_set_id')
            percentage = data.get('percentage')

            # Get or create the user's flashcard progress record
            user_progress, created = UserFlashcardProgress.objects.get_or_create(
                user_id=user_id,
                flashcard_set_id=flashcard_set_id
            )

            # Calculate the number of completed flashcards based on percentage
            flashcard_set = FlashcardSet.objects.get(id=flashcard_set_id)
            total_flashcards = flashcard_set.flashcards.count()
            completed_flashcards = int((percentage / 100) * total_flashcards)

            # Update the progress
            user_progress.completed_flashcards = completed_flashcards
            user_progress.save()

            return JsonResponse({'status': 'success', 'message': 'Progress updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required(login_url="login")
def update_progress(request):
    if request.method == "POST":
        try:
            import json
            data = json.loads(request.body)
            user_id = data.get('user_id')
            flashcard_set_id = data.get('flashcard_set_id')
            percentage = data.get('percentage')

            if not (user_id and flashcard_set_id is not None):
                return JsonResponse({'error': 'Missing data'}, status=400)

            # Get or create the user's progress on this flashcard set
            user_progress, created = UserFlashcardProgress.objects.get_or_create(
                user_id=user_id,
                flashcard_set_id=flashcard_set_id
            )

            # Calculate the completed flashcards based on the percentage received
            total_flashcards = Flashcard.objects.filter(flashcard_set_id=flashcard_set_id).count()
            completed_flashcards = int((percentage / 100) * total_flashcards)

            # Update the completed flashcards count
            user_progress.completed_flashcards = completed_flashcards
            user_progress.save()

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)