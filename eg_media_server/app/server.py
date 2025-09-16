import os
import mimetypes
from flask import Flask, request, abort, render_template_string, send_file
from urllib.parse import quote, unquote

app = Flask(__name__)
MEDIA_DIR = "/media"
VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi')
AUDIO_EXTENSIONS = ('.mp3', '.ogg', '.flac')
IMAGE_EXTENSIONS = ('.jpeg', '.jpg', '.png')

# HTML Template für Verzeichnisse
DIR_TEMPLATE = """
<!doctype html>
<title>Media Browser</title>
<h1>Verzeichnis: {{ current_path }}</h1>
{% if parent_path %}
<a href="{{ parent_path }}">⬅ Zurück</a><br><br>
{% endif %}
<ul>
{% for name, type, url in entries %}
    <li>
    {% if type == "folder" %}
        📁 <a href="{{ url }}">{{ name }}</a>
    {% elif type == "video" %}
        🎬 <a href="{{ url }}">{{ name }}</a>
    {% elif type == "audio" %}
        🎵 <a href="{{ url }}">{{ name }}</a>
    {% elif type == "image" %}
        🖼️ <a href="{{ url }}">{{ name }}</a>
    {% else %}
        📄 <a href="{{ url }}">{{ name }}</a>
    {% endif %}
    </li>
{% endfor %}
</ul>
<style>
body { font-family: Arial, sans-serif; }
ul { list-style-type: none; padding-left: 0; }
li { margin: 3px 0; }
</style>
"""

# HTML Template für Datei
FILE_TEMPLATE = """
<!doctype html>
<title>{{ filename }}</title>
<h1>Datei: {{ filename }}</h1>
<a href="{{ parent_path }}">⬅ Zurück</a><br><br>
<pre>{{ content }}</pre>
<style>
body { font-family: monospace; white-space: pre-wrap; }
pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
</style>
"""

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
            entries.append((name, entry_type, url))
        parent_path = get_parent(req_path)
        if parent_path is not None:
            parent_path = "/" + parent_path.strip("/")
        return render_template_string(DIR_TEMPLATE, current_path="/" + req_path.strip("/"), entries=entries, parent_path=parent_path)
    else:
        if not abs_path or not os.path.isfile(abs_path):
            abort(404, "Datei nicht gefunden")

        mime_type, _ = mimetypes.guess_type(abs_path)
        return send_file(abs_path, mimetype=mime_type)

        # Sonst als Download
        #return send_file(file_path, as_attachment=True)
        
        #try:
        #    with open(abs_path, "r", encoding="utf-8") as f:
        #        content = f.read()
        #except:
        #    content = "Kann Datei nicht lesen (Binär oder Berechtigung)"
        #parent_path = get_parent(req_path)
        #if parent_path is not None:
        #    parent_path = "/" + parent_path.strip("/")
        #return render_template_string(FILE_TEMPLATE, filename=req_path, content=content, parent_path=parent_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
