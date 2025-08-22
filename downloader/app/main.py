from fastapi import FastAPI, Query, Request
from fastapi.responses import Response
import subprocess, os, glob, secrets, base64
from mutagen.mp4 import MP4
import musicbrainzngs

# ----------------------------
# 環境変数でBasic認証設定
# ----------------------------
USERNAME = os.getenv("DOWNLOADER_USER", "admin")
PASSWORD = os.getenv("DOWNLOADER_PASSWORD", "password")

# ----------------------------
# FastAPIアプリケーション
# ----------------------------
app = FastAPI(title="Media Downloader")

# ----------------------------
# Middlewareで全リクエストBasic認証
# ----------------------------
@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    auth = request.headers.get("Authorization")
    if auth is None or not auth.startswith("Basic "):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Media Downloader"'}
        )
    encoded = auth.split(" ")[1]
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        user, pwd = decoded.split(":", 1)
    except Exception:
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Media Downloader"'}
        )
    if not (secrets.compare_digest(user, USERNAME) and secrets.compare_digest(pwd, PASSWORD)):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Media Downloader"'}
        )
    return await call_next(request)

# ----------------------------
# ディレクトリ設定
# ----------------------------
MUSIC_DIR = "/media/music"
VIDEO_DIR = "/media/video"
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# ----------------------------
# MusicBrainz設定
# ----------------------------
musicbrainzngs.set_useragent("YouTubeDownloader", "1.0", "your@email.com")

def set_music_tags(path: str):
    """MusicBrainzで検索してタグを埋め込む"""
    try:
        audio = MP4(path)
        title = audio.tags.get("\xa9nam", [os.path.basename(path)])[0]

        result = musicbrainzngs.search_recordings(recording=title, limit=1)
        if result["recording-list"]:
            rec = result["recording-list"][0]
            artist = rec["artist-credit"][0]["artist"]["name"]
            album = rec["release-list"][0]["title"]

            audio["\xa9ART"] = artist
            audio["\xa9alb"] = album
            audio["\xa9nam"] = title
            audio.save()
            return {"artist": artist, "album": album, "title": title}
        else:
            return {"artist": "Unknown", "album": "Single", "title": title}
    except Exception as e:
        return {"error": str(e), "file": path}

# ----------------------------
# 音楽ダウンロード
# ----------------------------
@app.get("/download/music")
def download_music(url: str = Query(..., description="YouTube URL or playlist")):
    try:
        subprocess.run([
            "yt-dlp", "-f", "bestaudio",
            "--extract-audio", "--audio-format", "m4a", "--audio-quality", "5",
            "-o", f"{MUSIC_DIR}/%(title)s-%(id)s.%(ext)s", url
        ], check=True)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

    files = sorted(glob.glob(f"{MUSIC_DIR}/*.m4a"), key=os.path.getmtime, reverse=True)
    if not files:
        return {"status": "error", "message": "no file downloaded"}

    latest_file = files[0]
    tags = set_music_tags(latest_file)

    return {"status": "done", "file": latest_file, "tags": tags}

# ----------------------------
# 動画ダウンロード
# ----------------------------
@app.get("/download/video")
def download_video(url: str = Query(..., description="YouTube URL or playlist")):
    try:
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/mp4",
            "-o", f"{VIDEO_DIR}/%(title)s-%(id)s.%(ext)s", url
        ], check=True)
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}

    files = sorted(glob.glob(f"{VIDEO_DIR}/*.mp4"), key=os.path.getmtime, reverse=True)
    if not files:
        return {"status": "error", "message": "no file downloaded"}

    latest_file = files[0]
    return {"status": "done", "file": latest_file}
