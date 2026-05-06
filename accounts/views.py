"""
Account views for user authentication and profile.

QuizCraft Free Edition — quiz-taking only. Quiz creation, billing, and
subscription management are available in QuizCraft Pro:
https://djangozen.com/saas/product/quizcraft/
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm


def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Log the user in
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to QuizCraft!')
            return redirect('quiz:dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'quiz:dashboard')
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('quiz:index')


@login_required
def profile(request):
    """User profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def subscription(request):
    """Show current plan + Pro upgrade link.

    Free Edition shows the user's tier and a link to QuizCraft Pro.
    Pro purchase / Stripe billing is not handled inside this codebase.
    """
    context = {
        'user': request.user,
        'subscription_tier': request.user.get_subscription_tier_display(),
        'pro_url': 'https://djangozen.com/saas/product/quizcraft/',
    }
    return render(request, 'accounts/subscription.html', context)


# ===== PASSWORD RESET =====

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string


def password_reset_request(request):
    """Request a password reset email"""
    if request.user.is_authenticated:
        return redirect('quiz:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email:
            from .models import User
            try:
                user = User.objects.get(email=email)
                # Generate token
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(
                    f'/accounts/password-reset-confirm/{uid}/{token}/'
                )

                # Send email
                subject = 'QuizCraft - Password Reset'
                message = f"""Hello {user.first_name or user.username},

You requested a password reset for your QuizCraft account.

Click the link below to reset your password:
{reset_url}

If you didn't request this, you can safely ignore this email.

Best regards,
The QuizCraft Team"""

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except User.DoesNotExist:
                pass  # Don't reveal if email exists

        messages.success(request, 'If an account exists with that email, a password reset link has been sent.')
        return redirect('accounts:login')

    return render(request, 'accounts/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    """Confirm password reset with token"""
    from .models import User

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')

            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
                return render(request, 'accounts/password_reset_confirm.html', {'valid_link': True})

            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/password_reset_confirm.html', {'valid_link': True})

            user.set_password(password)
            user.save()
            messages.success(request, 'Your password has been reset successfully. You can now log in.')
            return redirect('accounts:login')

        return render(request, 'accounts/password_reset_confirm.html', {'valid_link': True})
    else:
        return render(request, 'accounts/password_reset_confirm.html', {'valid_link': False})
