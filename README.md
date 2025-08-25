# Media Downloader
`yt-dlp`を使ってYouTube動画を`mp4`として保存

`http://localhost:5000/`にアクセスしてURLを指定 → ダウンロード

ダウンロードした動画は`video/動画名のハッシュ.m4a`という形で保存されます。

## Techs used
- yt-dlp
- Flask
- Celery
- Redis

## File Structure
```
media-downloader/
├── app/
│   ├── app.py
│   ├── tasks.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── Dockerfile
└── docker-compose.yml
```

## `cookies.txt`
YouTubeの`cookie`を入れてください。

[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)というChrome拡張機能があります。
