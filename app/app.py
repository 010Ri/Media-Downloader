from flask import Flask, request, jsonify, render_template
from tasks import download_youtube

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def start_download():
    data = request.get_json()
    url = data.get("url")
    task = download_youtube.apply_async(args=[url])
    return jsonify({'task_id': task.id, 'url': url})

@app.route("/status/<task_id>")
def status(task_id):
    from tasks import celery_app
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PROGRESS':
        meta = task.info
        return jsonify({'state': task.state, 'percent': meta.get('percent', 0)})
    elif task.state == 'SUCCESS':
        return jsonify({'state': task.state, 'filename': task.result})
    else:
        return jsonify({'state': task.state})

@app.route("/download/<filename>")
def download_file(filename):
    from flask import send_from_directory
    return send_from_directory("/music", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
