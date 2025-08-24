from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from tempfile import NamedTemporaryFile
import base64
import os
import json
from openai import OpenAI

def get_ai_evaluation_trial(client, question, student_answer, language):
    """Simple AI evaluation for trial"""
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
    """Simple trial page with teacher and student sections - session-based storage"""
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'create_question':
            question_text = request.POST.get('question_text')
            expected_answer = request.POST.get('expected_answer')
            
            if question_text and expected_answer:
                # Store questions in session instead of database
                if 'trial_questions' not in request.session:
                    request.session['trial_questions'] = []
                
                new_question = {
                    'id': len(request.session['trial_questions']) + 1,
                    'question_text': question_text,
                    'expected_answer': expected_answer
                }
                
                request.session['trial_questions'].append(new_question)
                request.session.modified = True
                
                return JsonResponse({'status': 'success', 'message': 'Question created successfully!'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Please fill in both question and expected answer.'})
        
        elif action == 'submit_audio':
            audio_data = request.POST.get('audio_data')
            question_id = request.POST.get('question_id')
            
            if audio_data and question_id:
                try:
                    audio_bytes = base64.b64decode(audio_data)
                    
                    with NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                        temp_audio_file.write(audio_bytes)
                        temp_audio_file.flush()
                        
                        api_key = os.environ.get('OPENAI_API_KEY', '').strip()
                        client = OpenAI(api_key=api_key)
                        
                        # Get question from session
                        trial_questions = request.session.get('trial_questions', [])
                        question_id = int(question_id)
                        
                        if question_id <= len(trial_questions):
                            question = trial_questions[question_id - 1]
                            
                            # Transcribe audio
                            with open(temp_audio_file.name, "rb") as wav_file:
                                transcription = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=wav_file,
                                    response_format="text",
                                    language="fr",  # Default to French for trial
                                )
                            
                            transcribed_text = transcription.strip()
                            
                            # Get AI evaluation
                            evaluation = get_ai_evaluation_trial(client, question['question_text'], transcribed_text, "fr")
                            
                            # Parse evaluation
                            evaluation_lines = evaluation.split('\n')
                            score = evaluation_lines[0].split(':')[1].strip()
                            feedback = evaluation_lines[1].split(':')[1].strip()
                            
                            return JsonResponse({
                                "transcribed_text": transcribed_text,
                                "score": score,
                                "feedback": feedback,
                                "question": question['question_text'],
                            })
                        else:
                            return JsonResponse({"error": "Question not found."}, status=400)
                            
                except Exception as e:
                    return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
            else:
                return JsonResponse({"error": "No audio data or question ID provided."}, status=400)
        
        elif action == 'clear_questions':
            # Clear all trial questions from session
            if 'trial_questions' in request.session:
                del request.session['trial_questions']
                request.session.modified = True
            
            return JsonResponse({'status': 'success', 'message': 'All questions cleared successfully!'})
    
    # GET request - show the trial page
    trial_questions = request.session.get('trial_questions', [])
    
    return render(request, 'transcription/trial.html', {
        'questions': trial_questions
    }) 