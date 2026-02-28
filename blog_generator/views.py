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


HF_TOKEN = os.getenv("HF_TOKEN")  # Set this in Render Environment
HF_MODEL = "gpt2"  # You can replace with another Hugging Face model if desired
API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def call_hf_api(prompt, max_length=600):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_length,
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 50,
            "repetition_penalty": 1.15,
            "no_repeat_ngram_size": 3,
        },
        "options": {"wait_for_model": True}
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    data = response.json()
    try:
        return data[0]["generated_text"]
    except Exception:
        return "Error generating text"

def generate_blog_from_transcription(transcription):
    transcription = transcription[:3000]  # Limit size

    # Generate title
    title_prompt = f"""
    You are a professional blog writer.
    Create a compelling blog title based on the following content:
    {transcription}
    Title:
    """
    title = call_hf_api(title_prompt, max_length=20).strip()

    # Generate introduction
    intro_prompt = f"""
    Write an engaging introduction for a professional blog article.
    Use storytelling and avoid repetition.
    Content:
    {transcription}
    Introduction:
    """
    introduction = call_hf_api(intro_prompt, max_length=150).strip()

    # Generate body
    body_prompt = f"""
    Write the main body of a structured blog article.
    Use clear paragraphs and logical flow.
    Do not repeat phrases.
    Expand important ideas thoughtfully.
    Content:
    {transcription}
    Main Body:
    """
    body = call_hf_api(body_prompt, max_length=400).strip()

    # Generate conclusion
    conclusion_prompt = f"""
    Write a strong and reflective conclusion for this blog article.
    Content:
    {transcription}
    Conclusion:
    """
    conclusion = call_hf_api(conclusion_prompt, max_length=150).strip()

    # Combine into full blog
    blog_article = f"{title}\n\n{introduction}\n\n{body}\n\n{conclusion}"
    return blog_article



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
