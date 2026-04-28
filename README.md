# 🌊 ContentFlow: Video-to-Editorial AI Suite

**Live Demo:** [ai-blog-article-generator-1.onrender.com](https://ai-blog-article-generator-1.onrender.com)  
**Demo Credentials:** `user: demo_admin` | `pass: demo12345`

---

## 📖 Overview
**ContentFlow** is a premium, AI-powered platform designed to transform YouTube video content into professional, well-structured editorial articles. Whether it's a technical tutorial, a live stream, or a quick "Short", ContentFlow extracts the core message and synthesizes it into a high-quality publication ready for blogs or newsletters.

### 🌟 Features
- **🎥 Universal YouTube Support:** Handles standard videos, YouTube Shorts, Live recordings, and mobile links.
- **⚡ Real-Time Pipeline:** Watch the step-by-step progress as the system extracts audio, transcribes speech, and writes the article.
- **🎨 Modern SaaS UI:** A sleek, high-performance interface with glassmorphism effects and micro-animations.
- **🌓 Dual-Theme Engine:** Seamlessly toggle between a "Clean Writing Space" (Light Mode) and a "Deep Focus" (Dark Mode).
- **💾 Session Persistence:** Never lose your work—LocalDB integration saves your current generation progress across page reloads.
- **🔐 Secure & Isolated:** User-specific archives ensure your articles are private and protected.
- **🛠️ Human-Like Feedback:** Background tasks provide natural status updates like *"Listening carefully to what was said..."* instead of technical logs.

---

## 🛠️ Tech Stack

### Backend (The Engine)
- **Django 6.0:** The backbone of the application, providing robust routing, security, and user management.
- **Django-Q:** Handles heavy lifting (AI generation) in background workers to keep the UI snappy.
- **PostgreSQL (Supabase):** Reliable, cloud-hosted relational database for production data.
- **yt-dlp & FFmpeg:** Industrial-grade tools for high-speed media extraction and processing.

### AI Intelligence
- **AssemblyAI (Nano Model):** Cutting-edge Neural Speech-to-Text for ultra-fast and accurate transcription.
- **OpenRouter AI:** An intelligent gateway that routes content to the best-performing large language models for creative synthesis.

### Frontend (The Experience)
- **Vanilla CSS3:** Custom Design System built with CSS variables, Flexbox/Grid, and hardware-accelerated animations.
- **JavaScript (ES6+):** Pure logic for state management, AJAX polling, and real-time DOM updates.
- **Lucide Icons:** Crisp, consistent iconography across the platform.

---

## 🏗️ Architecture
The project is split into a **Decoupled Architecture** to ensure maintainability:

```text
AI_blog_app/
├── client/              # Frontend (Design System & Views)
│   ├── static/          # CSS Design Tokens & Logic Scripts
│   └── templates/       # Semantic HTML5 Layouts
└── server/              # Backend (Core AI Pipeline)
    ├── blog_generator/  # Services, Views, & Task Processing
    ├── ai_blog_app/     # Deployment & Security Settings
    └── media/           # Temporary processing buffer
```

---

## 🚀 Installation

### 1. Prerequisites
- **Python 3.12+**
- **FFmpeg** (installed on system PATH)
- API Keys for **AssemblyAI** and **OpenRouter**

### 2. Setup
```bash
# Clone the repo
git clone https://github.com/vins254/AI-Blog-Article-Generator.git
cd AI-Blog-Article-Generator/server

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate
```

### 3. Environment Config
Create a `.env` file in the `server/` directory:
```env
ASSEMBLYAI_API_KEY=your_key
OPENROUTER_API_KEY=your_key
DATABASE_URL=your_postgres_url
DEBUG=True
```

### 4. Run
Start the web server and the background worker (open two terminals):
```bash
# Terminal 1: Web Server
python manage.py runserver

# Terminal 2: AI Background Worker
python manage.py qcluster
```

---

## 📸 Screenshots

| Dashboard (Dark Mode) | Article Pipeline |
|:---:|:---:|
| ![Dashboard](https://via.placeholder.com/600x400?text=ContentFlow+Dashboard+Dark) | ![Pipeline](https://via.placeholder.com/600x400?text=Live+Generation+Pipeline) |

| Article View | Archive Grid |
|:---:|:---:|
| ![Article](https://via.placeholder.com/600x400?text=Generated+Article+View) | ![Archive](https://via.placeholder.com/600x400?text=My+Articles+Grid) |

---

## 👤 Author
Developed by **vins254** — [GitHub Profile](https://github.com/vins254)
