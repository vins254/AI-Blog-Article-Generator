import re
import json
import os

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.conf import settings

import assemblyai as aai
import yt_dlp
import requests

from .models import BlogPost


# ── Pages ──

@login_required
def index(request):
    return render(request, 'index.html')


# ── Blog Generation ──

@login_required
def generate_blog(request):
    """
    Streaming view that provides real-time progress updates to the UI.
    Uses 'text/event-stream' format to push updates chunk by chunk.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        yt_link = data.get('link', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid data sent'}, status=400)

    # Validate YouTube URL
    if not yt_link or not re.match(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', yt_link
    ):
        return JsonResponse({'error': 'Please provide a valid YouTube URL.'}, status=400)


    def stream_generator():
        print(f"\n>>> INITIATING STREAMING PIPELINE for: {yt_link}")
        
        try:
            # Stage 1: Title
            yield json.dumps({'step': 1, 'msg': 'Extracting Video Metadata'}) + "\n"
            title = yt_title(yt_link)
            
            # Stage 2: Download
            yield json.dumps({'step': 2, 'msg': 'Downloading Audio Stream'}) + "\n"
            audio_file = download_audio(yt_link)
            
            # Stage 3: Transcription
            yield json.dumps({'step': 3, 'msg': 'Transcribing with AssemblyAI'}) + "\n"
            transcription = get_transcription(yt_link)
            if not transcription:
                yield json.dumps({'error': 'Transcription failed'}) + "\n"
                return

            # Stage 4: AI Synthesis
            # We add a small delay for UI readability
            yield json.dumps({'step': 4, 'msg': 'Synthesizing Professional Article'}) + "\n"
            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                yield json.dumps({'error': 'AI synthesis failed'}) + "\n"
                return

            # Archiving
            print(f"--- [Final] Archiving Content ---")
            new_post = BlogPost.objects.create(
                user=request.user,
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            print(f">>> SUCCESS: Article #{new_post.id} Created\n")

            # Final Output
            yield json.dumps({'step': 5, 'msg': 'Complete', 'content': blog_content}) + "\n"

        except Exception as e:
            print(f"!!! STREAMING EXCEPTION: {e}")
            yield json.dumps({'error': str(e)}) + "\n"

    return StreamingHttpResponse(stream_generator(), content_type='application/x-ndjson')


# ── YouTube Helpers ──

def yt_title(link):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }
    print(f"--- [1/4] Extracting Video Metadata ---")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            title = info.get("title", "Untitled Video")
            print(f"--- [1/4] Title: {title} ---")
            return title
    except Exception as e:
        print(f"!!! Error extracting title: {e}")
        return "Untitled Video"


def download_audio(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    print(f"--- [2/4] Downloading Audio Stream ---")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
        base = os.path.splitext(filename)[0]
        audio_path = base + ".mp3"
        print(f"--- [2/4] Download Complete: {os.path.basename(audio_path)} ---")
        return audio_path


def get_transcription(link):
    audio_file = download_audio(link)
    
    print(f"--- [3/4] Transcribing with AssemblyAI ---")
    aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
    config = aai.TranscriptionConfig(
        speech_models=["universal"]
    )
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_file)
    
    if transcript.status == aai.TranscriptStatus.error:
        print(f"!!! [3/4] Transcription Error: {transcript.error}")
        return None

    print(f"--- [3/4] Transcription Complete ({len(transcript.text)} chars) ---")
    return transcript.text


# ── AI Synthesis Engine (OpenRouter - Free Fallback) ──

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
# Using OpenRouter Auto-Router (Free Tier)
# This dynamically selects the best working free model to avoid 404s
ACTIVE_MODEL = "openrouter/free"


def call_synthesis_engine(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "ContentFlow",
    }

    data = {
        "model": ACTIVE_MODEL,
        "messages": [
            {"role": "system", "content": "You are a professional content editor. Write structured, SEO-optimized articles based on the provided material."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    print(f"--- [AI] Synthesis via OpenRouter ({ACTIVE_MODEL}) ---")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        if response.status_code != 200:
            print(f"!!! Synthesis Error [{response.status_code}]: {response.text}")
            return None
        result = response.json()
        if "choices" not in result or not result["choices"]:
            print(f"!!! Synthesis Error: Invalid response format")
            return None
        
        # Strip DeepSeek R1 reasoning tags if present
        content = result["choices"][0]["message"]["content"]
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        print(f"--- [AI] Synthesis Complete! ---")
        return content
    except Exception as e:
        print("Synthesis Engine Exception:", str(e))
        return None


def generate_blog_from_transcription(transcription):
    transcription = transcription[:4000]

    prompt = f"""
    Generate a professional article based on the following transcript.

    Requirements:
    - Structured headings (H1, H2, H3)
    - Professional, objective tone
    - Concise bullet points for key takeaways
    - Meta description at the end

    Transcript:
    {transcription}
    """

    return call_synthesis_engine(prompt)


# ── Blog Views (Authenticated & User-Scoped) ──

@login_required
def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})


@login_required
def blog_details(request, pk):
    try:
        blog_article_detail = BlogPost.objects.get(id=pk, user=request.user)
    except BlogPost.DoesNotExist:
        return redirect('/')
    return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})


# ── Authentication ──

def user_login(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            return render(request, 'login.html', {
                'error_message': 'Please fill in all fields.'
            })

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {
                'error_message': 'Invalid username or password.'
            })

    return render(request, 'login.html')


def user_signup(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        repeat_password = request.POST.get('repeatPassword', '')

        # Server-side validation
        if not username or not email or not password or not repeat_password:
            return render(request, 'signup.html', {
                'error_message': 'All fields are required.'
            })

        if len(username) < 3:
            return render(request, 'signup.html', {
                'error_message': 'Username must be at least 3 characters.'
            })

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return render(request, 'signup.html', {
                'error_message': 'Username can only contain letters, numbers, and underscores.'
            })

        if password != repeat_password:
            return render(request, 'signup.html', {
                'error_message': 'Passwords do not match.'
            })

        if len(password) < 8:
            return render(request, 'signup.html', {
                'error_message': 'Password must be at least 8 characters.'
            })

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {
                'error_message': 'Username is already taken.'
            })

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'error_message': 'An account with this email already exists.'
            })

        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'signup.html', {
                'error_message': e.messages[0]
            })

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            login(request, user)
            return redirect('/')
        except Exception:
            return render(request, 'signup.html', {
                'error_message': 'An error occurred while creating your account.'
            })

    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/login')
