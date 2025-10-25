import os, mimetypes, yaml, posixpath
from flask import Flask, request, abort, render_template, send_file
from urllib.parse import quote, unquote, urlparse, parse_qs

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

DEFAULT_MEDIA_DIR = "/media"

if 'MEDIA_DIR' not in globals():
    MEDIA_DIR = DEFAULT_MEDIA_DIR

IMAGE_EXTENSIONS = ('.jpeg', '.jpg', '.png')
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac')

@app.route("/")
@app.route("/folder")
def folder():
    dir = unquote(request.args.get("path", "/"))
    focus = unquote(request.args.get("focus", ""))
    dir_path = os.path.join(MEDIA_DIR, dir.lstrip('/'))
    if not os.path.isdir(dir_path):
        abort(500, f"Verzeichnis {dir} existiert nicht")
    entries = []
    imageCount = 0
    audioCount = 0
    for file in sorted(os.listdir(dir_path)):
        if file.startswith('.'):
            continue
        file_path = os.path.join(dir_path, file.lstrip('/'))
        url = quote(posixpath.join(dir, file))
        medium = "file"
        if os.path.isdir(file_path):
            medium = "folder"
        else:
            if file.endswith(".yaml"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                medium = data['medium']
                file = data['title']
            elif file.endswith(IMAGE_EXTENSIONS):
                medium = "image"
                imageCount += 1
                if imageCount > 10:
                    continue
            elif file.endswith(VIDEO_EXTENSIONS):
                medium = "video"
            elif file.endswith(AUDIO_EXTENSIONS):
                medium = "audio"
                audioCount += 1
                if audioCount > 10:
                    continue
            else:
                medium = "file"
        entries.append((file, medium, url))
    path = quote(dir)
    return render_template("folder.jinja", title=dir, path=path, entries=entries, imageCount=imageCount, audioCount=audioCount, focus=focus)

@app.route("/file")
def file():
    file = unquote(request.args.get("path", ""))
    file_path = os.path.join(MEDIA_DIR, file.lstrip('/'))
    if (not os.path.isfile(file_path)):
        abort(500, f"Datei {file} existiert nicht")
    mime_type, _ = mimetypes.guess_type(file_path)
    return send_file(file_path, mimetype=mime_type)

@app.route("/slideshow")
def slideshow():
    dir = unquote(request.args.get("path", "/"))
    dir_path = os.path.join(MEDIA_DIR, dir.lstrip('/'))
    if not os.path.isdir(dir_path):
        abort(500, f"Verzeichnis {dir} nicht gefunden")
    images = []
    for file in sorted(os.listdir(dir_path)):
        image_path = os.path.join(dir_path, file)
        if os.path.isfile(image_path):
            ext = file.lower()
            if ext.endswith(IMAGE_EXTENSIONS):
                url = quote(posixpath.join(dir, file))
                images.append((url))
    if len(images) < 1:
        abort(500, "Keine Bilder gefunden")
    return render_template("slideshow.jinja", title=dir, images=images)

@app.route("/album")
def album():
    dir = unquote(request.args.get("path", "/"))
    dir_path = os.path.join(MEDIA_DIR, dir.lstrip('/'))
    if not os.path.isdir(dir_path):
        abort(500, f"Verzeichnis {dir} nicht gefunden")
    audios = []
    cover = None
    for file in sorted(os.listdir(dir_path)):
        if file.startswith(".cover."):
            cover = quote(os.path.join(dir, file))
            continue
        title, ext = os.path.splitext(file)
        file_path = os.path.join(dir_path, file)
        if os.path.isfile(file_path):
            if ext.endswith(AUDIO_EXTENSIONS):
                url = quote(posixpath.join(dir, file))
                audios.append((title, file, url))
    if len(audios) < 1:
        abort(500, "Keine Audios gefunden")
    
    return render_template("album.jinja", title=dir, audios=audios, cover=cover)

@app.route("/image")
def image():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip('/'))
    title = os.path.basename(path)
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('image/'):
        return render_template("image.jinja", title=title, source=quote(path), folder=folder, file=title)
    else:
        abort(500, f"Mime {mime_type} ist keine Bild-Datei")

@app.route("/video")
def video():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip('/'))
    title = os.path.basename(path)
    if path.endswith(".yaml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = data['title']
        path = data['src']
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('video/'):
        return render_template("video.jinja", title=title, source=quote(path), folder=folder, file=title)
    elif mime_type == "application/vnd.apple.mpegurl":
        return render_template("videoHls.jinja", title=title, source=path, folder=folder, file=title)
    else:
        parsedHref = urlparse(path)
        if parsedHref.netloc.endswith("youtube.com"):
            params = parse_qs(parsedHref.query)
            video = params.get('v', [None])
            if (video):
                return render_template("videoYoutube.jinja", title=title, video=video[0], folder=folder, file=title)
        abort(500, f"Ungültiges Video = {path}")

@app.route("/audio")
def audio():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip('/'))
    title = os.path.basename(path)
    if path.endswith(".yaml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = data['title']
        path = data['src']
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('audio/'):
        if path.startswith("http://") or path.startswith("https://"):
            return render_template("audio.jinja", title=title, source=path, folder=folder, file=title)
        return render_template("audio.jinja", title=title, source=quote(path), folder=folder, file=title)
    else:
        abort(500, f"Mime {mime_type} ist keine Audio-Datei")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
