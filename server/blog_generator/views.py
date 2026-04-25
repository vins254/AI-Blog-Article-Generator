"""
=============================================================================
FILE: server/blog_generator/views.py
PURPOSE: The core controller of the application. This file contains every
         view function — the Python code that runs in response to HTTP
         requests and decides what data to fetch and what HTML to return.
=============================================================================

HOW IT WORKS — OVERALL FLOW:
  Every URL in urls.py maps to one function in this file. Django calls that
  function with the incoming HTTP Request object, and the function returns
  an HTTP Response (HTML page, JSON, or a data stream).

VIEWS DEFINED IN THIS FILE:

  1. index(request)
     Renders the main dashboard (index.html). Protected by @login_required
     so only authenticated users can see it.

  2. generate_blog(request)  ← THE HEART OF THE APP
     Accepts a POST request with a YouTube URL.
     Instead of processing everything then sending ONE response, it uses a
     Python generator function (stream_generator) with Django's
     StreamingHttpResponse. This allows it to 'yield' (send) progress
     updates to the browser in real time as each stage completes:
       Stage 1 → Extract video title via yt-dlp
       Stage 2 → Download audio stream via yt-dlp + FFmpeg
       Stage 3 → Transcribe audio via AssemblyAI SDK
       Stage 4 → Generate article via OpenRouter (LLM API)
       Stage 5 → Save to database, send final HTML to browser

  3. yt_title(link)
     A helper that calls yt-dlp in metadata-only mode (no download) to
     quickly grab the video's title string for database labeling.

  4. download_audio(link)
     Calls yt-dlp to download the best available audio track, then runs
     it through FFmpeg (via yt-dlp's FFmpegExtractAudio post-processor)
     to produce an MP3 file saved in server/media/.

  5. get_transcription(link)
     Sends the MP3 file to AssemblyAI's Universal neural transcription
     model. Waits for the result and returns the text. Returns None if
     the transcription job fails (bad audio, timeout, etc.).

  6. call_synthesis_engine(prompt)
     Sends the raw transcript text to OpenRouter's chat completions API.
     Uses the "openrouter/free" model auto-router which automatically
     picks the best available free LLM at runtime (DeepSeek, Llama, etc.).
     Also strips <think> tags that some reasoning models include.

  7. generate_blog_from_transcription(transcription)
     Builds the master prompt string that instructs the LLM exactly how
     to structure the article, then calls call_synthesis_engine().

  8. blog_list(request) / blog_details(request, pk)
     Data retrieval views. Each query is scoped to the logged-in user
     (filter(user=request.user)) so users can only ever access their own data.

  9. user_login / user_signup / user_logout
     Standard Django auth flows. Passwords are NEVER stored in plain text —
     Django's create_user() automatically applies PBKDF2+SHA256 hashing.
     Password strength is validated by Django's built-in AUTH_PASSWORD_VALIDATORS.

SECURITY LAYERS:
  - @login_required: Redirects unauthenticated requests to /login.
  - CSRF validation: Enforced by Django's CsrfViewMiddleware for all POSTs.
  - Object-level ownership: blog_details uses .get(id=pk, user=request.user)
    so guessing another article's ID in the URL returns a 404/redirect.
  - Input validation: YouTube URL is regex-checked before any API is called.

THIRD-PARTY LIBRARIES USED:
  - assemblyai: Official AssemblyAI Python SDK for speech-to-text.
  - yt_dlp: YouTube download library (fork of youtube-dl) for audio extraction.
  - requests: HTTP library for calling the OpenRouter REST API.
=============================================================================
"""
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


# ── PAGE VIEWS ──

@login_required
def index(request):
    """Renders the main dashboard for generating articles."""
    return render(request, 'index.html')


# ── CORE GENERATION PIPELINE ──

