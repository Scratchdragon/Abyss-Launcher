import os
import subprocess
import sys
import threading
import glob

from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMessageBox

from datetime import datetime

from py.shortcuts import *
from py.app_overlay import *


def debug():
    print("debug")


app_process = subprocess.Popen("uname -a".split(" "))
app_stop = Value("i", 0)


def queue_app_stop():
    app_stop.value = 1


def stop_current_app():
    kill_app(app_process)


def kill_app(process):
    logger.log("Killing app process " + str(process.pid))
    process.kill()


def show_overlay():
    manual_show.value = 1


def send_overlay_keyevent(key):
    events = {
        "w": 1,
        "Key.up": 1,
        "s": 2,
        "Key.down": 2,
        "a": 3,
        "Key.left": 3,
        "d": 4,
        "Key.right": 4,
        "Key.enter": 5,
        "Key.space": 5
    }
    if key in events:
        event.value = events[key]


# Register all keyboard shortcuts
register_shortcut("Key.f4", stop_current_app)
register_shortcut("Key.cmd", show_overlay)
start_listener(send_overlay_keyevent)

ignore_icons = True


class Logger:
    file = None

    def write(self, msg):
        print(msg)
        self.file.write(msg + "\n")

    def log(self, msg):
        print("[-] " + msg)
        self.file.write("[-] " + msg + "\n")

    def warn(self, msg):
        print("[!] " + msg)
        self.file.write("[!] " + msg + "\n")

    def error(self, msg):
        print("[E] " + msg)
        self.file.write("[E] " + msg + "\n")

    def note(self, msg):
        print("[*] " + msg)
        self.file.write("[*] " + msg + "\n")

    def __init__(self, outfile):
        if os.path.exists(outfile + ".0.log"):
            os.system("mv " + outfile + ".0.log " + outfile + ".1.log")

        now = datetime.now()
        time = now.strftime("%H:%M:%S")

        self.file = open(outfile + ".0.log", "a")
        self.write("Abyss Launcher Log (" + time + ")")
        self.write("\t[-] Info")
        self.write("\t[*] Note")
        self.write("\t[!] Warning")
        self.write("\t[E] Error")

    def close(self):
        now = datetime.now()
        time = now.strftime("%H:%M:%S")

        self.file.write("Log closed at (" + time + ")\n")
        self.file.close()
        print("Log closed at (" + time + ")")


logger = Logger("Launcher")
in_app = False


class Object(object):
    pass


def parse_desktop_file(file):
    obj = Object()
    for line in file.split("\n"):
        attrib = line.split("=")
        if len(attrib) == 2:
            setattr(obj, attrib[0], attrib[1])
    return obj


def get_desktop_entries():
    locations = ["/usr/share/applications", "/usr/local/share/applications/",
                 os.getenv("HOME") + "/.local/share/applications/"]
    entries = []
    logger.note("Loading desktop entries")
    for location in locations:
        logger.write("\tIndexing directory '" + location + "'")
        if not os.path.exists(location):
            logger.write("\tDirectory does not exist, skipping")
        else:
            for entry in os.listdir(location):
                if entry.endswith(".desktop"):
                    file = open(location + "/" + entry)
                    obj = parse_desktop_file(file.read())
                    file.close()
                    entries.append(obj)
                    logger.write("\t\tLoaded '" + entry + "' (" + obj.Name + ")")
                else:
                    logger.write("\t\tSkipped '" + entry + "' (Not .desktop)")
    logger.note("Finished loading desktop entries")
    return entries


desktop_entries = get_desktop_entries()

icons_ready = ignore_icons


def full_icon_path(icon):
    try:
        if icon.startswith("/"):
            return icon
        locations = ["/usr/share/icons/hicolor", "/usr/share/icons", os.getenv("HOME") + "/.local/share/icons",
                     "/usr/share/pixmaps", "/usr/local/share/pixmaps"]

        for location in locations:
            icons = (glob.glob(location + "/**/" + icon + "*", recursive=True))
            if len(icons) > 0:
                return icons[0]
        return "images/icon.png"
    except Exception as e:
        return "images/icon.png"


def loadIcons():
    logger.note("Expanding Icon paths")
    for entry in desktop_entries:
        if hasattr(entry, "Icon"):
            entry.Icon = full_icon_path(entry.Icon)
            logger.write("\tExpanded '" + entry.Name + "'")
        else:
            logger.write("\tEntry '" + entry.Name + "' does not have an icon, skipping")
    global icons_ready
    icons_ready = True


if not ignore_icons:
    asset_thread = threading.Thread(name="Asset loader", target=loadIcons)
    asset_thread.start()


def close():
    try:
        asset_thread.join()
    except Exception as e:
        logger.error(str(e))
    logger.log("Closing listener")
    stop_listener()
    logger.log("Closing overlay")
    stop_overlay()
    logger.close()


