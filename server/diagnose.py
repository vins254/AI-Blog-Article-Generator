import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_blog_app.settings')
django.setup()

from django.conf import settings
from blog_generator.models import BlogPost, TaskProgress
from django.contrib.auth.models import User
import yt_dlp
import subprocess

def check_env():
    print("--- Environment Check ---")
    print(f"DATABASE_URL: {'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}")
    print(f"ASSEMBLYAI_API_KEY: {'SET' if settings.ASSEMBLYAI_API_KEY else 'NOT SET'}")
    print(f"OPENROUTER_API_KEY: {'SET' if settings.OPENROUTER_API_KEY else 'NOT SET'}")
    
    try:
        from django.db import connection
        tables = connection.introspection.table_names()
        print(f"Database tables found: {len(tables)}")
        if 'blog_generator_taskprogress' in tables:
            print("SUCCESS: 'blog_generator_taskprogress' table exists.")
        else:
            print("ERROR: 'blog_generator_taskprogress' table MISSING.")
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")

    try:
        res = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        print(f"FFmpeg check: SUCCESS ({res.stdout.splitlines()[0]})")
    except Exception:
        print("ERROR: FFmpeg NOT FOUND in PATH.")

    print(f"yt-dlp version: {yt_dlp.version.__version__}")

if __name__ == "__main__":
    check_env()
