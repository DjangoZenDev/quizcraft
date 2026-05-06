"""
URL Configuration for quiz app
"""

from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # Public pages
    path('', views.index, name='index'),
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quiz/<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<uuid:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('attempt/<uuid:attempt_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('attempt/<uuid:attempt_id>/results/', views.quiz_results, name='quiz_results'),

    # User pages (require login)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-attempts/', views.my_attempts, name='my_attempts'),
]
