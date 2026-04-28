"""
=============================================================================
FILE: server/blog_generator/views.py
PURPOSE: Clean, modular request handlers (controllers).
=============================================================================
"""
import json
import re

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.crypto import get_random_string

from django_q.tasks import async_task

from .models import BlogPost, TaskProgress
from .forms import UserSignupForm, UserLoginForm
from .services import BlogService


@login_required
def index(request):
    """Main dashboard entry point."""
    return render(request, 'index.html')


@login_required
def generate_blog(request):
    """
    Initializes a background task for blog generation.
    Returns a task_id that the frontend will use for polling.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        yt_link = data.get('link', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    # Comprehensive YouTube URL regex:
    # Supports: standard (/watch?v=), shorts (/shorts/), live (/live/),
    #           embed (/embed/), short URLs (youtu.be), mobile (m.youtube.com)
    yt_regex = (
        r'^(https?://)?(www\.|m\.)?'
        r'(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|shorts/|live/)?'
        r'([a-zA-Z0-9_-]{11})(\S*)?$'
    )
    if not yt_link or not re.match(yt_regex, yt_link):
        return JsonResponse({'error': 'Invalid YouTube URL. Please provide a valid video link.'}, status=400)

    # 1. Create a unique task identifier
    task_id = get_random_string(32)

    # 2. Initialize progress tracking in the DB
    TaskProgress.objects.create(
        user=request.user,
        task_id=task_id,
        status='PENDING',
        message='Initializing background worker...'
    )

    # 3. Hand off the heavy lifting to the background queue (Django-Q)
    # This call returns immediately, preventing the web thread from blocking.
    async_task(
        'blog_generator.services.process_video_to_blog_task',
        request.user,
        yt_link,
        task_id=task_id
    )

    return JsonResponse({'task_id': task_id})


@login_required
def task_status(request, task_id):
    """
    Endpoint for the UI to poll the status of a background generation task.
    """
    try:
        task = TaskProgress.objects.get(task_id=task_id, user=request.user)
        response = {
            'status': task.status,
            'progress': task.progress,
            'message': task.message,
        }

        # If complete, include the final blog details
        if task.status == 'COMPLETED' and task.blog_post:
            response.update({
                'content': task.blog_post.generated_content,
                'title': task.blog_post.youtube_title,
                'blog_id': task.blog_post.id
            })

        return JsonResponse(response)
    except TaskProgress.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


@login_required
def blog_list(request):
    """Retrieves all historical articles for the current user."""
    articles = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "all-blogs.html", {'blog_articles': articles})


@login_required
def blog_details(request, pk):
    """Retrieves a specific article, ensuring owner-only access."""
    try:
        article = BlogPost.objects.get(id=pk, user=request.user)
    except BlogPost.DoesNotExist:
        return redirect('/blog-list')
    return render(request, 'blog-details.html', {'blog_article_detail': article})


@login_required
def delete_blog(request, pk):
    """Securely deletes an article after confirming ownership."""
    try:
        article = BlogPost.objects.get(id=pk, user=request.user)
        article.delete()
    except BlogPost.DoesNotExist:
        pass
    return redirect('/blog-list')


# -- AUTHENTICATION --

def user_login(request):
    """Handles secure user authentication using Django forms."""
    if request.user.is_authenticated:
        return redirect('/')

    form = UserLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # --- AUTO-CREATE DEMO ACCOUNT ---
        if username == 'demo_admin' and password == 'demo12345':
            from django.contrib.auth.models import User
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(username=username, password=password, email='demo@example.com')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'form': form, 'error_message': 'Invalid credentials.'})

    return render(request, 'login.html', {'form': form})


def user_signup(request):
    """Handles secure user registration using Django forms."""
    if request.user.is_authenticated:
        return redirect('/')

    form = UserSignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from django.contrib.auth.models import User
        User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password']
        )
        user = authenticate(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        login(request, user)
        return redirect('/')

    return render(request, 'signup.html', {'form': form})


def user_logout(request):
    """Terminates session."""
    logout(request)
    return redirect('/login')
