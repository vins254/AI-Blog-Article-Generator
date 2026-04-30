"""
=============================================================================
FILE: server/blog_generator/apps.py
PURPOSE: The application configuration class for the 'blog_generator' Django
         app. This is how Django recognizes this folder as a self-contained
         application module within the larger project.
=============================================================================

HOW IT WORKS:
- Every Django app has an AppConfig class. Django reads this when the server
  starts and uses it to initialize the application correctly.
- The `name = 'blog_generator'` must exactly match the folder name, as Django
  uses this string to locate the app's models, views, migrations, etc.
- This class is referenced in settings.py under INSTALLED_APPS as
  'blog_generator', which tells Django to include it.
- You can also use this class to run startup logic via the ready() method
  (e.g., connecting signal handlers), though we don't need that here.

TOOLS:
  - AppConfig: Django's base class for application configuration.
    Subclassing it and setting `name` is the minimum required setup.
=============================================================================
"""
from django.apps import AppConfig



class BlogGeneratorConfig(AppConfig):
    name = 'blog_generator'
