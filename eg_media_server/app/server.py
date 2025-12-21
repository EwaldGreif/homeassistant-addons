import os, mimetypes, yaml, posixpath
from flask import Flask, Blueprint, request, abort, render_template, send_file
from urllib.parse import quote, unquote, urlparse, parse_qs

flask = None

MEDIA_DIR = "/media"
IMAGE_EXTENSIONS = (".jpeg", ".jpg", ".png")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi")
AUDIO_EXTENSIONS = (".mp3")
PLAYLIST_EXTENSIONS = (".playlist")

def init(*, port: int, path: str|None = None):
    global MEDIA_DIR, flask
    if path is not None:
        MEDIA_DIR = path
    template_folder = os.path.join(MEDIA_DIR, ".templates")
    flask = Flask(__name__, template_folder = template_folder)
    flask.jinja_env.trim_blocks = True
    flask.jinja_env.lstrip_blocks = True
    flask.register_blueprint(bp)
    flask.run(host = "0.0.0.0", port = port)

bp = Blueprint("main", __name__)

@bp.route("/")
@bp.route("/folder")
def folder():
    dir = unquote(request.args.get("path", "/"))
    focus = unquote(request.args.get("focus", ""))
    dir_path = os.path.join(MEDIA_DIR, dir.lstrip("/"))
    if not os.path.isdir(dir_path):
        abort(500, f"Verzeichnis {dir} existiert nicht")
    entries = []
    imageCount = 0
    audioCount = 0
    for file in sorted(os.listdir(dir_path)):
        if file.startswith('.'):
            continue
        file_path = os.path.join(dir_path, file.lstrip("/"))
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
                continue;
            elif file.endswith(VIDEO_EXTENSIONS):
                medium = "video"
            elif file.endswith(AUDIO_EXTENSIONS):
                medium = "audio"
                audioCount += 1
                continue
            else:
                medium = "file"
        entries.append((file, medium, url))
    path = quote(dir)
    return render_template("folder.html", title=dir, path=path, entries=entries, imageCount=imageCount, audioCount=audioCount, focus=focus)

@bp.route("/file")
def file():
    file = unquote(request.args.get("path", ""))
    file_path = os.path.join(MEDIA_DIR, file.lstrip("/"))
    if (not os.path.isfile(file_path)):
        abort(500, f"Datei {file} existiert nicht")
    mime_type, _ = mimetypes.guess_type(file_path)
    return send_file(file_path, mimetype=mime_type)

@bp.route("/slideshow")
def slideshow():
    folder = unquote(request.args.get("path", ""))
    folder_path = os.path.join(MEDIA_DIR, folder.lstrip("/"))
    if not os.path.isdir(folder_path):
        abort(500, f"Verzeichnis {folder} nicht gefunden")
    images = []
    for file in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            if file.endswith(IMAGE_EXTENSIONS):
                url = quote(posixpath.join(folder, file))
                images.append((url))
    if len(images) < 1:
        abort(500, "Keine Bilder gefunden")
    return render_template("slideshow.html", title=folder, images=images, folder=folder)

@bp.route("/album")
def album():
    folder = unquote(request.args.get("path", ""))
    folder_path = os.path.join(MEDIA_DIR, folder.lstrip("/"))
    if not os.path.isdir(folder_path):
        abort(500, f"Verzeichnis {folder} nicht gefunden")
    audios = []
    cover = None
    for file in sorted(os.listdir(folder_path)):
        if file.startswith(".cover."):
            cover = quote(os.path.join(folder, file))
            continue
        title, ext = os.path.splitext(file)
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            if ext.endswith(AUDIO_EXTENSIONS):
                url = quote(posixpath.join(folder, file))
                audios.append((title, file, url))
    if len(audios) < 1:
        abort(500, "Keine Audios gefunden")
    return render_template("album.html", title=folder, audios=audios, cover=cover, folder=folder)

@bp.route("/radio")
def radio():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip("/"))
    title = os.path.basename(path)
    if path.endswith(".yaml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = data["title"]
    stations = []
    for sd in data["stations"]:
        name = sd.get("name", "")
        src = sd.get("src", "")
        icon = sd.get("icon", "")
        rpid = sd.get("rpid", "")
        stations.append((name, src, icon, rpid))
    return render_template("radio.html", title=title, stations=stations, folder=folder, file=quote(title))

@bp.route("/image")
def image():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    title = os.path.basename(path)
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith("image/"):
        return render_template("image.html", title=title, source=quote(path), folder=folder, file=quote(title))
    else:
        abort(500, f"Mime {mime_type} ist keine Bild-Datei")

@bp.route("/video")
def video():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip('/'))
    title = os.path.basename(path)
    mime_type = None
    if path.endswith(".yaml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = data['title']
        path = data['src']
        mime_type = data.get('mime', None)
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('video/'):
        return render_template("video.html", title=title, source=quote(path), folder=folder, file=quote(title))
    elif mime_type == "application/vnd.apple.mpegurl":
        return render_template("videoHls.html", title=title, source=path, folder=folder, file=quote(title))
    else:
        parsedHref = urlparse(path)
        if parsedHref.netloc.endswith("youtube.com"):
            params = parse_qs(parsedHref.query)
            video = params.get('v', [None])
            if (video):
                return render_template("videoYoutube.html", title=title, video=video[0], folder=folder, file=quote(title))
        abort(500, f"Ungültiges Video = {path}")

@bp.route("/audio")
def audio():
    path = unquote(request.args.get("path", ""))
    folder = os.path.dirname(path)
    file_path = os.path.join(MEDIA_DIR, path.lstrip('/'))
    title = os.path.basename(path)
    mime_type = None
    if path.endswith(".yaml"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        title = data['title']
        path = data['src']
        mime_type = data.get('mime', None)
    if mime_type is None:
        mime_type, _ = mimetypes.guess_type(path)
        mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('audio/'):
        if path.startswith("http://") or path.startswith("https://"):
            return render_template("audio.html", title=title, source=path, folder=folder, file=quote(title))
        return render_template("audio.html", title=title, source=quote(path), folder=folder, file=quote(title))
    else:
        abort(500, f"Mime {mime_type} ist keine Audio-Datei")

if __name__ == "__main__":
    init(port = 8090, path = "/media")
