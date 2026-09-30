"""
Django settings for smartwaste_project project.
SMART WASTE MANAGEMENT SYSTEM - SPECTRUM HACKATHON
"""

import os
from pathlib import Path

# Build paths inside the project: BASE_DIR is backend/
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Quick-start development settings - unsuitable for production
# In production, SECRET_KEY is read from environment variable or falls back to secure default
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-smartwaste-hackathon-spectrum-2026-secure-key-ec2-deployment'
)

# DEBUG is True by default for local dev. Production should set DJANGO_DEBUG=False
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1')

# Allowed hosts for domain, EC2 public IP and local reverse proxy access
ALLOWED_HOSTS = [
    'cleanloop.sarthakml.in',
    'www.cleanloop.sarthakml.in',
    '16.171.238.127',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '*',  # Permissive for hackathon demo to ensure external judges can connect without host header mismatch
]

# CSRF trusted origins for web forms submitted from cleanloop domain & public IP
CSRF_TRUSTED_ORIGINS = [
    'https://cleanloop.sarthakml.in',
    'https://www.cleanloop.sarthakml.in',
    'http://cleanloop.sarthakml.in',
    'http://www.cleanloop.sarthakml.in',
    'http://16.171.238.127',
    'http://localhost',
    'http://127.0.0.1',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Core waste management application
    'waste_management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartwaste_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [PROJECT_ROOT / 'frontend' / 'pages'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartwaste_project.wsgi.application'

# Database
# Using SQLite3 as strictly required by tech constraints
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_ROOT / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'
STATICFILES_DIRS = [
    PROJECT_ROOT / 'frontend',
]

# Media files (for complaint image uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = PROJECT_ROOT / 'media'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'citizen_dashboard'
LOGOUT_REDIRECT_URL = 'landing'

# File upload security limits (maximum 5MB for complaint pictures)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
