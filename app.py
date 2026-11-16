import shared
from flask import *
import os
app = Flask(__name__)
@app.route("/")
def home():
    return render_template("index.html")
def build_tree(path):
    tree = {}
    for item in os.listdir(path):
        full = os.path.join(path, item)
        if os.path.isdir(full):
            tree[item] = build_tree(full)
        else:
            with open(full, "r", encoding="utf-8") as f:
                tree[item] = f.read()
    return tree
@app.route("/Open_Folder")
def open_folder():
    shared.selected_folder = None
    shared.folder_event.clear()
    shared.bridge.chooseFolder.emit()
    shared.folder_event.wait()
    if not shared.selected_folder:
        return jsonify(None)
    return jsonify({
        "Main Root": build_tree(shared.selected_folder)
    })