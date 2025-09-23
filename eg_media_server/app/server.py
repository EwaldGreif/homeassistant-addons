import os, mimetypes, yaml
from flask import Flask, request, abort, render_template, send_file
from urllib.parse import quote, unquote, urlparse, parse_qs

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

MEDIA_DIR = "/media"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac')
IMAGE_EXTENSIONS = ('.jpeg', '.jpg', '.png')
PLAYLIST_EXTENSIONS = ('.playlist')

def get_parent(path):
    if path == "":
        return None
    return "/" + "/".join(path.strip("/").split("/")[:-1])

@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def serve(req_path):
    req_path = unquote(req_path)  # URL-dekodieren
    dir_path = os.path.join(MEDIA_DIR, req_path)
    parent_path = get_parent(req_path)
    if parent_path is not None:
        parent_path = "/" + parent_path.strip("/")
    dir = "/" + req_path.strip("/")

    if not os.path.exists(dir_path):
        abort(404)

    entries = []
    if os.path.isdir(dir_path):
        imageCount = 0
        for name in sorted(os.listdir(dir_path)):
            entry_path = os.path.join(req_path, name).replace("\\", "/")
            url = "/" + quote(entry_path)
            entry_type = "file"
            if os.path.isdir(os.path.join(dir_path, name)):
                entry_type = "folder"
            else:
                ext = name.lower()
                if ext.endswith(VIDEO_EXTENSIONS):
                    entry_type = "video"
                elif ext.endswith(AUDIO_EXTENSIONS):
                    entry_type = "audio"
                elif ext.endswith(IMAGE_EXTENSIONS):
                    entry_type = "image"
                    imageCount += 1                            
                elif ext.endswith(PLAYLIST_EXTENSIONS):
                    entry_type = "playlist"
                else:
                    entry_type = "file"
            entries.append((name, entry_type, url))
        return render_template("folder.jinja", dir=dir, entries=entries, images=imageCount, parent_dir=parent_path)
    elif req_path.endswith(PLAYLIST_EXTENSIONS):
        url = "/" + req_path;
        file_path = os.path.join(MEDIA_DIR, req_path)
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
                for video in data.get("playlist", []):
                    entries.append((video['title'], "video", video['src']))
        except Exception as e:
            abort(404, f"Fehler {e}")
        return render_template("playlist.jinja", file=url, entries=entries, parent_dir=parent_path)
    else:
        mime_type, _ = mimetypes.guess_type(dir_path)
        return send_file(dir_path, mimetype=mime_type)

@app.route("/video")
def video():
    href = request.args.get("href")
    title = href
    if len(title) > 50:
        title = title[:25] + "..." + title[-20:]
    mime_type, _ = mimetypes.guess_type(href)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('video/'):
        return render_template("video.jinja", title=title, source=href, mime=mime_type)
    elif mime_type == "application/vnd.apple.mpegurl":
        return render_template("videoHls.jinja", title=title, source=href, mime=mime_type)
    else:
        try:
            parsedHref = urlparse(href)
            if parsedHref.netloc.endsWith("youtube.com"):
                params = parse_qs(parsedHref.query)
                video = params.get('v', [None])
                if (video):
                    return render_template("videoYoutube.jinja", title=title, source=href, video=video[0])
            abort(404, f"Ungültiges href = {href}")
        except Exception as e:
            abort(404, f"Fehler {e}")

@app.route("/audio")
def audio():
    href = request.args.get("href")
    mime_type, _ = mimetypes.guess_type(href)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith('audio/'):
        return render_template("audio.jinja", source=href, mime=mime_type)
    else:
        abort(404, f"Mime {mime_type} ist keine Audio-Datei")

@app.route("/slideshow")
def slideshow():
    dir_path = request.args.get("dir")
    abs_path = os.path.join(MEDIA_DIR, dir_path.strip("/"))
    if not abs_path or not os.path.isdir(abs_path):
        abort(404, f"Verzeichnis {abs_path} nicht gefunden")

    images = []
    for name in sorted(os.listdir(abs_path)):
        image_path = os.path.join(dir_path, name.strip("/"))
        if os.path.isdir(os.path.join(abs_path, name)):
            pass
        else:
            ext = name.lower()
            if ext.endswith(VIDEO_EXTENSIONS):
                pass
            elif ext.endswith(AUDIO_EXTENSIONS):
                pass
            elif ext.endswith(IMAGE_EXTENSIONS):
                images.append((image_path))

    if len(images) < 2:
        abort(400, f"{images} sind nicht genug Bilder für eine Diashow")

    return render_template("slideshow.jinja", images=images, dir=dir_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
