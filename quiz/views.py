"""
Quiz Views for QuizCraft
Handles quiz listing, taking, submission, and results
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import random

from .models import Quiz, Question, Answer, QuizAttempt, Response
from accounts.models import User


# Home page
def index(request):
    """Home page showing featured quizzes"""
    featured_quizzes = Quiz.objects.filter(
        is_published=True,
        is_public=True,
        is_featured=True
    )[:6]

    recent_quizzes = Quiz.objects.filter(
        is_published=True,
        is_public=True
    ).order_by('-created_at')[:6]

    stats = {
        'total_quizzes': Quiz.objects.filter(is_published=True, is_public=True).count(),
        'total_attempts': QuizAttempt.objects.filter(status='COMPLETED').count(),
        'total_users': User.objects.filter(is_active=True).count(),
    }

    context = {
        'featured_quizzes': featured_quizzes,
        'recent_quizzes': recent_quizzes,
        'stats': stats,
    }
    return render(request, 'quiz/index.html', context)


# Quiz list
def quiz_list(request):
    """List all public quizzes with search and filters"""
    quizzes = Quiz.objects.filter(is_published=True, is_public=True)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        quizzes = quizzes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # Filter by difficulty
    difficulty = request.GET.get('difficulty', '')
    if difficulty:
        quizzes = quizzes.filter(difficulty=difficulty)

    # Filter by category
    category = request.GET.get('category', '')
    if category:
        quizzes = quizzes.filter(category=category)

    # Sort
    sort_by = request.GET.get('sort', '-created_at')
    quizzes = quizzes.order_by(sort_by)

    # Pagination
    paginator = Paginator(quizzes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique categories for filter
    categories = Quiz.objects.filter(
        is_published=True,
        is_public=True
    ).values_list('category', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'difficulty': difficulty,
        'category': category,
        'categories': [c for c in categories if c],
        'sort_by': sort_by,
    }
    return render(request, 'quiz/quiz_list.html', context)


# Quiz detail
def quiz_detail(request, quiz_id):
    """Show quiz details and start button"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

    # Check if quiz requires authentication
    if quiz.requires_authentication and not request.user.is_authenticated:
        messages.warning(request, 'You must be logged in to take this quiz.')
        return redirect('accounts:login')

    # Check user's previous attempts
    user_attempts = None
    can_attempt = True
    if request.user.is_authenticated:
        user_attempts = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user
        ).order_by('-started_at')

        # Check max attempts limit
        if quiz.max_attempts > 0:
            completed_attempts = user_attempts.filter(status='COMPLETED').count()
            can_attempt = completed_attempts < quiz.max_attempts

    context = {
        'quiz': quiz,
        'user_attempts': user_attempts,
        'can_attempt': can_attempt,
    }
    return render(request, 'quiz/quiz_detail.html', context)


# Take quiz
def take_quiz(request, quiz_id):
    """Quiz taking interface"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)

    # Check authentication requirement
    if quiz.requires_authentication and not request.user.is_authenticated:
        messages.warning(request, 'You must be logged in to take this quiz.')
        return redirect('accounts:login')

    # Check max attempts
    if request.user.is_authenticated and quiz.max_attempts > 0:
        attempts_count = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            status='COMPLETED'
        ).count()
        if attempts_count >= quiz.max_attempts:
            messages.error(request, f'You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz.')
            return redirect('quiz:quiz_detail', quiz_id=quiz.id)

    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        user=request.user if request.user.is_authenticated else None,
        anonymous_id=request.session.session_key if not request.user.is_authenticated else '',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

    # Update quiz statistics
    quiz.total_attempts += 1
    quiz.save(update_fields=['total_attempts'])

    # Get questions
    questions = list(quiz.questions.all())

    # Shuffle if needed
    if quiz.shuffle_questions:
        random.shuffle(questions)

    context = {
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
    }
    return render(request, 'quiz/take_quiz.html', context)


# Submit quiz
def submit_quiz(request, attempt_id):
    """Process quiz submission"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    # Verify ownership
    if request.user.is_authenticated:
        if attempt.user != request.user:
            return HttpResponseForbidden("You don't have permission to submit this quiz.")
    else:
        if attempt.anonymous_id != request.session.session_key:
            return HttpResponseForbidden("You don't have permission to submit this quiz.")

    if request.method != 'POST':
        return redirect('quiz:take_quiz', quiz_id=attempt.quiz.id)

    # Process answers
    questions = attempt.quiz.questions.all()

    for question in questions:
        # Get submitted answer
        if question.question_type in ['MULTIPLE_CHOICE', 'TRUE_FALSE']:
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                answer = Answer.objects.filter(id=answer_id, question=question).first()
                if answer:
                    response = Response.objects.create(
                        attempt=attempt,
                        question=question
                    )
                    response.selected_answers.add(answer)
                    response.grade()

        elif question.question_type == 'MULTIPLE_SELECT':
            answer_ids = request.POST.getlist(f'question_{question.id}')
            if answer_ids:
                response = Response.objects.create(
                    attempt=attempt,
                    question=question
                )
                for answer_id in answer_ids:
                    answer = Answer.objects.filter(id=answer_id, question=question).first()
                    if answer:
                        response.selected_answers.add(answer)
                response.grade()

        elif question.question_type in ['SHORT_ANSWER', 'FILL_BLANK', 'ESSAY']:
            text_answer = request.POST.get(f'question_{question.id}', '').strip()
            if text_answer:
                response = Response.objects.create(
                    attempt=attempt,
                    question=question,
                    text_answer=text_answer
                )
                response.grade()

    # Complete the attempt
    attempt.complete()

    messages.success(request, 'Quiz submitted successfully!')
    return redirect('quiz:quiz_results', attempt_id=attempt.id)


