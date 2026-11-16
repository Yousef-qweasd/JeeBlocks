from PyQt6.QtCore import QObject, pyqtSignal
from threading import *
class Bridge(QObject):
    chooseFolder = pyqtSignal()
bridge = Bridge()
selected_folder = None
folder_event = Event()