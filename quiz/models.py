"""
Quiz Models for QuizCraft
Enhanced models supporting multiple question types, analytics, and monetization
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class Quiz(models.Model):
    """
    Main Quiz model representing a complete quiz/assessment
    """

    class Difficulty(models.TextChoices):
        EASY = 'EASY', _('Easy')
        MEDIUM = 'MEDIUM', _('Medium')
        HARD = 'HARD', _('Hard')

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )

    # Quiz Settings
    time_limit = models.IntegerField(
        help_text="Time limit in seconds (0 for unlimited)",
        default=0,
        validators=[MinValueValidator(0)]
    )
    pass_score = models.IntegerField(
        help_text="Percentage required to pass (0-100)",
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    max_attempts = models.IntegerField(
        help_text="Maximum attempts allowed (0 for unlimited)",
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Quiz Properties
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM
    )
    category = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")

    # Visibility & Sharing
    is_public = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    requires_authentication = models.BooleanField(default=False)

    # Behavior Settings
    shuffle_questions = models.BooleanField(default=False)
    shuffle_answers = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    allow_review = models.BooleanField(default=True)
    show_results_immediately = models.BooleanField(default=True)

    # Statistics
    total_attempts = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Featured/Premium
    is_featured = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('quiz')
        verbose_name_plural = _('quizzes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', '-created_at']),
            models.Index(fields=['is_public', 'is_published']),
        ]

    def __str__(self):
        return self.title

    @property
    def total_questions(self):
        """Get total number of questions in this quiz"""
        return self.questions.count()

    @property
    def total_points(self):
        """Calculate total possible points"""
        return sum(q.points for q in self.questions.all())

    @property
    def completion_rate(self):
        """Calculate percentage of attempts that were completed"""
        if self.total_attempts == 0:
            return 0
        return (self.total_completions / self.total_attempts) * 100

    def update_statistics(self):
        """Update quiz statistics from attempts"""
        completed_attempts = self.attempts.filter(completed_at__isnull=False)
        self.total_completions = completed_attempts.count()

        if self.total_completions > 0:
            self.average_score = completed_attempts.aggregate(
                models.Avg('score_percentage')
            )['score_percentage__avg'] or 0

        self.save(update_fields=['total_completions', 'average_score'])


class Question(models.Model):
    """
    Question model supporting multiple question types
    """

    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', _('Multiple Choice')
        TRUE_FALSE = 'TRUE_FALSE', _('True/False')
        SHORT_ANSWER = 'SHORT_ANSWER', _('Short Answer')
        ESSAY = 'ESSAY', _('Essay')
        MULTIPLE_SELECT = 'MULTIPLE_SELECT', _('Multiple Select')
        FILL_BLANK = 'FILL_BLANK', _('Fill in the Blank')

    # Relationships
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')

    # Question Content
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE
    )
    question_text = models.TextField()
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after answering"
    )

    # Media
    image = models.ImageField(upload_to='questions/', null=True, blank=True)

    # Settings
    points = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.IntegerField(default=0)
    time_limit = models.IntegerField(
        help_text="Time limit in seconds for this question (0 for quiz default)",
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Required for certain question types
    correct_answer_text = models.TextField(
        blank=True,
        help_text="For short answer/fill in blank questions"
    )

    # Statistics
    times_answered = models.IntegerField(default=0)
    times_correct = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['quiz', 'order']
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}: {self.question_text[:50]}"

    @property
    def difficulty_rate(self):
        """Calculate difficulty based on correct answer rate"""
        if self.times_answered == 0:
            return 50.0  # Default to medium difficulty
        return (self.times_correct / self.times_answered) * 100

    @property
    def is_objective(self):
        """Check if question can be auto-graded"""
        return self.question_type in [
            self.QuestionType.MULTIPLE_CHOICE,
            self.QuestionType.TRUE_FALSE,
            self.QuestionType.MULTIPLE_SELECT,
        ]


class Answer(models.Model):
    """
    Answer choices for multiple choice and similar questions
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    explanation = models.TextField(blank=True, help_text="Why this answer is correct/incorrect")

    # Statistics
    times_selected = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('answer')
        verbose_name_plural = _('answers')
        ordering = ['question', 'order']

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.answer_text[:50]}"


