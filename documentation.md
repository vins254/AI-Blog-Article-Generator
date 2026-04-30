# ContentFlow — Technical Documentation
**Live Project**: [https://ai-blog-article-generator-t1ps.onrender.com](https://ai-blog-article-generator-t1ps.onrender.com)

## 1. Project Overview
**ContentFlow** is a high-performance AI-powered blog generator that transforms YouTube videos into professional, well-structured articles. It simplifies content repurposing for creators, allowing them to turn video content into written blog posts in minutes.

---

## 2. How It Works
The application uses an automated asynchronous pipeline to process video content:

1.  **Extraction**: The system uses `yt-dlp` to extract the audio stream from a YouTube URL.
2.  **Transcription**: The audio is sent to **AssemblyAI (Universal-3-Pro)**, which converts the speech into highly accurate text, identifying speakers and timestamps.
3.  **Synthesis**: The raw transcript is sent to an LLM via **OpenRouter**. The AI is instructed to remove verbal fillers, structure the content with meaningful headings, and write in a professional editorial tone.
4.  **Publication**: The final article is rendered in a beautiful, reader-friendly format and saved to your personal editorial archive.
5.  **Management**: Users can delete unwanted articles directly from the archive grid to keep their history clean.

## 3. Key Features
- **Asynchronous Generation**: Processing happens in the background, allowing users to navigate away or start new tasks.
- **Dynamic Theming**: Support for sleek Dark and Light modes.
- **Full Responsiveness**: A mobile-first design with a dedicated slide-out menu for small screens.
- **Article Archive**: A central grid to view, read, and manage previously generated content.
- **Security**: Account-based isolation ensuring users only see their own articles.

---

## 3. Tech Stack
- **Backend**: Django (Python 3.12)
- **Background Tasks**: Django-Q (Handles the heavy processing without blocking the UI)
- **Speech-to-Text**: AssemblyAI
- **Artificial Intelligence**: OpenRouter (LLM Orchestration)
- **Frontend**: Vanilla HTML5, CSS3 (Custom Design System), and JavaScript
- **Media Processing**: yt-dlp & FFmpeg
- **Deployment**: Render (Static files served via WhiteNoise)

---

## 4. Key Features
- **Horizontal Pipeline Tracker**: A real-time visual progress bar with icon-based stage tracking.
- **Responsive Design System**: Custom-built UI with native Light/Dark mode support and glassmorphism aesthetics.
- **Editorial Archive**: Users can save, view, and manage all previously generated articles.
- **Clean Slate Dashboard**: The UI automatically resets on navigation/refresh to ensure a fresh experience for every new article.
- **Automated Demo Mode**: Self-initializing demo credentials for easy onboarding.

---

## 5. Challenges Faced & Solutions

### Challenge A: Dashboard State Persistence
*   **The Issue**: When users returned to the dashboard after viewing an article, the old article would still be visible, creating a confusing experience.
*   **The Fix**: Implemented a "Clean Slate" policy using JavaScript to clear `localStorage` on page load and ensure the input field and output sections are reset upon return.

### Challenge B: Static File Visibility on Deployment
*   **The Issue**: On the Render deployment platform, the CSS styling would often fail to load or show an old version due to complex directory paths and aggressive caching.
*   **The Fix**: 
    1.  Restructured the project by moving the `client/` directory inside the `server/` directory for better path resolution.
    2.  Implemented **WhiteNoise Manifest Storage** in Django, which adds unique hashes to filenames (e.g., `styles.a1b2c3.css`) to force the browser to bypass the cache.

### Challenge C: Status Message Interruption
*   **The Issue**: During the generation process, the rotating status messages (e.g., "Finding video...") would reset every time the frontend polled the server for an update.
*   **The Fix**: Refactored the `updatePipeline` function in JavaScript to only restart timers when the pipeline stage actually changes, ensuring smooth text transitions.

### Challenge D: AI Meta-Commentary in Articles
*   **The Issue**: The AI would occasionally include meta-comments like "In this video transcript..." or "The speaker says...".
*   **The Fix**: Refined the system prompts in `services.py` to explicitly forbid any mention of transcripts or videos, ensuring the output reads as a standalone professional article.

---

## 6. Project Directory Structure
```text
server/
├── ai_blog_app/          # Project configuration & settings
├── blog_generator/       # Main app logic (Models, Views, Services)
├── client/               # UI Assets
│   ├── static/           # CSS, JS, and Images
│   └── templates/        # HTML Templates
├── manage.py
└── requirements.txt
```

---
*Documentation last updated: April 2026*
