import os
import re
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL

# Network Fix: Force clear any phantom environment proxies that might confuse Miniforge/Python
for var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    if var in os.environ:
        del os.environ[var]

app = FastAPI(title="VectorShell Video Downloader", version="1.0.0")

# Setup safe local download path
DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_video_id(user_input: str) -> str:
    """Extracts the clean 11-character YouTube video ID from a URL or raw ID."""
    clean_input = user_input.strip()
    regex = r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/watch\?v=|^)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, clean_input)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL or Video ID format.")

# --- Frontend User Interface Dashboard ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VectorShell Downloader</title>
        <script src="https://tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center p-4">
        <div class="max-w-md w-full bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700">
            <h1 class="text-2xl font-bold text-center mb-2 text-indigo-400">⚡ VectorShell Tube</h1>
            <p class="text-sm text-slate-400 text-center mb-6">Paste any YouTube URL or Video ID below to download</p>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">YouTube Link / ID</label>
                    <input type="text" id="videoInput" placeholder="e.g., https://youtube.com" 
                           class="w-full px-4 py-3 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors">
                </div>
                
                <button onclick="triggerDownload()" id="downloadBtn" 
                        class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-lg transition-all flex items-center justify-center space-x-2">
                    <span>Download to Machine</span>
                </button>
            </div>

            <!-- Status Notifications -->
            <div id="statusBox" class="mt-6 p-4 rounded-lg hidden text-sm"></div>
        </div>

        <script>
            async function triggerDownload() {
                const videoInput = document.getElementById('videoInput').value;
                const btn = document.getElementById('downloadBtn');
                const statusBox = document.getElementById('statusBox');

                if (!videoInput) {
                    showStatus('Please input a valid YouTube URL or ID.', 'bg-red-900/50 border border-red-500 text-red-200');
                    return;
                }

                // UI Loading State
                btn.disabled = true;
                btn.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> <span>Processing...</span>`;
                showStatus('Connecting to YouTube... This may take a moment.', 'bg-indigo-950 border border-indigo-700 text-indigo-200');

                try {
                    const response = await fetch('/download', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ input_string: videoInput })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showStatus(`✨ <strong>Success!</strong><br>Downloaded: ${result.video_title}<br><span class="text-xs text-slate-400">Saved to: ${result.saved_at}</span>`, 'bg-emerald-900/50 border border-emerald-500 text-emerald-200');
                    } else {
                        showStatus(`❌ Error: ${result.detail || 'Failed to download'}`, 'bg-red-900/50 border border-red-500 text-red-200');
                    }
                } catch (err) {
                    showStatus('❌ Network error or server offline.', 'bg-red-900/50 border border-red-500 text-red-200');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<span>Download to Machine</span>';
                }
            }

            function showStatus(text, classes) {
                const statusBox = document.getElementById('statusBox');
                statusBox.className = `mt-6 p-4 rounded-lg text-sm ${classes}`;
                statusBox.innerHTML = text;
                statusBox.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """

# --- API Endpoint Schemas ---
class DownloadRequest(BaseModel):
    input_string: str

# --- Core Download Endpoint ---
@app.post("/download", status_code=200)
def download_youtube_video(payload: DownloadRequest):
    try:
        video_id = extract_video_id(payload.input_string)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    video_url = f"https://youtube.com{video_id}"
    
    # Configuration built with strict IPv4 bindings to prevent resolution drops
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'source_address': '0.0.0.0',  # Network Fix: Force traffic exclusively over IPv4
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
        return {
            "status": "success",
            "video_title": info.get("title"),
            "saved_at": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"yt-dlp error: {str(e)}")
