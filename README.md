# 🌊 ContentFlow

> **State-of-the-Art Video Content Automation Suite.**
> Transform YouTube streams into professional, SEO-optimized editorial articles in real-time.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)

---

## 📖 Overview

ContentFlow is a high-performance content engine designed to bridge the gap between video media and written editorial content. It automates the complex pipeline of stream extraction, transcription, and contextual synthesis.

### ✨ Key Features

- 🔄 **Real-Time Streaming Pipeline** — Watch the entire process (Download → Transcribe → Synthesize) live in the UI.
- 📂 **Clean Architecture** — Separated `client/` (Frontend) and `server/` (Backend) structure for better scalability.
- 🎥 **Video-to-Article** — Batch process YouTube content into polished archives.
- 💾 **State Persistence** — Supports page reloads without losing your current input or generated results.
- 🔐 **Hardened Security** — Full CSRF protection, secure authentication, and user-isolated content archives.
- 🎨 **SaaS Interface** — Professional, minimalist design focused on editorial clarity.
- 🧩 **Redundant AI Routing** — Automatically falls back to stable models (via OpenRouter).

---

## 🏗️ Project Structure

The project follows a decoupled structure to ensure it is **scalable** and easy to maintain:

```text
AI_blog_app/
├── client/              # Frontend Assets
│   ├── static/          # CSS, JS, and global assets
│   └── templates/       # Django HTML templates
└── server/              # Backend Logic (Django)
    ├── ai_blog_app/     # Core project settings
    ├── blog_generator/  # Application logic & AI pipeline
    ├── media/           # Local storage for audio extractions
    ├── manage.py        # Project entry point
    └── .env             # Sensitive API keys (Secrets)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-----------|-----------|
| **Backend** | Django 6.0 (Python) |
| **Frontend** | Vanilla JavaScript + HTML5 (State Persistence via LocalStorage) |
| **Logic Engine** | OpenRouter AI (Multi-model Auto-Router) |
| **Transcription** | AssemblyAI (Neural Speech-to-Text) |
| **Extraction** | yt-dlp + FFmpeg |
| **Security** | Django CSRF & Session Auth + Dotenv configuration |

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.12+**
- **FFmpeg** — Required for audio stream processing
- **API Keys:**
  - [AssemblyAI](https://www.assemblyai.com/)
  - [OpenRouter](https://openrouter.ai/)

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vins254/AI-Blog-Article-Generator.git
   cd AI-Blog-Article-Generator
   ```

2. **Setup the Server**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   
   Create a `.env` file in the `server/` directory:
   ```env
   ASSEMBLYAI_API_KEY=your_assemblyai_key
   OPENROUTER_API_KEY=your_openrouter_key
   ```

4. **Initialize Database & Start**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

5. **Access the App**
   Open your browser and navigate to `http://127.0.0.1:8000`.

---

## 🔐 Security & Scalability

- **Security**: All API keys are decoupled from the codebase using `.env` files. Authentication is handled by Django's battle-tested auth system, and all stateful requests require CSRF tokens.
- **Scalability**: The `client/server` split allows you to easily replace the frontend with a modern framework (like React or Next.js) in the future without touching the core AI pipeline.
- **Persistence**: We use `localStorage` to bridge the gap between page reloads, ensuring the "Article Generator" feels like a robust desktop application.

---

## 👤 Author

Developed by **vins254** — [GitHub](https://github.com/vins254)
