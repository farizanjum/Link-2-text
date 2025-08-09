Link2Text – AI Content Generator
================================

<img width="1243" height="785" alt="{985A0B9E-5F62-49E7-9F1A-2F81AA13C41C}" src="https://github.com/user-attachments/assets/6c14705f-8341-483f-8dcb-1003297ce6be" />


Turn tech/AI articles into WhatsApp-ready content with proper formatting, minimal emoji use, and relevant cover images. Choose between ChatGPT (premium) and Mistral (free) models.
Features
--------
- URL processing and direct text input
- AI model selection: ChatGPT (premium) or Mistral (free)
- Optional web search enrichment (references) with Mistral
- Dynamic cover images via OpenGraph + Bing Images fallback
- WhatsApp-friendly formatting with minimal emojis
- One-click copy and share to WhatsApp
- Simple Basic Auth gate on ChatGPT usage

Quick start (local)
-------------------
1) Install dependencies
- Windows (PowerShell)
```
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```
- macOS/Linux
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Set environment variables (in the current shell) and run
- PowerShell
```
$env:OPENAI_API_KEY = "sk-..."
$env:MISTRAL_API_KEY = "mistral-..."
python main.py
```
- Bash
```
export OPENAI_API_KEY="sk-..."
export MISTRAL_API_KEY="mistral-..."
python main.py
```

3) Open the app
- Visit: http://127.0.0.1:5000
- Select model and generate content

ChatGPT login (Basic Auth)
--------------------------
- Username: farizanjum
- Password: 1Don'tknow@@@@@@
- Notes: Only ChatGPT routes require login; Mistral is open by default.

Environment variables
---------------------
- OPENAI_API_KEY (required for ChatGPT)
- MISTRAL_API_KEY (required for Mistral)
- BING_API_KEY (optional; improves image results, otherwise uses a fallback scraper)

API
---
- Base URL: /api
- Endpoint: POST /api/process
- Request bodies:
  - URL mode
    ```json
    { "url": "https://example.com/article", "model": "chatgpt" , "use_web_search": false }
    ```
  - Text mode
    ```json
    { "text": "...", "title": "Optional", "model": "mistral", "use_web_search": false }
    ```
  - Format-only (Mistral)
    ```json
    { "text": "...", "title": "Optional", "format_only": true }
    ```
- Headers (ChatGPT only):
  - Authorization: Basic base64(farizanjum:1Don'tknow@@@@@@)
- Response:
  ```json
  {
    "formatted_content": "...",
    "image_urls": ["..."],
    "title": "...",
    "keywords": ["..."],
    "source_url": "..."
  }
  ```

Deployment
----------
Backend (Render/Railway/VM)
- Start command: gunicorn main:app
- Env vars: OPENAI_API_KEY, MISTRAL_API_KEY, optional BING_API_KEY
- Ensure outbound internet is allowed

Frontend (Netlify)
- Publish directory: Static
- No build command required
- Configure API proxy:
  - netlify.toml and Static/_redirects contain placeholder https://YOUR-BACKEND-DOMAIN
  - Replace with your backend URL, e.g., https://link2text-api.onrender.com
- SPA fallback is already configured

Project structure
-----------------
```
Link-2-text/
├─ main.py                 # Flask app, serves Static/ and /api
├─ Routes/
│  ├─ __init__.py
│  ├─ api.py               # API routes, ChatGPT auth gate
│  ├─ web_search.py        # Web search helpers for enrichment
│  └─ bing_search.py       # Image search + fallback
├─ Static/
│  ├─ index.html           # Frontend UI (Bootstrap + jQuery)
│  └─ _redirects           # Netlify redirects/proxy rules
├─ requirements.txt        # Python deps (incl. lxml_html_clean)
├─ netlify.toml            # Netlify config (publish + proxy + SPA)
└─ README.md
```

Notes
-----
- newspaper3k requires lxml_html_clean; included in requirements.txt.
- NLTK downloads punkt and stopwords on first run.
- CORS is enabled for /api/* to allow frontend hosting on Netlify.

License
-------
MIT


