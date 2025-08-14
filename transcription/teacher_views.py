from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import base64
import os
from tempfile import NamedTemporaryFile
from .models import InterpersonalSession, InterpersonalQuestion, ClassCode
from .forms import InterpersonalSessionForm, InterpersonalQuestionForm
import boto3
from botocore.exceptions import NoCredentialsError
import uuid

def is_teacher(user):
    """Check if user is a teacher (staff or superuser)"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    """Teacher dashboard showing all interpersonal sessions"""
    sessions = InterpersonalSession.objects.all().order_by('-created_at')
    class_codes = ClassCode.objects.all()
    
    return render(request, 'transcription/teacher/dashboard.html', {
        'sessions': sessions,
        'class_codes': class_codes
    })

@login_required
@user_passes_test(is_teacher)
def create_interpersonal_session(request):
    """Create a new interpersonal session"""
    if request.method == 'POST':
        form = InterpersonalSessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(request, f'Interpersonal session "{session.title}" created successfully!')
            return redirect('edit_interpersonal_session', session_id=session.id)
    else:
        form = InterpersonalSessionForm()
    
    return render(request, 'transcription/teacher/create_session.html', {
        'form': form
    })

@login_required
@user_passes_test(is_teacher)
def edit_interpersonal_session(request, session_id):
    """Edit an interpersonal session and its questions"""
    session = get_object_or_404(InterpersonalSession, id=session_id)
    questions = session.questions.all().order_by('order')
    
    if request.method == 'POST':
        form = InterpersonalSessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated successfully!')
            return redirect('edit_interpersonal_session', session_id=session.id)
    else:
        form = InterpersonalSessionForm(instance=session)
    
    return render(request, 'transcription/teacher/edit_session.html', {
        'session': session,
        'questions': questions,
        'form': form
    })

@csrf_exempt
@require_POST
@login_required
@user_passes_test(is_teacher)
def save_teacher_audio(request):
    """Save teacher's audio recording for a question"""
    try:
        audio_data = request.POST.get('audio_data')
        session_id = request.POST.get('session_id')
        question_text = request.POST.get('question_text')
        order = request.POST.get('order')
        
        if not all([audio_data, session_id, question_text, order]):
            return JsonResponse({"error": "Missing required data"}, status=400)
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Generate unique filename
        filename = f"teacher_question_{uuid.uuid4().hex}.wav"
        
        # Upload to cloud storage
        audio_url = upload_audio_to_cloud(audio_bytes, filename)
        
        if not audio_url:
            return JsonResponse({"error": "Failed to upload audio"}, status=500)
        
        # Create or update the question
        session = get_object_or_404(InterpersonalSession, id=session_id)
        question, created = InterpersonalQuestion.objects.get_or_create(
            session=session,
            order=order,
            defaults={
                'teacher_audio_file': audio_url,
                'teacher_transcription': question_text
            }
        )
        
        if not created:
            question.teacher_audio_file = audio_url
            question.teacher_transcription = question_text
            question.save()
        
        return JsonResponse({
            "success": True,
            "question_id": question.id,
            "audio_url": audio_url
        })
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(is_teacher)
def delete_question(request, question_id):
    """Delete a question from an interpersonal session"""
    question = get_object_or_404(InterpersonalQuestion, id=question_id)
    session_id = question.session.id
    
    # Delete audio file from cloud storage if it exists
    if question.teacher_audio_file:
        delete_audio_from_cloud(question.teacher_audio_file)
    
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('edit_interpersonal_session', session_id=session_id)

@login_required
@user_passes_test(is_teacher)
def delete_session(request, session_id):
    """Delete an entire interpersonal session"""
    session = get_object_or_404(InterpersonalSession, id=session_id)
    
    # Delete all audio files from cloud storage
    for question in session.questions.all():
        if question.teacher_audio_file:
            delete_audio_from_cloud(question.teacher_audio_file)
    
    session.delete()
    messages.success(request, 'Session deleted successfully!')
    return redirect('teacher_dashboard')

def upload_audio_to_cloud(audio_bytes, filename):
    """Upload audio file to cloud storage (Backblaze B2)"""
    try:
        # Initialize B2 client
        b2 = boto3.client(
            's3',
            endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME')
        )
        
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        
        # Upload file
        b2.put_object(
            Bucket=bucket_name,
            Key=f'interpersonal_questions/{filename}',
            Body=audio_bytes,
            ContentType='audio/wav'
        )
        
        # Return the public URL
        return f"{os.environ.get('AWS_S3_ENDPOINT_URL')}/{bucket_name}/interpersonal_questions/{filename}"
        
    except NoCredentialsError:
        print("AWS credentials not found")
        return None
    except Exception as e:
        print(f"Error uploading to cloud: {e}")
        return None

def delete_audio_from_cloud(audio_url):
    """Delete audio file from cloud storage"""
    try:
        # Extract filename from URL
        filename = audio_url.split('/')[-1]
        
        b2 = boto3.client(
            's3',
            endpoint_url=os.environ.get('AWS_S3_ENDPOINT_URL'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=os.environ.get('AWS_S3_REGION_NAME')
        )
        
        bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        
        b2.delete_object(
            Bucket=bucket_name,
            Key=f'interpersonal_questions/{filename}'
        )
        
    except Exception as e:
        print(f"Error deleting from cloud: {e}") 