import os
import subprocess
import sys
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, "Found"
    except FileNotFoundError:
        return False, "Not Found (Critical for audio processing)"

def check_env_vars():
    keys = ["ASSEMBLYAI_API_KEY", "OPENROUTER_API_KEY", "DATABASE_URL"]
    results = {}
    for key in keys:
        val = os.environ.get(key)
        results[key] = "Set" if val else "MISSING"
    return results

if __name__ == "__main__":
    print("\n--- CONTENTFLOW DIAGNOSTIC ---")
    
    ff_ok, ff_msg = check_ffmpeg()
    print(f"FFmpeg: {ff_msg}")
    
    envs = check_env_vars()
    for k, v in envs.items():
        print(f"{k}: {v}")
    
    print("\nCheck if 'python manage.py qcluster' is running in a separate terminal.")
    print("------------------------------\n")
