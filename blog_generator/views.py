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
from transformers import pipeline, set_seed
import torch
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

generator = pipeline(
    "text-generation", 
    model="gpt2",
    device=0 if torch.cuda.is_available() else -1
    )
def generate_blog_from_transcription(transcription):
    transcription = transcription[:3000]

    prompt = f"""
        You are an expert technical blog writer.
        Analyze the transcript below and determine the MAIN topic being discussed.
        Then write a clear, well-structured educational blog article explaining that topic.
        Requirements:
        - Identify the central subject of the video.
        - Explain the concepts clearly and professionally.
        - Do NOT mention YouTube or the transcript.
        - Expand on important ideas where necessary.
        - Use clear Introduction, Body, and Conclusion sections.
        - Avoid repetition.

        Transcript:
        {transcription}
        Blog Article:
        Introduction:
        """

    result = generator(
        prompt,
        max_length=600,
        do_sample=True,
        temperature=0.9,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1.15,
        no_repeat_ngram_size=3,
        num_return_sequences=1
    )

    blog_text = result[0]["generated_text"]
    blog_text = blog_text.replace(prompt, "").strip()

    return blog_text

    #Limit transcript size
    transcription = transcription[:3000]

    #title
    title_prompt = f"""
        You are a professional blog writer.
        Create a compelling and creative blog title based on the following content.
        Content:
        {transcription}
        Title:
        """
    title = generate_section(title_prompt, 80)

    #introduction
    intro_prompt = f"""
        Write an engaging introduction for a professional blog article.
        Use storytelling and avoid repetition.

        Content:
        {transcription}

        Introduction:
        """
    introduction = generate_section(intro_prompt, 200)

    #body
    body_prompt = f"""
        Write the main body of a structured blog article. Use clear paragraphs and logical flow. Do not repeat phrases. Expand important ideas thoughtfully.
        Content:
        {transcription}
        Main Body:
        """
    body = generate_section(body_prompt, 400)

    
    conclusion_prompt = f"""
        Write a strong and reflective conclusion for this blog article. Make it impactful and professional.
        Content:{transcription}
        Conclusion:
    """
    conclusion = generate_section(conclusion_prompt, 150)

    blog_article = f"""
        {title}
        {introduction}
        {body}
        {conclusion}
    """
    return blog_article.strip()



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
