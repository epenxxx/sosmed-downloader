from fastapi import FastAPI, HTTPException
import yt_dlp

app = FastAPI()

@app.get("/extract")
async def extract_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL kosong")

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'dump_single_json': True,
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
        print(e)
        raise HTTPException(status_code=500, detail="Gagal mengekstrak video")
