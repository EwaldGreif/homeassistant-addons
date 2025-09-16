import os
import mimetypes
from flask import Flask, request, abort, render_template, send_file
from urllib.parse import quote, unquote

app = Flask(__name__)
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

MEDIA_DIR = "/media"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac')
IMAGE_EXTENSIONS = ('.jpeg', '.jpg', '.png')

def get_parent(path):
    if path == "":
        return None
    return "/" + "/".join(path.strip("/").split("/")[:-1])

@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def serve(req_path):
    req_path = unquote(req_path)  # URL-dekodieren
    abs_path = os.path.join(MEDIA_DIR, req_path)

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
            else:
                ext = name.lower()
                if ext.endswith(VIDEO_EXTENSIONS):
                    entry_type = "video"
                elif ext.endswith(AUDIO_EXTENSIONS):
                    entry_type = "audio"
                elif ext.endswith(IMAGE_EXTENSIONS):
                    entry_type = "image"
                    imageCount += 1
            entries.append((name, entry_type, url))
        parent_path = get_parent(req_path)
        if parent_path is not None:
            parent_path = "/" + parent_path.strip("/")
        return render_template("folder.html", dir="/" + req_path.strip("/"), entries=entries, images=imageCount, parent_dir=parent_path)
    else:
        if not abs_path or not os.path.isfile(abs_path):
            abort(404, "Datei nicht gefunden")

        mime_type, _ = mimetypes.guess_type(abs_path)
        return send_file(abs_path, mimetype=mime_type)

@app.route("/play")
def play():
    file_path = request.args.get("file")
    abs_path = os.path.join(MEDIA_DIR, file_path.strip("/"))
    if not abs_path or not os.path.isfile(abs_path):
        abort(404, "Datei nicht gefunden")

    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or 'application/octet-stream'
    
    # Nur Video/Audio anzeigen, sonst als Download
    if mime_type.startswith(('video/','audio/')):
        return render_template("player.html", file=file_path, mime=mime_type)
    else:
        return send_file(abs_path, as_attachment=True)

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
