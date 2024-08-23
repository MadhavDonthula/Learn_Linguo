from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("register/", views.registerPage, name="register"),
    path("login/", views.loginPage, name="login"),
    path("logout/", views.logoutUser, name="logout"),

    path("flashcards/<int:set_id>/", views.flashcards, name="flashcards"), 
    path("check_pronunciation/", views.check_pronunciation, name="check_pronunciation"),  

    path("teacher_login", admin.site.urls, name="teacher_login"),
    path('assignments/<int:assignment_id>/', views.index, name='index'),
    path("record/<int:assignment_id>/", views.record_audio, name="record_audio"),
    path("save_audio/", views.save_audio, name="save_audio"),
    path('recording/<int:assignment_id>/<int:question_id>/', views.recording, name="recording"),
]
