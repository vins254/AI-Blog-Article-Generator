import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent
print(f"BASE_DIR: {BASE_DIR}")

# decouple logic: it searches for .env in current directory and parent directories
print(f"ASSEMBLYAI_API_KEY: {config('ASSEMBLYAI_API_KEY', default=None)}")
print(f"DEEPSEEK_API_KEY: {config('DEEPSEEK_API_KEY', default=None)}")
