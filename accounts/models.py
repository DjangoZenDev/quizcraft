"""
User Account Models for QuizCraft
Includes custom user model with subscription tiers and preferences
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser
    Adds subscription tier and user preferences
    """

    class SubscriptionTier(models.TextChoices):
        FREE = 'FREE', _('Free')
        TEACHER = 'TEACHER', _('Teacher')
        PROFESSIONAL = 'PROFESSIONAL', _('Professional')
        SCHOOL = 'SCHOOL', _('School')
        ENTERPRISE = 'ENTERPRISE', _('Enterprise')

    # Additional user fields
    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(max_length=500, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    website = models.URLField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    # Subscription information
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)

    # Usage tracking
    total_quizzes_created = models.IntegerField(default=0)
    total_responses_received = models.IntegerField(default=0)

    # Preferences
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    @property
    def is_subscribed(self):
        """Check if user has an active paid subscription"""
        return self.subscription_tier != self.SubscriptionTier.FREE

    @property
    def can_create_quiz(self):
        """Check if user can create more quizzes based on tier"""
        from django.conf import settings
        if self.is_subscribed:
            return True
        return self.total_quizzes_created < settings.MAX_FREE_QUIZZES

    @property
    def remaining_free_quizzes(self):
        """Calculate remaining quizzes for free tier users"""
        from django.conf import settings
        if self.is_subscribed:
            return float('inf')
        return max(0, settings.MAX_FREE_QUIZZES - self.total_quizzes_created)


class UserProfile(models.Model):
    """
    Extended user profile for additional information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Professional information
    job_title = models.CharField(max_length=100, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    grades_taught = models.CharField(max_length=100, blank=True, help_text="e.g., 6-8, High School")
    subjects_taught = models.CharField(max_length=200, blank=True, help_text="Comma-separated")

    # Social links
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(max_length=200, blank=True)

    # Timezone
    timezone = models.CharField(max_length=50, default='UTC')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.username}'s profile"
