from celery import Celery
import yt_dlp
import os

DOWNLOAD_FOLDER = "/music"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@celery_app.task(bind=True)
def download_youtube(self, url, codec="m4a"):
    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded / total * 100)
            self.update_state(state='PROGRESS', meta={'percent': percent})
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": codec,
            "preferredquality": "192",
        }],
        "cookiefile": "/app/cookies.txt",
        "progress_hooks": [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"{info['title']}.{codec}"
    return filename