def desktop_entries_by_category(category):
    ret = []
    for entry in desktop_entries:
        if entry.Type == "Application":
            if category == "All":
                ret.append(entry)
            elif hasattr(entry, "Categories") and category in entry.Categories.split(";"):
                ret.append(entry)
    return ret


def getDesktopEntryAttribute(name, key):
    try:
        for entry in desktop_entries:
            if hasattr(entry, "Name") and entry.Name == name:
                if hasattr(entry, key):
                    return getattr(entry, key)
                else:
                    return None
    except Exception as e:
        logger.error("Error occurred when getting attribute '" + key + "' for desktop app '" + name + "':")
        logger.write("\t" + str(e))
    return None


def launch(appname, run):
    global in_app
    in_app = True

    logger.log("> " + run)
    global app_process
    logger.log("Starting application '" + appname + "'")
    try:
        app_process = subprocess.Popen(run.split(" "))
    except Exception as e:
        logger.error(str(e))
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Command Error")
        msg.setText("Error running application '" + appname + "':\n" + str(e))
        msg.exec_()


def restart():
    logger.note("Restarting")
    close()
    os.system("reboot")


def shutdown():
    logger.note("Shutting down")
    close()
    os.system("shutdown now")


class WebApp(QWebEngineView):
    path = None

    def __init__(self):
        super().__init__()

        self.path = "file:///" + os.path.dirname(os.path.abspath(__file__))

        # Load page
        logger.note("Loading '" + self.path + "/src/launcher.html" + "'")
        self.page().setUrl(QUrl(self.path + "/src/launcher.html"))

        # setup channel
        self.channel = QWebChannel()
        self.channel.registerObject('backend', self)
        self.page().setWebChannel(self.channel)

    @pyqtSlot(str, int)
    def log(self, msg, weight=0):
        log_func = [
            logger.write,
            logger.log,
            logger.note,
            logger.warn,
            logger.error
        ]
        log_func[weight](msg)

    @pyqtSlot(str, str)
    def launch(self, appname, comm):
        launch(appname, comm)

    @pyqtSlot()
    def restart(self):
        restart()

    @pyqtSlot()
    def shutdown(self):
        shutdown()

    @pyqtSlot(result=bool)
    def in_app(self):
        global in_app
        in_app = app_process.poll() is None
        return in_app

    @pyqtSlot(result=bool)
    def icons_ready(self):
        return icons_ready

    @pyqtSlot(str, result=list)
    def getDesktopEntriesByCategory(self, category):
        entries = desktop_entries_by_category(category)
        ret = list()
        for entry in entries:
            ret.append(entry.Name)
        return ret

    @pyqtSlot(str)
    def launchDesktopApp(self, name):
        logger.log("Opening app '" + name + "' from desktop file")
        try:
            path = getDesktopEntryAttribute(name, "Path")
            comm = ""
            if path is not None:
                logger.write("\tPath: " + path)
                comm = "cd " + path + "; "
            comm += getDesktopEntryAttribute(name, "Exec")
            logger.write("\tExec: " + comm)
            launch(name, comm)
        except Exception as e:
            logger.error("Error occurred when opening app '" + name + "' using from desktop file:")
            logger.write("\t" + str(e))

    @pyqtSlot(str, result=str)
    def getDesktopEntryAttribute(self, name, key):
        return getDesktopEntryAttribute(name, key)

    @pyqtSlot(str, result=str)
    def getDesktopIconPath(self, name):
        return getDesktopEntryAttribute(name, "Icon")

    @pyqtSlot()
    def pollRequests(self):
        if app_stop.value == 1:
            app_stop.value = 0
            stop_current_app()

    @pyqtSlot(str, result=str)
    def getFile(self, path):
        fullpath = "src/" + path
        if path.startswith("/"):
            fullpath = path
        logger.log("getFile request for '" + fullpath + "'")
        try:
            f = open(fullpath)
            file = f.read()
            f.close()
            logger.note("File request succeeded")
            return file
        except Exception as e:
            logger.warn("File request failed")
            return ""


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
    view = WebApp()

    logger.log("Getting screen size")
    cmd = "xdpyinfo  | grep -oP 'dimensions:\\s+\\K\\S+'"
    logger.log("> " + cmd)
    size = os.popen(cmd).readlines()[0]
    logger.note("Size: " + size.strip("\n"))
    width = int(size.split("x")[0])
    height = int(size.split("x")[1])

    logger.log("Initializing in-app overlay")
    start_overlay(width, height, shutdown, restart, queue_app_stop)

    logger.log("Starting launcher")
    view.setGeometry(0, 0, width, height)
    view.show()
    app.exec_()
    close()
