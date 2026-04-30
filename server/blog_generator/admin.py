"""
=============================================================================
FILE: server/blog_generator/admin.py
PURPOSE: Registers the application's models with Django's built-in Admin
         interface, giving you a ready-made web dashboard to browse, search,
         edit, and delete database records — with zero extra code.
=============================================================================

HOW IT WORKS:
- Django ships with a fully-featured admin panel available at /admin/.
- You need a superuser account to log in: create one with
  `python manage.py createsuperuser`.
- By calling admin.site.register(BlogPost), we tell Django to include the
  BlogPost model in the admin panel.
- Once registered, you can see every article in the database, filter by user,
  search by title, and manually delete or edit records — extremely useful
  during development and for production data management.

TOOLS:
  - django.contrib.admin: Django's built-in admin framework.
  - admin.site.register(): The one-line call that makes a model visible
    in the admin panel with a default list/detail view.

TO ACCESS:
  1. Run `python manage.py createsuperuser` to create an admin account.
  2. Start the server and go to http://127.0.0.1:8000/admin/
  3. Log in and you'll see "Blog Generator > Blog posts" in the sidebar.
=============================================================================
"""
from django.contrib import admin

from .models import BlogPost
# Register your models here.
admin.site.register(BlogPost)