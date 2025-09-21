import os, mimetypes, yaml
from flask import Flask, request, abort, render_template, send_file
from urllib.parse import quote, unquote

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

MEDIA_DIR = "/media"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac')
IMAGE_EXTENSIONS = ('.jpeg', '.jpg', '.png')
PLAYLIST_EXTENSIONS = ('.plst')

def get_parent(path):
    if path == "":
        return None
    return "/" + "/".join(path.strip("/").split("/")[:-1])

@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def serve(req_path):
    req_path = unquote(req_path)  # URL-dekodieren
    abs_path = os.path.join(MEDIA_DIR, req_path)
    parent_path = get_parent(req_path)
    if parent_path is not None:
        parent_path = "/" + parent_path.strip("/")
    dir = "/" + req_path.strip("/")

    if not os.path.exists(abs_path):
        abort(404)

    if os.path.isdir(abs_path):
        entries = []
        imageCount = 0
        for name in sorted(os.listdir(abs_path)):
            entry_path = os.path.join(req_path, name).replace("\\", "/")
            url = "/" + quote(entry_path)
            entry_type = "file"
            if os.path.isdir(os.path.join(abs_path, name)):
                entry_type = "folder"
                entries.append((name, entry_type, url))
            else:
                ext = name.lower()
                if ext.endswith(VIDEO_EXTENSIONS):
                    entry_type = "video"
                    entries.append((name, entry_type, url))
                elif ext.endswith(AUDIO_EXTENSIONS):
                    entry_type = "audio"
                    entries.append((name, entry_type, url))
                elif ext.endswith(IMAGE_EXTENSIONS):
                    entry_type = "image"
                    entries.append((name, entry_type, url))
                    imageCount += 1
                elif ext.endswith(PLAYLIST_EXTENSIONS):
                    entry_type = "playlist"
                    entries.append((name, entry_type, url))
                    #with open(abs_path, "r", encoding="utf-8") as file:
                    #    data = yaml.safe_load(file)
                    #    name = data.get("title", "Unbekannte Playlist")
                    #    for video in data.get("playlist", []):
                    #        entries.append((video['title'], entry_type, video['src']))
                            
        return render_template("folder.html", dir=dir, entries=entries, images=imageCount, parent_dir=parent_path)
    else:
        if not abs_path or not os.path.isfile(abs_path):
            abort(404, "Datei nicht gefunden")

        mime_type, _ = mimetypes.guess_type(abs_path)
        return send_file(abs_path, mimetype=mime_type)

@app.route("/video")
def video():
    href = request.args.get("href")
    mime_type, _ = mimetypes.guess_type(href)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith(('video/')):
        return render_template("video.html", source=href, mime=mime_type)
    else:
        abort(404, "Keine Video-Datei")

@app.route("/audio")
def audio():
    href = request.args.get("href")
    mime_type, _ = mimetypes.guess_type(href)
    mime_type = mime_type or 'application/octet-stream'
    if mime_type.startswith(('audio/')):
        return render_template("audio.html", source=href, mime=mime_type)
    else:
        abort(404, "Keine Audio-Datei")

@app.route("/slideshow")
def slideshow():
    dir_path = request.args.get("dir")
    abs_path = os.path.join(MEDIA_DIR, dir_path.strip("/"))
    if not abs_path or not os.path.isdir(abs_path):
        abort(404, "Verzeichnis nicht gefunden")

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
        abort(400, "Nicht genug Bilder für eine Diashow")

    return render_template("slideshow.html", images=images, dir=dir_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
