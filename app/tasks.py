from celery import Celery
import yt_dlp
import os
import re

# 保存先
DOWNLOAD_FOLDER = "/video"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# Celery 設定
celery_app = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)


def sanitize_filename(s):
    """ファイル名に使えない文字を置換"""
    return re.sub(r'[\\/:*?"<>|]', '_', s)


@celery_app.task(bind=True)
def download_youtube(self, url):
    """YouTube動画を720pでダウンロード（mp4形式）"""
    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded / total * 100)
            self.update_state(state='PROGRESS', meta={'percent': percent})

    ydl_opts = {
        # 映像は720p、音声はbestaudioを結合、出力はmp4
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/mp4",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "cookiefile": "/app/cookies.txt",
        "progress_hooks": [progress_hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        original_file = ydl.prepare_filename(info)

    # ファイル名をサニタイズ
    safe_title = sanitize_filename(info.get("title", "video"))
    final_filename = f"{safe_title}.mp4"
    final_path = os.path.join(DOWNLOAD_FOLDER, final_filename)

    if original_file != final_path:
        os.rename(original_file, final_path)

    return final_filename
