"""
Django Admin configuration for User accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    list_display = ('username', 'email', 'subscription_badge', 'total_quizzes_created',
                   'total_responses_received', 'is_staff', 'date_joined')
    list_filter = ('subscription_tier', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'organization')

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {
            'fields': ('bio', 'organization', 'website', 'avatar')
        }),
        ('Subscription', {
            'fields': ('subscription_tier', 'subscription_start_date', 'subscription_end_date',
                      'stripe_customer_id', 'stripe_subscription_id')
        }),
        ('Usage Statistics', {
            'fields': ('total_quizzes_created', 'total_responses_received')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'marketing_emails')
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'total_quizzes_created', 'total_responses_received')

    def subscription_badge(self, obj):
        colors = {
            'FREE': 'gray',
            'TEACHER': 'blue',
            'PROFESSIONAL': 'purple',
            'SCHOOL': 'orange',
            'ENTERPRISE': 'green'
        }
        color = colors.get(obj.subscription_tier, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_subscription_tier_display()
        )
    subscription_badge.short_description = 'Subscription'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin"""
    list_display = ('user', 'job_title', 'school_name', 'timezone')
    search_fields = ('user__username', 'user__email', 'job_title', 'school_name')
    list_filter = ('timezone', 'created_at')

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('job_title', 'school_name', 'grades_taught', 'subjects_taught')
        }),
        ('Social Links', {
            'fields': ('twitter', 'linkedin')
        }),
        ('Settings', {
            'fields': ('timezone',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')
