"""
Django Admin configuration for Quiz models
Provides user-friendly interface for managing quizzes, questions, and results
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Quiz, Question, Answer, QuizAttempt, Response, QuizTemplate


class AnswerInline(admin.TabularInline):
    """Inline for managing answers within a question"""
    model = Answer
    extra = 4
    fields = ('answer_text', 'is_correct', 'order', 'times_selected')
    readonly_fields = ('times_selected',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin for Question model"""
    list_display = ('question_preview', 'quiz', 'question_type', 'points', 'order', 'difficulty_badge', 'times_answered')
    list_filter = ('question_type', 'quiz', 'created_at')
    search_fields = ('question_text', 'quiz__title')
    inlines = [AnswerInline]
    fieldsets = (
        ('Question Content', {
            'fields': ('quiz', 'question_type', 'question_text', 'explanation', 'image')
        }),
        ('Settings', {
            'fields': ('points', 'order', 'time_limit', 'correct_answer_text')
        }),
        ('Statistics', {
            'fields': ('times_answered', 'times_correct'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('times_answered', 'times_correct')

    def question_preview(self, obj):
        return obj.question_text[:80] + '...' if len(obj.question_text) > 80 else obj.question_text
    question_preview.short_description = 'Question'

    def difficulty_badge(self, obj):
        rate = obj.difficulty_rate
        if rate >= 70:
            color = 'green'
            label = 'Easy'
        elif rate >= 40:
            color = 'orange'
            label = 'Medium'
        else:
            color = 'red'
            label = 'Hard'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} ({:.0f}%)</span>',
            color, label, rate
        )
    difficulty_badge.short_description = 'Difficulty'


class QuestionInline(admin.TabularInline):
    """Inline for managing questions within a quiz"""
    model = Question
    extra = 1
    fields = ('question_text', 'question_type', 'points', 'order')
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin for Quiz model"""
    list_display = ('title', 'creator', 'total_questions_display', 'difficulty', 'status_badge', 'total_attempts', 'avg_score', 'created_at')
    list_filter = ('difficulty', 'is_published', 'is_public', 'created_at', 'creator')
    search_fields = ('title', 'description', 'creator__username')
    readonly_fields = ('total_attempts', 'total_completions', 'average_score', 'created_at', 'updated_at')
    inlines = [QuestionInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'creator', 'difficulty', 'category', 'tags')
        }),
        ('Settings', {
            'fields': ('time_limit', 'pass_score', 'max_attempts')
        }),
        ('Visibility & Behavior', {
            'fields': ('is_published', 'is_public', 'requires_authentication',
                      'shuffle_questions', 'shuffle_answers', 'show_correct_answers',
                      'allow_review', 'show_results_immediately')
        }),
        ('Statistics', {
            'fields': ('total_attempts', 'total_completions', 'average_score'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Premium', {
            'fields': ('is_featured', 'is_premium'),
            'classes': ('collapse',)
        }),
    )

    def total_questions_display(self, obj):
        return f"{obj.total_questions} questions"
    total_questions_display.short_description = 'Questions'

    def status_badge(self, obj):
        if obj.is_published:
            return format_html('<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Published</span>')
        return format_html('<span style="background-color: gray; color: white; padding: 3px 10px; border-radius: 3px;">Draft</span>')
    status_badge.short_description = 'Status'

    def avg_score(self, obj):
        return f"{obj.average_score:.1f}%"
    avg_score.short_description = 'Avg Score'


class ResponseInline(admin.TabularInline):
    """Inline for viewing responses within an attempt"""
    model = Response
    extra = 0
    fields = ('question', 'is_correct', 'points_earned', 'time_spent_seconds')
    readonly_fields = ('question', 'is_correct', 'points_earned', 'time_spent_seconds')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Admin for QuizAttempt model"""
    list_display = ('user_display', 'quiz', 'status_badge', 'score_display', 'passed_badge', 'time_taken_formatted', 'started_at')
    list_filter = ('status', 'passed', 'quiz', 'started_at')
    search_fields = ('user__username', 'user__email', 'quiz__title', 'anonymous_id')
    readonly_fields = ('quiz', 'user', 'status', 'score', 'total_possible', 'score_percentage',
                      'passed', 'started_at', 'completed_at', 'time_taken_seconds',
                      'ip_address', 'user_agent', 'results_viewed_at')
    inlines = [ResponseInline]

    fieldsets = (
        ('Attempt Information', {
            'fields': ('quiz', 'user', 'anonymous_id', 'status')
        }),
        ('Results', {
            'fields': ('score', 'total_possible', 'score_percentage', 'passed')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'time_taken_seconds')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'results_viewed_at'),
            'classes': ('collapse',)
        }),
    )

    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return f"Anonymous ({obj.anonymous_id})"
    user_display.short_description = 'User'

    def status_badge(self, obj):
        colors = {
            'IN_PROGRESS': 'blue',
            'COMPLETED': 'green',
            'ABANDONED': 'orange',
            'TIMED_OUT': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def score_display(self, obj):
        return f"{obj.score}/{obj.total_possible} ({obj.score_percentage:.1f}%)"
    score_display.short_description = 'Score'

    def passed_badge(self, obj):
        if obj.status != 'COMPLETED':
            return '-'
        if obj.passed:
            return format_html('<span style="color: green; font-weight: bold;">✓ Passed</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Failed</span>')
    passed_badge.short_description = 'Result'

    def has_add_permission(self, request):
        return False


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Admin for Response model"""
    list_display = ('attempt_user', 'question_preview', 'is_correct_badge', 'points_earned', 'auto_graded', 'answered_at')
    list_filter = ('is_correct', 'auto_graded', 'answered_at')
    search_fields = ('attempt__user__username', 'question__question_text')
    readonly_fields = ('attempt', 'question', 'is_correct', 'points_earned',
                      'auto_graded', 'answered_at', 'time_spent_seconds')

    fieldsets = (
        ('Response', {
            'fields': ('attempt', 'question')
        }),
        ('Answer', {
            'fields': ('text_answer',)  # selected_answers shown separately
        }),
        ('Grading', {
            'fields': ('is_correct', 'points_earned', 'auto_graded')
        }),
        ('Manual Grading', {
            'fields': ('graded_by', 'grading_notes', 'graded_at'),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': ('time_spent_seconds', 'answered_at'),
            'classes': ('collapse',)
        }),
    )

    def attempt_user(self, obj):
        if obj.attempt.user:
            return obj.attempt.user.username
        return "Anonymous"
    attempt_user.short_description = 'User'

    def question_preview(self, obj):
        return obj.question.question_text[:60] + '...' if len(obj.question.question_text) > 60 else obj.question.question_text
    question_preview.short_description = 'Question'

    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ Correct</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Incorrect</span>')
    is_correct_badge.short_description = 'Result'

    def has_add_permission(self, request):
        return False


@admin.register(QuizTemplate)
class QuizTemplateAdmin(admin.ModelAdmin):
    """Admin for QuizTemplate model"""
    list_display = ('name', 'category', 'quiz', 'is_public', 'times_used', 'created_by', 'created_at')
    list_filter = ('category', 'is_public', 'created_at')
    search_fields = ('name', 'description', 'quiz__title')
    readonly_fields = ('times_used', 'created_at', 'updated_at')

    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'category', 'quiz')
        }),
        ('Settings', {
            'fields': ('is_public', 'created_by')
        }),
        ('Statistics', {
            'fields': ('times_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Admin for Answer model (optional - mainly used via inline)"""
    list_display = ('answer_preview', 'question', 'is_correct_badge', 'order', 'times_selected')
    list_filter = ('is_correct', 'question__quiz')
    search_fields = ('answer_text', 'question__question_text')
    readonly_fields = ('times_selected', 'created_at', 'updated_at')

    def answer_preview(self, obj):
        return obj.answer_text[:60] + '...' if len(obj.answer_text) > 60 else obj.answer_text
    answer_preview.short_description = 'Answer'

    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="color: green; font-weight: bold;">✓ Correct</span>')
        return format_html('<span style="color: red;">✗ Incorrect</span>')
    is_correct_badge.short_description = 'Correct?'


# Customize admin site header
admin.site.site_header = "QuizCraft Administration"
admin.site.site_title = "QuizCraft Admin"
admin.site.index_title = "Welcome to QuizCraft Admin Panel"
