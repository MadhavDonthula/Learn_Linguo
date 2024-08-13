from django.shortcuts import render
import base64
import io
import whisper
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Assignment, QuestionAnswer

def index(request):
    assignments = Assignment.objects.all()
    return render(request, "transcription/index.html", {"assignments": assignments} )

def record_audio(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    questions = assignment.questions.all()
    return render(request, "transcription/record_audio.html", {"assignment": assignment, "questions": questions})


def save_audio(request):
    if request.method == "POST":
        audio_data = request.POST.get("audio_data", "")
        assignment_id = request.POST.get("assignment_id", "")

        if not assignment_id.isdigit():
            return HttpResponse("Error: Invalid assignment ID format")
        
        assignment_id = int(assignment_id)

        try:
            if audio_data:
                # Decode audio data and save it as a WAV file
                audio_bytes = base64.b64decode(audio_data)
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio_bytes)

                # Load the Whisper model
                model = whisper.load_model("medium")

                # Transcribe the audio with language set to French
                result = model.transcribe("temp_audio.wav", language="fr")
                transcribed_text = result["text"]

                # Retrieve the assignment and reference text
                assignment = get_object_or_404(Assignment, id=assignment_id)
                reference_text = " ".join([qa.answer for qa in assignment.questions.all()])

                # Compare the transcribed text with the reference text
                missing_words = compare_texts(transcribed_text, reference_text)

                return HttpResponse(f"Transcribed Text: {transcribed_text}\n Reference Text: {reference_text} \n Missing Words: {missing_words}")
            else:
                return HttpResponse("Error: Invalid audio data format")
        except Exception as e:
            return HttpResponse(f"Error: {str(e)}")
    return HttpResponse("No audio data received")


def compare_texts(transcribed_text, reference_text):
    def normalize_text(text):
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text
    transcribed_text = normalize_text(transcribed_text)
    reference_text = normalize_text(reference_text)
    transcribed_words = set(transcribed_text.split())
    reference_words = set(reference_text.split())
    missing_words = reference_words - transcribed_words
    return ", ".join(missing_words)



