"""
=============================================================================
FILE: server/blog_generator/urls.py
PURPOSE: The URL routing table for the blog_generator application. Every
         user-facing URL in ContentFlow is defined here and mapped to its
         corresponding view function in views.py.
=============================================================================

HOW IT WORKS:
- This file is loaded via include('blog_generator.urls') from the project-
  level urls.py (ai_blog_app/urls.py). Django hands off any request that
  doesn't go to /admin/ to this file for further matching.
- Each `path()` call pairs a URL string pattern with a view function. When
  Django finds a match, it calls that function and returns its response.
- Named URLs (name='index', name='login', etc.) allow views and templates
  to reference URLs symbolically using {% url 'name' %} or redirect('name')
  instead of hard-coding strings — making future URL changes much easier.

URL MAP:
  /                          → views.index         (main dashboard)
  /login                     → views.user_login     (login page)
  /signup                    → views.user_signup    (registration page)
  /logout                    → views.user_logout    (clears session, redirects)
  /generate-blog             → views.generate_blog  (streaming API endpoint)
  /blog-list                 → views.blog_list      (archive page)
  /blog-details/<int:pk>/    → views.blog_details   (single article reader)

ABOUT <int:pk>:
  The <int:pk> in the blog-details URL is a path converter. It captures the
  integer in the URL (e.g., /blog-details/42/) and passes it as the `pk`
  (primary key) argument to the view function. The view then uses that ID
  to look up the correct database record.

TOOLS:
  - django.urls.path: Matches exact URL strings (no regex needed for simple paths).
  - Path converters (<int:pk>): Automatically validates and converts URL segments
    into Python types before passing them to the view.
=============================================================================
"""
from django.urls import path
from . import views

# ROUTING ARCHITECTURE
# This file maps incoming browser requests to specific Python functions in views.py.

urlpatterns = [
    # The main application dashboard
    path('', views.index, name='index'),
    
    # Authentication routes
    path('login', views.user_login, name='login'),
    path('signup', views.user_signup, name='signup'),
    path('logout', views.user_logout, name='logout'),
    
    # Core API endpoints
    path('generate-blog', views.generate_blog, name='generate-blog'),
    
    # User data views
    path('blog-list', views.blog_list, name='blog-list'),
    path('blog-details/<int:pk>/', views.blog_details, name='blog-details'),
]