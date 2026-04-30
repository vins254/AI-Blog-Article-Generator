"""
-----------------------------------------------------------------------------
FILE: server/blog_generator/urls.py
PURPOSE: The URL routing table for the blog_generator application.
AUTHORS: ContentFlow Development Team
-----------------------------------------------------------------------------
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
    path('task-status/<str:task_id>/', views.task_status, name='task-status'),
    
    # User data views
    path('blog-list', views.blog_list, name='blog-list'),
    path('blog-details/<int:pk>/', views.blog_details, name='blog-details'),
    path('delete-blog/<int:pk>/', views.delete_blog, name='delete-blog'),
]