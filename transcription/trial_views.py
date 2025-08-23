from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from tempfile import NamedTemporaryFile
import base64
import os
from openai import OpenAI
from .models import Assignment, ClassCode, Question

def get_ai_evaluation_trial(client, question, student_answer, language):
    """Trial version of AI evaluation without cloud storage dependencies"""
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

@csrf_exempt
@require_http_methods(["GET", "POST"])
def trial_page(request):
    """Trial page with teacher dashboard on left and student dashboard on right"""
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'create_question':
            question_text = request.POST.get('question_text')
            expected_answer = request.POST.get('expected_answer')
            
            if question_text and expected_answer:
                trial_class, created = ClassCode.objects.get_or_create(
                    code='TEST1',
                    defaults={'name': 'Trial Class', 'language': 'fr'}
                )
                
                trial_assignment, created = Assignment.objects.get_or_create(
                    title='Trial Assignment',
                    class_code=trial_class,
                    defaults={'language': 'fr'}
                )
                
                Question.objects.create(
                    assignment=trial_assignment,
                    question_text=question_text,
                    expected_answer=expected_answer
                )
                
                return JsonResponse({'status': 'success', 'message': 'Question created successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Please fill in both question and expected answer.'})
        
        elif action == 'submit_audio':
            audio_data = request.POST.get('audio_data')
            
            if audio_data:
                try:
                    audio_bytes = base64.b64decode(audio_data)
                    
                    with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                        temp_audio_file.write(audio_bytes)
                        temp_audio_file.flush()
                        
                        api_key = os.environ.get('OPENAI_API_KEY', '').strip()
                        client = OpenAI(api_key=api_key)
                        
                        trial_class = ClassCode.objects.get(code='TEST1')
                        trial_assignment = Assignment.objects.get(title='Trial Assignment', class_code=trial_class)
                        question = trial_assignment.questions.first()
                        
                        if question:
                            with open(temp_audio_file.name, "rb") as wav_file:
                                transcription = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=wav_file,
                                    response_format="text",
                                    language=trial_assignment.language,
                                )
                            
                            transcribed_text = transcription.strip()
                            
                            evaluation = get_ai_evaluation_trial(client, question.question_text, transcribed_text, trial_assignment.language)
                            
                            evaluation_lines = evaluation.split('\n')
                            score = evaluation_lines[0].split(':')[1].strip()
                            feedback = evaluation_lines[1].split(':')[1].strip()
                            
                            return JsonResponse({
                                "transcribed_text": transcribed_text,
                                "score": score,
                                "feedback": feedback,
                                "question": question.question_text,
                            })
                        else:
                            return JsonResponse({"error": "No questions available for trial."}, status=400)
                            
                except Exception as e:
                    return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
            else:
                return JsonResponse({"error": "No audio data provided."}, status=400)
    
    try:
        trial_class = ClassCode.objects.get(code='TEST1')
        trial_assignment = Assignment.objects.get(title='Trial Assignment', class_code=trial_class)
        questions = trial_assignment.questions.all()
    except (ClassCode.DoesNotExist, Assignment.DoesNotExist):
        trial_class = None
        trial_assignment = None
        questions = []
    
    return render(request, 'transcription/trial.html', {
        'trial_class': trial_class,
        'trial_assignment': trial_assignment,
        'questions': questions
    }) 