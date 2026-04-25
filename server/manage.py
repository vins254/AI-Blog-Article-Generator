#!/usr/bin/env python
"""
=============================================================================
FILE: server/manage.py
PURPOSE: The command-line entry point for the entire Django project. You use
         this file to run the development server, apply database migrations,
         create admin users, collect static files, and more.
=============================================================================

HOW IT WORKS:
- This is a thin wrapper around Django's management command infrastructure.
- It sets the DJANGO_SETTINGS_MODULE environment variable so that every
  Django command knows which settings file to use (ai_blog_app.settings).
- It then calls execute_from_command_line(sys.argv), which reads the
  arguments you typed in the terminal and dispatches to the right handler.

COMMON COMMANDS:
  python manage.py runserver          → Starts the local development server
                                        at http://127.0.0.1:8000/
  python manage.py migrate            → Applies pending database migrations
                                        (creates/alters tables in db.sqlite3)
  python manage.py makemigrations     → Generates new migration files when
                                        you change models.py
  python manage.py createsuperuser    → Creates a Django Admin account so you
                                        can access /admin/
  python manage.py collectstatic      → Copies all static files (CSS, JS) into
                                        STATIC_ROOT for production deployment
  python manage.py shell              → Opens an interactive Python shell with
                                        the Django environment fully loaded
  python manage.py check              → Validates the project configuration
                                        without starting the server
  python manage.py test               → Runs all test cases in tests.py

IMPORTANT:
  Always run this from the 'server/' directory, not the project root.
  The virtual environment (venv) must be active for Django to be importable.
=============================================================================
"""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
