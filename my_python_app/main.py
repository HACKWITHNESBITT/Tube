import os
import re
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL

# Force erase environment proxy markers that could alter socket bindings
for var in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
    if var in os.environ:
        del os.environ[var]

app = FastAPI(title="Watermark Remover AI", version="1.0.0")

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def extract_video_id(user_input: str) -> str:
    """Extracts the clean 11-character YouTube video ID from a URL or raw ID."""
    clean_input = user_input.strip()
    regex = r'(?:v=|\/shorts\/|\/embed\/|\/v\/|youtu\.be\/|\/watch\?v=|^)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, clean_input)
    if match:
        return match.group(1)
    raise ValueError("Invalid URL or Video ID format.")

# --- Frontend User Interface Dashboard (Hyper-Realistic 3D Skeuomorphic) ---
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Watermark Remover Dashboard</title>
        <!-- FIX: Updated script location to the correct functional CDN layer -->
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                background: radial-gradient(circle at center, #0f2d59 0%, #090d16 70%);
            }
            .chassis-3d {
                background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                border-top: 1px solid rgba(255, 255, 255, 0.15);
                border-left: 1px solid rgba(255, 255, 255, 0.08);
                border-right: 1px solid rgba(0, 0, 0, 0.4);
                border-bottom: 8px solid #0f141d;
                box-shadow: 
                    0 40px 80px -15px rgba(0, 0, 0, 0.9),
                    0 20px 40px -20px rgba(0, 0, 0, 0.8),
                    0 0 100px 10px rgba(14, 165, 233, 0.15);
            }
            .trench-3d {
                background-color: #0b0f17;
                box-shadow: 
                    inset 0 6px 10px 0 rgba(0, 0, 0, 0.95),
                    inset 0 1px 3px 0 rgba(0, 0, 0, 0.8),
                    0 1px 1px 0 rgba(255, 255, 255, 0.05);
            }
            .switch-3d {
                background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
                border-top: 1px solid rgba(255, 255, 255, 0.4);
                box-shadow: 
                    0 6px 0 0 #0369a1,
                    0 12px 20px 0 rgba(0, 0, 0, 0.5);
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
                transition: all 0.06s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }
            .switch-3d:hover {
                background: linear-gradient(180deg, #7dd3fc 0%, #0369a1 100%);
            }
            .switch-3d:active {
                transform: translateY(6px);
                box-shadow: 
                    0 0px 0 0 #0369a1,
                    0 3px 6px 0 rgba(0, 0, 0, 0.3);
            }
            .switch-3d:disabled {
                transform: translateY(6px);
                box-shadow: 0 0px 0 0 #0369a1 !important;
                background: linear-gradient(180deg, #0284c7 0%, #075985 100%);
                opacity: 0.8;
            }
        </style>
    </head>
    <body class="text-slate-200 min-h-screen flex items-center justify-center p-6">
        <div class="max-w-xl w-full p-10 rounded-[28px] chassis-3d">
            <div class="flex items-center justify-center space-x-3 mb-8">
                <svg class="h-9 w-9 text-sky-400 filter drop-shadow-[0_2px_4px_rgba(0,0,0,0.5)]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>
                </svg>
                <h1 class="text-3xl font-bold tracking-tight text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.6)]">
                    Watermark Remover
                </h1>
            </div>
            
            <div class="space-y-8">
                <div class="p-1 rounded-2xl bg-gradient-to-b from-slate-700/40 to-slate-900/10">
                    <input type="text" id="videoInput" placeholder="Paste link here..." 
                           class="w-full px-5 py-4 rounded-xl text-center text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-sky-500/50 trench-3d transition-all font-medium text-base">
                </div>
                
                <div class="px-1">
                    <button onclick="triggerDownload()" id="downloadBtn" 
                            class="w-full text-white font-bold text-lg py-4 rounded-xl switch-3d flex items-center justify-center space-x-3 cursor-pointer select-none">
                        <span>Process & Download</span>
                    </button>
                </div>
            </div>

            <div id="statusBox" class="mt-8 p-5 rounded-xl hidden text-sm font-semibold trench-3d text-center border border-slate-900"></div>
        </div>

        <script>
            async function triggerDownload() {
                const videoInput = document.getElementById('videoInput').value;
                const btn = document.getElementById('downloadBtn');
                const statusBox = document.getElementById('statusBox');

                if (!videoInput) {
                    showStatus('Please input a valid URL or ID.', 'text-rose-400 border-t border-rose-950/50');
                    return;
                }

                btn.disabled = true;
                btn.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> <span>Processing Stream...</span>`;
                showStatus('Connecting to source node... Stripping overlays.', 'text-sky-400 border-t border-sky-950/50');

                try {
                    const response = await fetch('/download', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ input_string: videoInput })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showStatus(`✨ <strong>Process Complete!</strong><br><span class="text-slate-400 font-normal mt-1 block">File: ${result.video_title}</span><br><span class="text-xs text-slate-500 block mt-2 font-mono">Location: ${result.saved_at}</span>`, 'text-emerald-400 border-t border-emerald-950/50');
                    } else {
                        showStatus(`❌ System Drop: ${result.detail || 'Processing failed'}`, 'text-rose-400 border-t border-rose-950/50');
                    }
                } catch (err) {
                    showStatus('❌ Connection lost or internal server offline.', 'text-rose-400 border-t border-rose-950/50');
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = '<span>Process & Download</span>';
                }
            }

            function showStatus(text, classes) {
                const statusBox = document.getElementById('statusBox');
                statusBox.className = `mt-8 p-5 rounded-xl text-sm font-semibold trench-3d text-center border border-slate-900 ${classes}`;
                statusBox.innerHTML = text;
                statusBox.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """

class DownloadRequest(BaseModel):
    input_string: str

# --- Core Download Endpoint with Network Fixes ---
@app.post("/download", status_code=200)
def download_youtube_video(payload: DownloadRequest):
    try:
        video_id = extract_video_id(payload.input_string)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    video_url = f"https://youtube.com{video_id}"
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'best',  # Handles unmerged streams dynamically
        'noplaylist': True,
        'source_address': '0.0.0.0',
        'proxy': '',
        'no_check_certificate': True,
        'quiet': True,
        
        # Bypasses standard web socket layout dependency constraints
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
                'skip': ['dash', 'hls']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        }
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
        raise HTTPException(status_code=500, detail=f"Engine error: {str(e)}")
