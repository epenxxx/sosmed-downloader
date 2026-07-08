import os
import glob
import uuid
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "/app/temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_file(filepath: str):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass

@app.get("/api/extract")
async def extract_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL kosong")
        
    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Gunakan link YouTube yang valid.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True,
        'extractor_args': {'youtube': ['player_client=android']},
        'cookiefile': '/app/cookies.txt', 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'YouTube_Video')
            thumbnail = info.get('thumbnail', '')
            safe_url = quote(url, safe="")
            
            downloads = [
                {"type": "video", "name": "Video 1080p", "link": f"/api/download?url={safe_url}&q=1080"},
                {"type": "video", "name": "Video 720p", "link": f"/api/download?url={safe_url}&q=720"},
                {"type": "video", "name": "Video 480p", "link": f"/api/download?url={safe_url}&q=480"},
                {"type": "audio", "name": "Audio MP3 (Super Cepat)", "link": f"/api/download?url={safe_url}&q=mp3"}
            ]

            return {
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "downloads": downloads
            }
            
    except Exception as e:
        print(f"Error Extract: {str(e)}")
        raise HTTPException(status_code=500, detail="Gagal membaca video.")

@app.get("/api/download")
def process_and_download(url: str, q: str, background_tasks: BackgroundTasks):
    file_id = str(uuid.uuid4())[:6]
    
    # Konfigurasi dasar yang dijamin stabil
    ydl_opts = {
        'quiet': False, # Diubah ke False agar log error terlihat di terminal
        'cookiefile': '/app/cookies.txt',
        'extractor_args': {'youtube': ['player_client=android']},
        'restrictfilenames': True, 
        'outtmpl': f'{TEMP_DIR}/{file_id}_%(title)s.%(ext)s',
    }

    if q == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Minta yt-dlp menggabungkan MP4 dengan sendirinya (tanpa parameter iGPU yang rawan crash)
        ydl_opts['format'] = f'bestvideo[height<={q}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Server Mendownload & Memproses File
            info = ydl.extract_info(url, download=True)
            
            # 2. Cari file hasil
            filename = ydl.prepare_filename(info)
            if q == "mp3":
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            # Cek apakah file sukses dibuat oleh FFmpeg
            if not os.path.exists(filename):
                files = glob.glob(f"{TEMP_DIR}/{file_id}_*")
                if files:
                    filename = files[0]
                else:
                    raise Exception("File hilang atau FFmpeg gagal menggabungkan video.")

            # 3. Jadwalkan hapus
            background_tasks.add_task(cleanup_file, filename)
            
            display_name = os.path.basename(filename).replace(f"{file_id}_", "")
            
            # 4. Kirim ke pengguna
            return FileResponse(
                path=filename,
                filename=display_name,
                media_type="audio/mpeg" if q == "mp3" else "video/mp4"
            )
    except Exception as e:
        error_msg = str(e)
        print(f"--- ERROR FATAL DOWNLOAD ---")
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"Gagal: {error_msg}")
