from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import InterpersonalSession, InterpersonalQuestion

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

class InterpersonalSessionForm(forms.ModelForm):
    class Meta:
        model = InterpersonalSession
        fields = ['title', 'language', 'class_code']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter session title'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'class_code': forms.Select(attrs={'class': 'form-control'}),
        }

class InterpersonalQuestionForm(forms.ModelForm):
    class Meta:
        model = InterpersonalQuestion
        fields = ['teacher_transcription', 'order']
        widgets = {
            'teacher_transcription': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the question text',
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
        }