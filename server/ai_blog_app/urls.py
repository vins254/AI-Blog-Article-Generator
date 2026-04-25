"""
=============================================================================
FILE: server/ai_blog_app/urls.py
PURPOSE: The top-level URL router for the entire Django project. This is the
         first file Django consults when a browser request arrives — it acts
         like the main switchboard that routes traffic to the right app.
=============================================================================

HOW IT WORKS:
- Django reads this file because ROOT_URLCONF = 'ai_blog_app.urls' is set
  in settings.py. Every HTTP request enters here first.
- The `include('blog_generator.urls')` call delegates ALL routes (except
  /admin/) to the blog_generator app's own urls.py file. This keeps routing
  modular — the project root doesn't need to know the details of each app.
- `admin.site.urls` mounts Django's built-in admin panel at /admin/.
- The `static(...)` call appended at the bottom adds a special URL rule so
  that files stored in MEDIA_ROOT (downloaded MP3s, etc.) are accessible
  via the /media/ URL prefix during local development.
  NOTE: In production, a proper web server (Nginx, Cloudfront) should serve
  media files instead — Django is not optimized for static/media file serving.

SCALABILITY NOTE:
  As the project grows, you can add new Django apps here by adding more
  include() entries. For example:
    path('api/v2/', include('api_v2.urls'))
  This keeps each feature area isolated and independently testable.

TOOLS:
  - django.urls.path: Defines a URL pattern matched by exact string.
  - django.urls.include: Delegates a URL namespace to another urls.py file.
  - django.conf.urls.static.static: Serves MEDIA_ROOT files in development.
=============================================================================
"""
# ── PROJECT-LEVEL ROUTING ──

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # The administrative control panel (built-in Django Admin)
    path('admin/', admin.site.urls),
    
    # We delegate all other requests to our 'blog_generator' app
    path('', include('blog_generator.urls'))
]

# Static & Media Asset Handling
# This ensures that files in the /media/ directory (like audio files) 
# are accessible via URL during development.
urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
