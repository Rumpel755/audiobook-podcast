# Audiobook Podcast Server

Turn a folder of audiobooks into a private podcast feed.

This project exposes a directory of audio files (MP3, M4A, M4B) as a
standards-compliant RSS podcast feed, including:

- Automatic feed generation
- One audiobook = one podcast episode
- Embedded cover support (MP3/M4A/M4B)
- Global fallback podcast cover
- Works with AntennaPod, gPodder, Cardo, Podcast Addict, etc.
- Designed for self-hosting with Docker

---

## Features

- 📂 Folder → Podcast feed
- 🎧 MP3, M4A, M4B support
- 🖼 Embedded cover extraction
- 🎨 Global podcast cover fallback
- 🔁 Feed updates automatically when files change
- 🐳 Docker & Docker Compose ready
- 🔒 Can be placed behind a reverse proxy (Nginx Proxy Manager, Traefik)

---

## Docker Image

Available on Docker Hub:docker pull rumpel755/audiobook-podcast


---

## Example docker-compose.yml
```yaml
services:
  audiobook_podcast:
    image: rumpel755/audiobook-podcast:latest
    container_name: audiobook-podcast
    restart: unless-stopped
    ports:
      - "8095:8095"
    environment:
      MEDIA_ROOT: /media
      GLOBAL_COVER_PATH: /cover/global_cover.jpg
      PORT: "8095"
    volumes:
      - /mnt/user/data/media/audiobooks:/media:ro
      - /mnt/user/appdata/audiobook-podcast/global_cover.jpg:/cover/global_cover.jpg:ro

--- 

## Feed URL
http://SERVER-IP:8095/feed


or behind a reverse proxy:

https://your-domain.example/feed

## Supported Podcast Apps

AntennaPod

gPodder

Cardo

Podcast Addict

Any RSS-compatible podcast player

License
MIT
