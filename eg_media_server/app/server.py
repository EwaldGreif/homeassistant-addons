from flask import Flask, send_from_directory, abort
import os, json

app = Flask(__name__)
MEDIA_DIR = "/media"

@app.route("/")
def list_files():
    files = []
    for root, dirs, filenames in os.walk(MEDIA_DIR):
        for name in filenames:
            rel_path = os.path.relpath(os.path.join(root, name), MEDIA_DIR)
            files.append(rel_path)
    return "<h1>Media-Dateien</h1><ul>" + "".join([f"<li><a href='/file/{f}'>{f}</a></li>" for f in files]) + "</ul>"

@app.route("/file/<path:filename>")
def serve_file(filename):
    try:
        return send_from_directory(MEDIA_DIR, filename, as_attachment=False)
    except FileNotFoundError:
        abort(404)

if __name__ == "__main__":
    # Port aus Optionen laden
    with open("/data/options.json") as f:
        options = json.load(f)
    port = options.get("port", 8000)

    app.run(host="0.0.0.0", port=port)
