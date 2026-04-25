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
from django.http import JsonResponse, StreamingHttpResponse

from .models import BlogPost
from .forms import UserSignupForm, UserLoginForm
from .services import BlogService


@login_required
def index(request):
    """Main dashboard entry point."""
    return render(request, 'index.html')


@login_required
def generate_blog(request):
    """
    Orchestrates the blog generation pipeline using the Service layer.
    Uses NDJSON streaming for real-time UI updates.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        yt_link = data.get('link', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    # Basic validation before starting the pipeline
    if not yt_link or not re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', yt_link):
        return JsonResponse({'error': 'Invalid YouTube URL provided.'}, status=400)

    def stream_generator():
        try:
            # Stage 1: Metadata
            yield json.dumps({'step': 1, 'msg': 'Identifying video source...'}) + "\n"
            title = BlogService.get_video_title(yt_link)
            
            # Stage 2: Audio Extraction
            yield json.dumps({'step': 2, 'msg': 'Pulling audio from stream...'}) + "\n"
            audio_path = BlogService.download_audio(yt_link)
            
            # Stage 3: Transcription
            yield json.dumps({'step': 3, 'msg': 'Turning speech into text...'}) + "\n"
            transcription = BlogService.transcribe_audio(audio_path)
            if not transcription:
                yield json.dumps({'error': 'Failed to generate transcription.'}) + "\n"
                return

            # Stage 4: AI Synthesis
            yield json.dumps({'step': 4, 'msg': 'Structuring article draft...'}) + "\n"
            content = BlogService.synthesize_article(transcription)
            if not content:
                yield json.dumps({'error': 'AI synthesis engine failed.'}) + "\n"
                return

            # Stage 5: Finalization & Persistence
            BlogService.save_blog_post(request.user, title, yt_link, content)
            yield json.dumps({'step': 5, 'msg': 'Success', 'content': content, 'title': title}) + "\n"

        except Exception as e:
            yield json.dumps({'error': f'Internal pipeline error: {str(e)}'}) + "\n"

    return StreamingHttpResponse(stream_generator(), content_type='application/x-ndjson')


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


# ── AUTHENTICATION ──

def user_login(request):
    """Handles secure user authentication using Django forms."""
    if request.user.is_authenticated:
        return redirect('/')

    form = UserLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request, 
            username=form.cleaned_data['username'], 
            password=form.cleaned_data['password']
        )
        if user:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'form': form, 'error_message': 'Invalid credentials'})

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
