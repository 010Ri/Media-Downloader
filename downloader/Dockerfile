FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && \
    pip install fastapi uvicorn yt-dlp mutagen musicbrainzngs && \
    rm -rf /var/lib/apt/lists/*

COPY app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
