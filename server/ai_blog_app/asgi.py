"""
=============================================================================
FILE: server/ai_blog_app/asgi.py
PURPOSE: The ASGI (Asynchronous Server Gateway Interface) entry point.
         ASGI is the modern successor to WSGI and is required for async
         features like WebSockets and long-lived HTTP connections.
=============================================================================

HOW IT WORKS:
- ASGI supports both synchronous AND asynchronous request handling, unlike
  WSGI which is synchronous-only.
- This project's streaming response (StreamingHttpResponse in views.py)
  works fine over WSGI, but ASGI would give even better performance for
  high-concurrency scenarios.
- The `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')`
  line points Django to the correct configuration before anything else loads.
- `get_asgi_application()` wraps the full Django stack (middleware, routing,
  ORM) into an ASGI-compatible callable.

WHEN TO USE ASGI vs WSGI:
  - WSGI (wsgi.py): Simpler, well-understood. Use for traditional deployments
    with Gunicorn on Render, Heroku, Railway.
  - ASGI (this file): Use when you need real WebSocket support (e.g., live
    chat) or when deploying with an ASGI server like Uvicorn or Daphne.
    Command: uvicorn ai_blog_app.asgi:application

TOOLS:
  - django.core.asgi.get_asgi_application: Django's ASGI adapter.
  - Uvicorn / Daphne: ASGI-compatible servers (not in requirements.txt by
    default since this project currently uses Gunicorn/WSGI).
=============================================================================
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')

application = get_asgi_application()
