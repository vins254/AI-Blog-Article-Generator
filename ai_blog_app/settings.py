"""
Django settings for ContentFlow project.

This file centralizes all core configurations, including security keys,
database connections, and third-party API keys (AssemblyAI, OpenRouter).
"""
import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from decouple import config

# ── PROJECT PATHS ──
# BASE_DIR points to the root of the project (where manage.py lives).
BASE_DIR = Path(__file__).resolve().parent.parent


# ── SECURITY ──
SECRET_KEY = 'django-insecure-1ez!e9&4+@k)r7$5+gm!a+q_jrg_ga6+&vzs3xi9+v_awuvg*7'
DEBUG = True # Set to False in production!
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']


# ── INSTALLED MODULES ──
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog_generator' # Core logic for article processing
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Optimized static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # CSRF protection for AJAX requests
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_blog_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR, 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_blog_app.wsgi.application'


# ── DATABASE CONFIGURATION ──
# Uses SQLite for local development and PostgreSQL for production deployments.
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=False
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ── STATIC & MEDIA FILES ──
# Manages CSS, JS, and local audio transcriptions.
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR / "static")]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (temporary audio extractions reside here during processing)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ── THIRD-PARTY API INTEGRATION ──
# Keys are loaded from the .env file for security.
load_dotenv(os.path.join(BASE_DIR, '.env'))

ASSEMBLYAI_API_KEY = config("ASSEMBLYAI_API_KEY", default=None)
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default=None)

# ── AUTHENTICATION ──
LOGIN_URL = 'login'
