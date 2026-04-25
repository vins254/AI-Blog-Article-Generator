"""
=============================================================================
FILE: server/ai_blog_app/settings.py
PURPOSE: The central brain of the Django project — every configuration
         decision lives here. Django reads this file at startup to know
         how to behave in the current environment.
=============================================================================

HOW IT WORKS:
- Django imports this module automatically when the server starts because
  the DJANGO_SETTINGS_MODULE environment variable points to it (set in
  manage.py, wsgi.py, and asgi.py).
- Settings are read once at startup; changing them requires a server restart.

KEY SECTIONS EXPLAINED:

  1. BASE_DIR / ROOT_DIR
     BASE_DIR = the 'server/' folder (where manage.py lives).
     ROOT_DIR = the project root (parent of client/ and server/), used to
     resolve cross-folder paths like the client's templates and static files.

  2. SECRET_KEY
     A cryptographic key used to sign cookies and sessions. In production
     this MUST be kept private — ideally loaded from an environment variable,
     never committed to Git.

  3. INSTALLED_APPS
     Registers both Django's built-in apps (auth, admin, sessions, etc.)
     and our custom 'blog_generator' app so Django knows to include its
     models, views, and migrations.

  4. MIDDLEWARE
     A stack of layers that process every request/response. Critical ones:
     - SecurityMiddleware: Enforces HTTPS redirects in production.
     - WhiteNoiseMiddleware: Serves static files efficiently without needing
       a separate Nginx or CDN in simple deployments.
     - CsrfViewMiddleware: Validates the CSRF token on all POST requests.
     - AuthenticationMiddleware: Attaches the logged-in User object to every
       request so views can access request.user.

  5. TEMPLATES
     Tells Django where to look for HTML files. We point it to ROOT_DIR/client/
     templates so the templates and Python code stay physically separated.

  6. DATABASES
     Smart dual-mode setup: reads DATABASE_URL from the environment for
     production (PostgreSQL on Render, Railway, etc.). Falls back to a local
     SQLite file for local development — zero config needed.

  7. STATIC & MEDIA FILES
     STATICFILES_DIRS: Where Django collects static files from (client/static/).
     STATIC_ROOT: Where `collectstatic` copies them for production serving.
     MEDIA_ROOT: Where downloaded audio files land temporarily during processing.

  8. THIRD-PARTY API KEYS
     Loaded from server/.env using python-decouple. This ensures secrets are
     never hard-coded in source code — only ASSEMBLYAI_API_KEY and
     OPENROUTER_API_KEY need to be set.

TOOLS & LIBRARIES CONFIGURED HERE:
  - dj-database-url: Parses a DATABASE_URL connection string into Django format.
  - WhiteNoise: Compressed, cached static file serving for production.
  - python-decouple: Reads .env files for clean environment variable management.
  - python-dotenv: Loads .env into os.environ at startup.
=============================================================================
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from decouple import config

# ── PROJECT PATHS ──
# BASE_DIR points to the root of the project (where manage.py lives).
# BASE_DIR points to the 'server' directory.
BASE_DIR = Path(__file__).resolve().parent.parent
# ROOT_DIR points to the absolute project root (parent of client/ and server/).
ROOT_DIR = BASE_DIR.parent


# ── SECURITY ──
# In production, these MUST be set as environment variables in the Render dashboard.
# Never hard-code a real SECRET_KEY or leave DEBUG=True in production.
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)

# ALLOWED_HOSTS: Accepts the Render domain automatically.
# The RENDER_EXTERNAL_HOSTNAME env var is injected by Render at build time.
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
RENDER_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

# CSRF_TRUSTED_ORIGINS: Required for secure POST requests from the Render domain.
# Without this, all form submissions and AJAX calls will be rejected in production.
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
]
if RENDER_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_HOSTNAME}')

# PRODUCTION SECURITY HEADERS
# These settings are intentionally OFF in development (DEBUG=True) to keep
# local dev easy. They activate automatically when DEBUG=False on Render.
if not DEBUG:
    # Force all traffic through HTTPS
    SECURE_SSL_REDIRECT = True
    # Protect cookies from being sent over HTTP
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Tell browsers to only talk to this site over HTTPS for 1 year
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Prevent the browser from guessing content types (security best practice)
    SECURE_CONTENT_TYPE_NOSNIFF = True


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
        'DIRS': [os.path.join(ROOT_DIR, 'client', 'templates')],
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
# Supabase provides a PostgreSQL connection string (postgres://...).
# Set DATABASE_URL in the Render environment variables dashboard.
# Locally, falls back to SQLite so no setup is needed for development.
_database_url = os.environ.get('DATABASE_URL')
if _database_url:
    # Supabase URLs often include query params like ?pgbouncer=true that
    # psycopg2 doesn't understand and will crash on. We strip everything
    # after the '?' to keep only the core connection string.
    if '?' in _database_url:
        _database_url = _database_url.split('?')[0]

    # IMPORTANT: We use dj_database_url.parse() instead of .config() here.
    # .config() reads DATABASE_URL directly from os.environ (ignoring our
    # cleaned variable). .parse() takes our cleaned string directly.
    DATABASES = {
        'default': dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    # Local development: SQLite requires no configuration at all.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ── STATIC & MEDIA FILES ──
# Manages CSS, JS, and local audio transcriptions.
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(ROOT_DIR, 'client', 'static')]
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