class QuizAttempt(models.Model):
    """
    Track individual attempts at taking a quiz
    """

    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        ABANDONED = 'ABANDONED', _('Abandoned')
        TIMED_OUT = 'TIMED_OUT', _('Timed Out')

    # Relationships
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        null=True,
        blank=True
    )

    # Attempt Information
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )

    # Anonymous user tracking (optional)
    anonymous_id = models.CharField(max_length=100, blank=True)

    # Scores
    score = models.IntegerField(default=0)
    total_possible = models.IntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)

    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # Results viewed
    results_viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('quiz attempt')
        verbose_name_plural = _('quiz attempts')
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['quiz', '-started_at']),
            models.Index(fields=['user', '-started_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else f"Anonymous ({self.anonymous_id})"
        return f"{user_str} - {self.quiz.title} ({self.status})"

    def complete(self):
        """Mark attempt as completed and calculate scores"""
        self.completed_at = timezone.now()
        self.status = self.Status.COMPLETED

        # Calculate time taken
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.time_taken_seconds = int(delta.total_seconds())

        # Calculate scores
        self.calculate_score()

        # Check if passed
        self.passed = self.score_percentage >= self.quiz.pass_score

        self.save()

        # Update quiz statistics
        self.quiz.update_statistics()

        # Update user statistics
        if self.user:
            self.user.total_responses_received += 1
            self.user.save(update_fields=['total_responses_received'])

    def calculate_score(self):
        """Calculate total score from responses"""
        responses = self.responses.all()
        self.score = sum(r.points_earned for r in responses)
        self.total_possible = sum(r.question.points for r in responses)

        if self.total_possible > 0:
            self.score_percentage = (self.score / self.total_possible) * 100
        else:
            self.score_percentage = 0

        self.save(update_fields=['score', 'total_possible', 'score_percentage'])

    @property
    def is_completed(self):
        return self.status == self.Status.COMPLETED

    @property
    def time_taken_formatted(self):
        """Return time taken in MM:SS format"""
        if not self.time_taken_seconds:
            return "N/A"
        minutes = self.time_taken_seconds // 60
        seconds = self.time_taken_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    # Alias for template compatibility
    time_taken_display = time_taken_formatted

    @property
    def correct_answers(self):
        """Count correct responses"""
        return self.responses.filter(is_correct=True).count()

    @property
    def total_questions(self):
        """Count total questions answered"""
        return self.responses.count()

    @property
    def can_retake(self):
        """Check if user can retake this quiz"""
        if self.quiz.max_attempts == 0:
            return True
        if not self.user:
            return True
        completed = QuizAttempt.objects.filter(
            quiz=self.quiz,
            user=self.user,
            status='COMPLETED'
        ).count()
        return completed < self.quiz.max_attempts


class Response(models.Model):
    """
    Individual responses to questions within an attempt
    """

    # Relationships
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')

    # Answers (different types)
    selected_answers = models.ManyToManyField(
        Answer,
        blank=True,
        related_name='responses',
        help_text="For multiple choice/select questions"
    )
    text_answer = models.TextField(
        blank=True,
        help_text="For short answer/essay questions"
    )

    # Grading
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    auto_graded = models.BooleanField(default=True)

    # Manual grading (for essays, etc.)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_responses'
    )
    grading_notes = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    # Timing
    time_spent_seconds = models.IntegerField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('response')
        verbose_name_plural = _('responses')
        ordering = ['attempt', 'question__order']
        unique_together = ['attempt', 'question']

    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.question.question_text[:50]}"

    @property
    def is_graded(self):
        """Check if this response has been graded"""
        return self.auto_graded or self.graded_at is not None

    def grade(self):
        """Automatically grade the response if possible"""
        question = self.question

        if question.question_type == Question.QuestionType.MULTIPLE_CHOICE:
            # Check if selected answer is correct
            selected = self.selected_answers.first()
            if selected and selected.is_correct:
                self.is_correct = True
                self.points_earned = question.points
            else:
                self.is_correct = False
                self.points_earned = 0

        elif question.question_type == Question.QuestionType.TRUE_FALSE:
            # Same as multiple choice
            selected = self.selected_answers.first()
            if selected and selected.is_correct:
                self.is_correct = True
                self.points_earned = question.points
            else:
                self.is_correct = False
                self.points_earned = 0

        elif question.question_type == Question.QuestionType.MULTIPLE_SELECT:
            # All correct answers must be selected, no incorrect ones
            correct_answers = set(question.answers.filter(is_correct=True))
            selected_answers = set(self.selected_answers.all())

            if correct_answers == selected_answers:
                self.is_correct = True
                self.points_earned = question.points
            else:
                self.is_correct = False
                self.points_earned = 0

        elif question.question_type == Question.QuestionType.SHORT_ANSWER:
            # Simple case-insensitive comparison
            if self.text_answer.strip().lower() == question.correct_answer_text.strip().lower():
                self.is_correct = True
                self.points_earned = question.points
            else:
                self.is_correct = False
                self.points_earned = 0
                self.auto_graded = False  # May need manual review

        elif question.question_type == Question.QuestionType.ESSAY:
            # Essays require manual grading
            self.auto_graded = False
            self.points_earned = 0

        elif question.question_type == Question.QuestionType.FILL_BLANK:
            # Similar to short answer
            if self.text_answer.strip().lower() == question.correct_answer_text.strip().lower():
                self.is_correct = True
                self.points_earned = question.points
            else:
                self.is_correct = False
                self.points_earned = 0

        self.save()

        # Update question statistics
        question.times_answered += 1
        if self.is_correct:
            question.times_correct += 1
        question.save(update_fields=['times_answered', 'times_correct'])

        # Update answer statistics
        for answer in self.selected_answers.all():
            answer.times_selected += 1
            answer.save(update_fields=['times_selected'])


class QuizTemplate(models.Model):
    """
    Reusable quiz templates (optional premium feature)
    """
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='templates')
    is_public = models.BooleanField(default=False)
    times_used = models.IntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('quiz template')
        verbose_name_plural = _('quiz templates')
        ordering = ['-times_used', '-created_at']

    def __str__(self):
        return self.name
