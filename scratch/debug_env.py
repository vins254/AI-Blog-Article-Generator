import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
print(f"BASE_DIR: {BASE_DIR}")
env_path = BASE_DIR / '.env'
print(f"ENV_PATH: {env_path} (Exists: {env_path.exists()})")

load_dotenv(dotenv_path=env_path)

print(f"ASSEMBLYAI_API_KEY: {os.getenv('ASSEMBLYAI_API_KEY')}")
print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")
