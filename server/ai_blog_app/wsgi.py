"""
=============================================================================
FILE: server/ai_blog_app/wsgi.py
PURPOSE: The WSGI (Web Server Gateway Interface) entry point for production
         deployment. WSGI is the standard Python interface between web
         servers (like Gunicorn or uWSGI) and Python web applications.
=============================================================================

HOW IT WORKS:
- WSGI is synchronous — it handles one request at a time per worker process.
- In production on platforms like Render or Railway, the server runs:
    gunicorn ai_blog_app.wsgi:application
  This tells Gunicorn to import 'application' from this module and use it
  to handle all incoming HTTP traffic.
- The `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')`
  line ensures Django loads the correct configuration file before it starts.
- `get_wsgi_application()` initializes the full Django stack (middleware,
  URL routing, ORM, etc.) and returns a callable that Gunicorn can call
  for each HTTP request.

LOCAL vs PRODUCTION:
  - Locally: You use `python manage.py runserver` instead. That command also
    uses WSGI internally but adds hot-reload and debug tooling on top.
  - Production: Gunicorn uses this file directly, running multiple parallel
    worker processes for better throughput.

TOOLS:
  - django.core.wsgi.get_wsgi_application: Creates the WSGI callable.
  - Gunicorn: The recommended production WSGI server (defined in requirements.txt).
=============================================================================
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')

application = get_wsgi_application()
