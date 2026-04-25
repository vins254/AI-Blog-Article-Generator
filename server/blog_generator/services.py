import os
import re
import requests
import json
import yt_dlp
import assemblyai as aai
from django.conf import settings
from .models import BlogPost

class BlogService:
    """
    A service layer that handles the core business logic of the application.
    By separating this from views.py, we make the code more testable, 
    reusable, and maintainable.
    """

    @staticmethod
    def get_video_title(link):
        ydl_opts = {'quiet': True, 'skip_download': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                return info.get("title", "Untitled Video")
        except Exception:
            return "Untitled Video"

    @staticmethod
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.splitext(filename)[0] + ".mp3"

    @staticmethod
    def transcribe_audio(audio_file_path):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        config = aai.TranscriptionConfig(speech_models=["universal"])
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)
        
        if transcript.status == aai.TranscriptStatus.error:
            return None
        return transcript.text

    @staticmethod
    def synthesize_article(transcription):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "X-Title": "ContentFlow",
        }
        
        # Safe truncation
        transcription = transcription[:4000]
        
        prompt = f"""
        Generate a professional article based on the following transcript.
        Requirements:
        - Structured headings (H1, H2, H3)
        - Professional tone
        - Concise bullet points
        - Meta description at end
        
        Transcript: {transcription}
        """

        data = {
            "model": "openrouter/free",
            "messages": [
                {"role": "system", "content": "You are a professional content editor."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=90)
            if response.status_code != 200:
                return None
            
            content = response.json()["choices"][0]["message"]["content"]
            # Clean DeepSeek <think> tags if present
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()
            return content
        except Exception:
            return None

    @classmethod
    def save_blog_post(cls, user, title, link, content):
        return BlogPost.objects.create(
            user=user,
            youtube_title=title,
            youtube_link=link,
            generated_content=content
        )
