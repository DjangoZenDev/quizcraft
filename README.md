# QuizCraft — Free Edition

**A SaaS quiz-taking platform for educators, trainers, and content creators.**

Built with Django 5.2+ and Bootstrap 5.3.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License: Source-Available](https://img.shields.io/badge/License-Source--Available-orange.svg)](LICENSE.md)

> **This is QuizCraft Free Edition — quiz-taking only.** Quiz creation, Stripe billing, and commercial deployment rights are exclusive to **[QuizCraft Pro](https://djangozen.com/saas/product/quizcraft/)** (€249).

---

## What's Included (Free Edition)

- **Browse & take quizzes** — public quiz catalogue, attempts, scoring
- **Auto-grading** for objective question types (Multiple Choice, True/False, Short Answer)
- **Quiz timer** with configurable per-quiz countdown
- **User dashboard** with attempt history and stats
- **Multi-Language** — EN, NL, ES, DE, FR with language switcher
- **Dark mode** with system preference auto-detection
- **Responsive design** — mobile-friendly Bootstrap 5.3 interface

## Pro Features (paid — not in this repo)

- Quiz creation, editing, and deletion (Pro deployers seed quizzes via Django admin)
- Stripe-powered subscription billing for end users
- Multi-tier subscription gating (Teacher / Professional / School / Enterprise)
- Commercial deployment licence

For Pro features and licence, see [LICENSE.md](LICENSE.md) and visit https://djangozen.com/saas/product/quizcraft/

---

## Quick Start

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Navigate to the project
cd QuizCraft

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
copy .env.example .env
# Edit .env with your settings

# 6. Run migrations
python manage.py migrate

# 7. Create a superuser
python manage.py createsuperuser

# 8. Run the server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
QuizCraft/
├── accounts/              # User authentication & profiles
│   ├── models.py          # Custom User model with subscriptions
│   ├── views.py           # Register, Login, Profile, Subscription
│   ├── forms.py           # Auth forms with Bootstrap widgets
│   └── admin.py           # Custom admin with subscription badges
├── quiz/                  # Core quiz functionality
│   ├── models.py          # Quiz, Question, Answer, Attempt, Response
│   ├── views.py           # 13+ views for quiz management
│   ├── forms.py           # Quiz creation forms
│   └── admin.py           # Comprehensive admin with inlines
├── quizcraft/             # Project settings
│   ├── settings.py        # Production-ready configuration
│   ├── urls.py            # URL routing with i18n
│   └── wsgi.py
├── templates/             # HTML templates
│   ├── base.html          # Main layout with dark mode & i18n
│   ├── accounts/          # Auth templates (login, register, profile)
│   ├── quiz/              # Quiz templates (10 templates)
│   ├── 404.html           # Error pages
│   ├── 403.html
│   └── 500.html
├── static/
│   ├── css/style.css      # Custom CSS with dark mode support
│   └── js/timer.js        # Quiz timer functionality
├── locale/                # Translation files
│   ├── nl/                # Dutch
│   ├── es/                # Spanish
│   ├── de/                # German
│   └── fr/                # French
├── media/                 # User uploads
├── logs/                  # Application logs
├── product_images/        # Product preview images (1200x850)
├── .env.example           # Environment template
├── requirements.txt
├── LICENSE.md
└── README.md
```

---

## Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | Django secret key |
| `DEBUG` | `False` | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hostnames |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection |
| `EMAIL_BACKEND` | Console | Email backend |
| `STRIPE_PUBLIC_KEY` | (empty) | Stripe publishable key |
| `STRIPE_SECRET_KEY` | (empty) | Stripe secret key |
| `MAX_FREE_QUIZZES` | `5` | Free tier quiz limit |
| `MAX_FREE_RESPONSES` | `50` | Free tier response limit |

---

## Subscription Tiers

| Tier | Features |
|------|----------|
| **Free** | 5 quizzes, 50 responses/month |
| **Teacher** | Unlimited quizzes & responses |
| **Professional** | Team features, advanced analytics |
| **School** | 10+ users, LMS integrations |
| **Enterprise** | White-label, self-hosted, custom |

---

## Security

- SECRET_KEY stored in environment variables
- HTTPS/SSL redirect in production
- Secure cookies (session & CSRF)
- XSS & clickjacking protection (X-Frame-Options: DENY)
- HSTS headers (1 year, include subdomains, preload)
- Content-Type nosniff
- Password validation (min 8 chars, complexity rules)
- Rotating log files (15MB max, 10 backups)

---

## Development

```bash
# Run tests
python manage.py test

# Run Django checks
python manage.py check

# Collect static files
python manage.py collectstatic

# Generate translations
python manage.py makemessages -l nl -l es -l de -l fr
python manage.py compilemessages
```

### Production Deployment

```bash
# With Gunicorn
gunicorn quizcraft.wsgi:application --bind 0.0.0.0:8000

# With WhiteNoise for static files (already configured)
python manage.py collectstatic --noinput
```

---

## Tech Stack

- **Backend:** Django 5.2+, Python 3.12+
- **Frontend:** Bootstrap 5.3, Bootstrap Icons
- **API:** Django REST Framework 3.16+
- **Auth:** Django built-in + SimpleJWT
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Payments:** Stripe (ready)
- **Static:** WhiteNoise
- **Server:** Gunicorn

---

## License

QuizCraft Free Edition is released under a **source-available licence** — free for evaluation, learning, and non-commercial self-hosting. Commercial use, SaaS hosting, and redistribution require purchasing a commercial licence.

See [LICENSE.md](LICENSE.md) for full terms. Commercial pricing tiers:

- **Starter** — €249 (1 deployment, internal commercial use)
- **Professional** — €996 (multi-deployment, paying users / SaaS)
- **Business / SaaS** — €2,490 (unlimited, white-label, resell)

Buy a licence: https://djangozen.com/saas/product/quizcraft/

---

## Version

**Current Version:** 1.0.0

**Status:** Production Ready (SaaS)