@login_required
def generate_blog(request):
    """
    This is the heart of the application. It orchestrates the entire process 
    of turning a YouTube video into a readable article. 
    
    We use a StreamingHttpResponse because the process takes time (downloading, 
    transcribing, and AI processing). Streaming allows us to give the user 
    real-time feedback so they know the app hasn't frozen.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed here!'}, status=405)

    try:
        # We expect a JSON body containing the 'link' property.
        data = json.loads(request.body)
        yt_link = data.get('link', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'The data sent was malformed.'}, status=400)

    # Basic check to make sure it's actually a YouTube link before we start 
    # spinning up expensive AI services.
    if not yt_link or not re.match(
        r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+', yt_link
    ):
        return JsonResponse({'error': 'That doesn\'t look like a valid YouTube URL.'}, status=400)


    def stream_generator():
        """
        This inner generator function yields chunks of JSON. 
        Each 'yield' is immediately pushed to the browser.
        """
        print(f"\n[PIPELINE START] User: {request.user} | URL: {yt_link}")
        
        try:
            # STEP 1: Get the video title. 
            # We do this first so we can label the entry in the database.
            yield json.dumps({'step': 1, 'msg': 'Fetching video details'}) + "\n"
            title = yt_title(yt_link)
            
            # STEP 2: Extract Audio. 
            # AssemblyAI needs an audio file to transcribe. We use yt-dlp to 
            # grab the best audio stream and FFmpeg to save it as an MP3.
            yield json.dumps({'step': 2, 'msg': 'Extracting audio from video'}) + "\n"
            audio_file = download_audio(yt_link)
            
            # STEP 3: Transcription.
            # We send the MP3 to AssemblyAI. Their 'universal' model is great 
            # at handling different accents and audio qualities.
            yield json.dumps({'step': 3, 'msg': 'Transcribing speech to text'}) + "\n"
            transcription = get_transcription(yt_link)
            if not transcription:
                yield json.dumps({'error': 'We couldn\'t get a clean transcript. Try another video.'}) + "\n"
                return

            # STEP 4: AI Article Generation.
            # Raw transcripts are usually messy. We send the text to a Large 
            # Language Model (via OpenRouter) to rewrite it into a structured, 
            # professional article.
            yield json.dumps({'step': 4, 'msg': 'AI is writing your article'}) + "\n"
            blog_content = generate_blog_from_transcription(transcription)
            if not blog_content:
                yield json.dumps({'error': 'The AI synthesis failed. This usually happens if the transcript is too short.'}) + "\n"
                return

            # STEP 5: Persistence.
            # Save the result to the database so the user can access it 
            # later from their dashboard.
            print(f"[DATABASE] Saving article: {title}")
            new_post = BlogPost.objects.create(
                user=request.user,
                youtube_title=title,
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            print(f"[PIPELINE SUCCESS] ID: {new_post.id}")

            # Final payload: Tells the UI we are done and provides the full content.
            yield json.dumps({'step': 5, 'msg': 'Success!', 'content': blog_content}) + "\n"

        except Exception as e:
            # Catch-all for unexpected issues (network drops, API timeouts, etc.)
            print(f"[PIPELINE ERROR] {str(e)}")
            yield json.dumps({'error': f'Something went wrong: {str(e)}'}) + "\n"

    # NDJSON is the standard for streaming multiple JSON objects.
    return StreamingHttpResponse(stream_generator(), content_type='application/x-ndjson')


# ── SERVICE HELPERS ──

def yt_title(link):
    """Uses yt-dlp to extract the video title without downloading the video itself."""
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
    """
    Downloads theBest available audio stream and uses FFmpeg to extract it as an MP3.
    Files are saved in the project's 'media' directory.
    """
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
    """Interfaces with AssemblyAI to perform the transcription."""
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


# ── AI SYNTHESIS ENGINE (OpenRouter) ──

OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
# Using 'openrouter/free' auto-router. This ensures high availability (HA)
# by automatically falling back to any available free model at runtime.
ACTIVE_MODEL = "openrouter/free"


def call_synthesis_engine(prompt):
    """Handles the API call to OpenRouter to turn raw text into structured articles."""
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
        
        # DeepSeek R1 specific logic: Clean the output by removing the <think> reasoning chain.
        # This keeps the article clean and professional for the end-user.
        content = result["choices"][0]["message"]["content"]
        if "<think>" in content and "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        print(f"--- [AI] Synthesis Complete! ---")
        return content
    except Exception as e:
        print("Synthesis Engine Exception:", str(e))
        return None


def generate_blog_from_transcription(transcription):
    """Constructs the master prompt for the AI synthesis engine."""
    # Truncate length to stay within safe token limits for free models
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


# ── USER-SCOPED DATA VIEWS ──

@login_required
def blog_list(request):
    """Displays only the articles generated by the logged-in user."""
    blog_articles = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})


@login_required
def blog_details(request, pk):
    """Displays the full content of a specific article with security scope check."""
    try:
        blog_article_detail = BlogPost.objects.get(id=pk, user=request.user)
    except BlogPost.DoesNotExist:
        return redirect('/')
    return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})


# ── AUTHENTICATION ──

def user_login(request):
    """Standard Django Auth for login."""
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
    """
    Handles secure user registration with password strength verification.
    """
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        repeat_password = request.POST.get('repeatPassword', '')

        # Server-side validation
        if not username or not email or not password or not repeat_password:
            return render(request, 'signup.html', {'error_message': 'All fields are required.'})

        if len(username) < 3:
            return render(request, 'signup.html', {'error_message': 'Username must be at least 3 characters.'})

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return render(request, 'signup.html', {'error_message': 'Username can only contain alphanumeric/underscores.'})

        if password != repeat_password:
            return render(request, 'signup.html', {'error_message': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error_message': 'Username is already taken.'})

        # Validate password strength using Django's built-in security policies
        try:
            validate_password(password)
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            login(request, user)
            return redirect('/')
        except ValidationError as e:
            return render(request, 'signup.html', {'error_message': e.messages[0]})
        except Exception:
            return render(request, 'signup.html', {'error_message': 'Account creation failed.'})

    return render(request, 'signup.html')


def user_logout(request):
    """Terminal session and redirect to login."""
    logout(request)
    return redirect('/login')
