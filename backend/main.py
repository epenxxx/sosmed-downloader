from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Izinkan akses internal dari Nginx
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/extract")
async def extract_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL kosong")

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True,
        # Paksa FFmpeg menggunakan iGPU AMD Radeon Vega
        'postprocessor_args': {
            'ffmpeg': [
                '-hwaccel', 'vaapi',
                '-hwaccel_device', '/dev/dri/renderD128',
                '-hwaccel_output_format', 'vaapi'
            ]
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "success": True,
                "title": info.get('title', 'Video Downloader'),
                "thumbnail": info.get('thumbnail', ''),
                "direct_url": info.get('url', ''),
                "platform": info.get('extractor', 'Unknown')
            }
    except Exception as e:
        print(f"yt-dlp Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Gagal mengekstrak video")
