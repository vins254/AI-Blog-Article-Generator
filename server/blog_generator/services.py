import os
import re
import requests
import json
import yt_dlp
import assemblyai as aai
from django.conf import settings
from .models import BlogPost, TaskProgress


def process_video_to_blog_task(user, link, task_id=None):
    """
    Background worker function called by Django-Q.
    Handles the entire 'Video -> Audio -> Text -> Synthesis' pipeline.
    """
    try:
        print(f"\n[PIPELINE] Starting generation for: {link}")
        
        BlogService._update_progress(task_id, 10, "Reading the link and fetching video info...")
        title = BlogService.get_video_title(link)
        print(f"[PIPELINE] Video title: {title}")

        BlogService._update_progress(task_id, 30, "Downloading the audio track from the video...")
        print("[PIPELINE] Downloading audio...")
        audio_path = BlogService.download_audio(link)
        print(f"[PIPELINE] Audio saved to: {audio_path}")

        BlogService._update_progress(task_id, 60, "Listening through the audio and converting it to text...")
        print("[PIPELINE] Transcribing with AssemblyAI...")
        transcription = BlogService.transcribe_audio(audio_path)
        if not transcription:
            print("[PIPELINE] ERROR: Transcription failed or empty.")
            BlogService._update_progress(task_id, 100, "Couldn't make out the audio. Please try a different video.", status='FAILED')
            return

        BlogService._update_progress(task_id, 80, "Writing up the article based on what was said...")
        print("[PIPELINE] Synthesizing article with OpenRouter AI...")
        content = BlogService.synthesize_article(transcription)
        if not content:
            print("[PIPELINE] ERROR: AI synthesis failed.")
            BlogService._update_progress(task_id, 100, "Ran into a problem while writing the article. Try again shortly.", status='FAILED')
            return

        BlogService._update_progress(task_id, 95, "Saving your article...")
        blog_post = BlogService.save_blog_post(user, title, link, content)
        print(f"[PIPELINE] SUCCESS: Article created (ID: {blog_post.id})")

        BlogService._update_progress(task_id, 100, "Done! Your article is ready.", status='COMPLETED', blog_post=blog_post)
        print("[PIPELINE] Task completed successfully.\n")
        return blog_post

    except Exception as e:
        # defensive truncation to 500 chars just in case, even though we changed model to TextField
        error_msg = str(e)[:500] 
        BlogService._update_progress(task_id, 100, f"Something went wrong: {error_msg}", status='FAILED')
        print(f"[PIPELINE] CRITICAL ERROR: {str(e)}")
        raise e

class BlogService:
    """
    Core service layer — handles video processing, transcription, and article writing.
    """

    @staticmethod
    def _update_progress(task_id, progress, message, status='RUNNING', blog_post=None):
        if task_id:
            TaskProgress.objects.filter(task_id=task_id).update(
                progress=progress,
                message=message,
                status=status,
                blog_post=blog_post
            )

    @staticmethod
    def get_video_title(link):
        ydl_opts = {
            'quiet': True, 
            'skip_download': True, 
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web_embedded']}},
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, download=False)
                if info:
                    return info.get("title", "Untitled Video")
                return "Untitled Video"
        except Exception:
            return "Untitled Video"

    @staticmethod
    def download_audio(link):
        ydl_opts = {
            'format': 'ba/best',
            'outtmpl': os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'referer': 'https://www.google.com/',
            'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web_embedded']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.splitext(filename)[0] + ".mp3"

    @staticmethod
    def transcribe_audio(audio_file_path):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.nano)
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

        # Safe truncation to avoid token limits
        transcription = transcription[:4000]

        prompt = f"""Based on the transcript below, write a well-structured, informative article.

Requirements:
- Use clear headings (H2, H3) to organise the content
- Write in a professional but approachable tone
- Include bullet points where appropriate
- Do NOT mention that this is based on a transcript or video
- End with a short summary paragraph

Transcript:
{transcription}
"""

        data = {
            "model": "openrouter/auto",
            "messages": [
                {"role": "system", "content": "You are an experienced content writer who turns spoken content into clean, readable articles."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.65,
            "max_tokens": 2000
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=90)
            if response.status_code != 200:
                return None

            content = response.json()["choices"][0]["message"]["content"]
            # Strip any chain-of-thought tags if present
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
