from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout 
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
import assemblyai as aai
import yt_dlp
import requests
from .models import BlogPost

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)
        # get yt title
        title = yt_title(yt_link)
        
        # get transcript
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Failed to get transcript"}, status=500)
        
        #use OpenAI to generate the blog
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': " Failed to generate blog article"}, status=500)
        
        #save  blog article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=yt_link,
            generated_content=blog_content,
        )
        new_blog_article.save()
        
        #return blog article as a response
        return JsonResponse({'content': blog_content})
        
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)



def yt_title(link):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        return info.get("title", "Untitled Video")
    


def download_audio(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
        base = os.path.splitext(filename)[0]
        return base + ".mp3"

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
    config = aai.TranscriptionConfig(
        speech_models=["universal"]
    )
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(audio_file)
    return transcript.text


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",  # free model
        "messages": [
            {"role": "system", "content": "You are a professional SEO blog writer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1200
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    try:
        return result["choices"][0]["message"]["content"]
    except Exception:
        return None


def generate_blog_from_transcription(transcription):
    transcription = transcription[:4000]

    prompt = f"""
    Write a professional, SEO-optimized blog article based on the following transcript.

    Requirements:
    - Catchy blog title
    - Engaging introduction
    - Structured sections with subheadings
    - Bullet points where appropriate
    - Strong conclusion
    - Meta description at the end

    Transcript:
    {transcription}
    """

    return call_openrouter(prompt)





def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})
 
def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
         return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')
 
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
