from flask import Flask, request, render_template_string, send_from_directory
import yt_dlp
import os

app = Flask(__name__)
DOWNLOAD_FOLDER = "/music"  # Docker外部ストレージにマウント
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML_FORM = """
<!doctype html>
<title>YouTube音楽ダウンロード</title>
<h2>YouTube URLを入力してください</h2>
<form method=post>
  <input type=text name=url size=50>
  <input type=submit value=ダウンロード>
</form>
{% if filename %}
<p>ダウンロード完了: <a href="/download/{{ filename }}">{{ filename }}</a></p>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    filename = None
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }],
                "cookiefile": "/app/cookies.txt",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = f"{info['title']}.m4a"
    return render_template_string(HTML_FORM, filename=filename)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
