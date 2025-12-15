from flask import Flask, Response, send_from_directory, send_file, request, abort
import os
import mutagen
import mutagen.mp3
import mutagen.mp4
import xml.etree.ElementTree as ET
from urllib.parse import quote
import io

app = Flask(__name__)

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/media")
GLOBAL_COVER_PATH = os.environ.get("GLOBAL_COVER_PATH", "/cover/global_cover.jpg")

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ET.register_namespace("itunes", ITUNES_NS)


def get_base_url():
    # Nginx setzt forwarded headers → funktioniert automatisch korrekt
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
    host = request.headers.get("Host", "")
    return f"{scheme}://{host}"


def get_audio_metadata(path):
    audio = mutagen.File(path)
    if audio is None:
        return {"title": os.path.basename(path), "artist": "Unknown", "album": ""}

    title = artist = album = ""

    if isinstance(audio, mutagen.mp3.MP3):
        tags = audio.tags
        if tags:
            title = str(tags.get("TIT2", [""])[0])
            artist = str(tags.get("TPE1", [""])[0])
            album = str(tags.get("TALB", [""])[0])

    elif isinstance(audio, mutagen.mp4.MP4):
        tags = audio.tags or {}
        title = tags.get("\xa9nam", [""])[0]
        artist = tags.get("\xa9ART", [""])[0]
        album = tags.get("\xa9alb", [""])[0]

    title = title or os.path.splitext(os.path.basename(path))[0]
    artist = artist or "Unknown"

    return {"title": title, "artist": artist, "album": album}


def has_embedded_cover(path):
    audio = mutagen.File(path)
    if audio is None:
        return False

    if isinstance(audio, mutagen.mp3.MP3):
        if audio.tags:
            return any(k.startswith("APIC") for k in audio.tags.keys())

    if isinstance(audio, mutagen.mp4.MP4):
        tags = audio.tags or {}
        return "covr" in tags and len(tags["covr"]) > 0

    return False


@app.route("/feed")
def feed():
    base_url = get_base_url()

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Meine Hörbücher"
    ET.SubElement(channel, "description").text = "Automatischer Hörbuch-Podcast"
    ET.SubElement(channel, "link").text = base_url

    # GLOBAL COVER
    if os.path.exists(GLOBAL_COVER_PATH):
        ch_img = ET.SubElement(channel, f"{{{ITUNES_NS}}}image")
        ch_img.set("href", f"{base_url}/global-cover")

    try:
        files = sorted(os.listdir(MEDIA_ROOT))
    except FileNotFoundError:
        files = []

    for name in files:
        full = os.path.join(MEDIA_ROOT, name)

        if not os.path.isfile(full):
            continue

        ext = os.path.splitext(name)[1].lower()
        if ext not in (".mp3", ".m4a", ".m4b"):
            continue

        meta = get_audio_metadata(full)

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = meta["title"]
        ET.SubElement(item, "guid").text = name

        desc = meta["album"] or meta["title"]
        ET.SubElement(item, "description").text = f"{desc} – {meta['artist']}"

        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", f"{base_url}/media/{quote(name)}")
        enclosure.set("type", "audio/mpeg" if ext == ".mp3" else "audio/mp4")

        # Item Cover
        if has_embedded_cover(full):
            itimg = ET.SubElement(item, f"{{{ITUNES_NS}}}image")
            itimg.set("href", f"{base_url}/cover?file={quote(name)}")

    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return Response(xml_bytes, mimetype="application/rss+xml; charset=utf-8")


@app.route("/media/<path:filename>")
def media(filename):
    return send_from_directory(MEDIA_ROOT, filename)


@app.route("/global-cover")
def global_cover():
    if os.path.exists(GLOBAL_COVER_PATH):
        return send_file(GLOBAL_COVER_PATH, mimetype="image/jpeg")
    abort(404)


@app.route("/cover")
def cover():
    file = request.args.get("file")
    if not file:
        abort(404)

    full = os.path.join(MEDIA_ROOT, file)
    if not os.path.exists(full):
        abort(404)

    audio = mutagen.File(full)
    if audio is None:
        return global_cover()

    img = None
    mime = "image/jpeg"

    if isinstance(audio, mutagen.mp3.MP3) and audio.tags:
        for k, v in audio.tags.items():
            if k.startswith("APIC"):
                img = v.data
                mime = v.mime or "image/jpeg"
                break

    elif isinstance(audio, mutagen.mp4.MP4):
        covr = audio.tags.get("covr")
        if covr:
            img = bytes(covr[0])
            if covr[0].imageformat == mutagen.mp4.MP4Cover.FORMAT_PNG:
                mime = "image/png"

    if not img:
        return global_cover()

    return send_file(io.BytesIO(img), mimetype=mime)
