"""
URL configuration for QuizCraft project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),

    # Admin
    path('admin/', admin.site.urls),

    # Apps
    path('', include('quiz.urls')),
    path('accounts/', include('accounts.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
