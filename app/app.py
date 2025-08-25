from flask import Flask, request, render_template_string, send_from_directory, Response
import yt_dlp
import os
import re
import json
import time
from threading import Thread

app = Flask(__name__)
DOWNLOAD_FOLDER = "/music"  # Docker外部ストレージにマウント
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# 単一ユーザー想定の進捗データ
progress_data = {"percent": "0%", "filename": ""}


def sanitize_filename(filename: str) -> str:
    """禁止文字をアンダースコアに置換"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def progress_hook(d):
    """yt-dlpの進捗を更新"""
    if d['status'] == 'downloading':
        progress_data['percent'] = d.get('_percent_str', '0%')
    elif d['status'] == 'finished':
        progress_data['percent'] = '100%'


def download_thread(url):
    """バックグラウンドでダウンロードする関数"""
    progress_data['percent'] = "0%"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, sanitize_filename("%(title)s.%(ext)s")),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "192",
        }],
        "cookiefile": "/app/cookies.txt",
        "progress_hooks": [progress_hook],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        progress_data['filename'] = sanitize_filename(f"{info['title']}.m4a")


HTML_FORM = """
<!doctype html>
<title>YouTube音楽ダウンロード</title>
<h2>YouTube URLを入力してください</h2>
<form method=post>
  <input type=text name=url size=50>
  <input type=submit value=ダウンロード>
</form>

<div id="progress-container" style="width:300px; border:1px solid #aaa; margin-top:10px;">
  <div id="progress-bar" style="width:0%; background:green; color:white; text-align:center;">0%</div>
</div>

<div id="download-link" style="margin-top:10px;"></div>

<script>
const evtSource = new EventSource("/progress");
evtSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.percent) {
    const bar = document.getElementById("progress-bar");
    bar.style.width = data.percent;
    bar.textContent = data.percent;
  }
  if (data.percent === "100%" && data.filename) {
    const linkDiv = document.getElementById("download-link");
    linkDiv.innerHTML = `<p>ダウンロード完了: <a href="/download/${data.filename}">${data.filename}</a></p>`;
  }
};
</script>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            # バックグラウンドでダウンロード開始
            Thread(target=download_thread, args=(url,), daemon=True).start()
    return render_template_string(HTML_FORM)


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)


@app.route("/progress")
def progress():
    """進捗をSSEでフロントに送信"""
    def generate():
        while True:
            yield f"data: {json.dumps(progress_data)}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
