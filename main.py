import sys
import os
import threading
import time
import shared
from app import *
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QUrl
def openFolderDialog():
    folder = QFileDialog.getExistingDirectory(window,"Select Folder")
    shared.selected_folder = folder
    shared.folder_event.set()
def run_flask():
    app.run(host="127.0.0.1",port=5000,debug=False,use_reloader=False)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prog Block")
        storage_dir = os.path.join(os.getcwd(), "Storage")
        os.makedirs(storage_dir, exist_ok=True)
        profile = QWebEngineProfile("MyApp", self)
        profile.setPersistentStoragePath(storage_dir)
        page = QWebEnginePage(profile, self)
        self.view = QWebEngineView()
        self.view.setPage(page)
        self.setCentralWidget(self.view)
        self.view.load(QUrl("http://127.0.0.1:5000"))
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
shared.bridge.chooseFolder.connect(openFolderDialog)
time.sleep(1)
qt_app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(qt_app.exec())