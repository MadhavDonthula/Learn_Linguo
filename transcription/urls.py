from django.urls import path
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.registerPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),
    path('flashcards/<int:set_id>/', views.flashcards, name='flashcards'),
    path('check_pronunciation/', views.check_pronunciation, name='check_pronunciation'),
    path('teacher_login/', admin.site.urls, name='teacher_login'),
    path('assignments/<int:assignment_id>/', views.index, name='index'),
    path('questions/<int:assignment_id>/', views.record_audio, name='questions'),
    path('save_audio/', views.save_audio, name='save_audio'),
    path('update-progress/', views.update_progress, name='update_progress'),
    # path("get_index", views.get_index, name="get_index")
    path('save_flashcard_index/', views.save_flashcard_index, name='save_flashcard_index'),
    path('get_flashcard_index/', views.get_flashcard_index, name='get_flashcard_index'),
    path("update_question_status", views.update_question_status, name="update_question_status"),
        path("update_question_progress", views.update_question_progress, name="update_question_progress"),
    path("assignment_progress_view", views.assignment_progress_view, name="assignment_progress_view"),
        path('check-class-code/<str:code>/', views.check_class_code, name='check_class_code'),
            path('join_game/', views.join_game, name='join_game'),
    path('game/<int:game_id>/', views.student_view_game, name='student_view_game'),



]