# Quiz results
def quiz_results(request, attempt_id):
    """Show quiz results"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)

    # Verify ownership
    if request.user.is_authenticated:
        if attempt.user and attempt.user != request.user:
            return HttpResponseForbidden("You don't have permission to view these results.")
    else:
        if attempt.anonymous_id != request.session.session_key:
            return HttpResponseForbidden("You don't have permission to view these results.")

    # Mark results as viewed
    if not attempt.results_viewed_at:
        attempt.results_viewed_at = timezone.now()
        attempt.save(update_fields=['results_viewed_at'])

    # Get responses with questions
    responses = attempt.responses.select_related('question').prefetch_related('selected_answers')

    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'responses': responses,
    }
    return render(request, 'quiz/quiz_results.html', context)


# User dashboard
@login_required
def dashboard(request):
    """User dashboard showing their quizzes and attempts"""
    # User's quizzes
    user_quizzes = Quiz.objects.filter(creator=request.user).order_by('-created_at')

    # User's attempts - don't slice yet, need for stats
    user_attempts_queryset = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-started_at')

    # Statistics
    total_quizzes = user_quizzes.count()
    total_attempts = user_attempts_queryset.count()
    completed_attempts_qs = user_attempts_queryset.filter(status='COMPLETED')
    avg_score = completed_attempts_qs.aggregate(Avg('score_percentage'))['score_percentage__avg'] or 0
    passed_attempts = completed_attempts_qs.filter(passed=True).count()
    failed_attempts = completed_attempts_qs.filter(passed=False).count()
    pass_rate = (passed_attempts / completed_attempts_qs.count() * 100) if completed_attempts_qs.count() > 0 else 0

    # Total responses received on user's quizzes
    total_responses = Response.objects.filter(attempt__quiz__creator=request.user).count()

    context = {
        'recent_quizzes': user_quizzes[:5],
        'recent_attempts': user_attempts_queryset[:5],
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
        'total_responses': total_responses,
        'passed_attempts': passed_attempts,
        'failed_attempts': failed_attempts,
        'pass_rate': pass_rate,
    }
    return render(request, 'quiz/dashboard.html', context)


# My attempts
@login_required
def my_attempts(request):
    """List user's quiz attempts"""
    attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-started_at')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        attempts = attempts.filter(quiz__title__icontains=search_query)

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'passed':
        attempts = attempts.filter(passed=True, status='COMPLETED')
    elif status_filter == 'failed':
        attempts = attempts.filter(passed=False, status='COMPLETED')

    # Sort
    sort_by = request.GET.get('sort', '-started_at')
    if sort_by in ['-completed_at', 'completed_at', '-score_percentage', 'score_percentage']:
        attempts = attempts.order_by(sort_by)

    # Stats
    all_attempts = QuizAttempt.objects.filter(user=request.user)
    completed_qs = all_attempts.filter(status='COMPLETED')
    total_attempts = all_attempts.count()
    passed_attempts = completed_qs.filter(passed=True).count()
    avg_score = completed_qs.aggregate(Avg('score_percentage'))['score_percentage__avg'] or 0
    pass_rate = (passed_attempts / completed_qs.count() * 100) if completed_qs.count() > 0 else 0

    # Pagination
    paginator = Paginator(attempts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'attempts': page_obj,
        'total_attempts': total_attempts,
        'passed_attempts': passed_attempts,
        'avg_score': avg_score,
        'pass_rate': pass_rate,
    }
    return render(request, 'quiz/my_attempts.html', context)
