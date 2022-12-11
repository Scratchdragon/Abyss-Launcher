import os
import subprocess
import sys
import threading
import glob

from PyQt5.QtCore import pyqtSlot, QUrl
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication, QMessageBox

from py.shortcuts import *
from py.app_overlay import *
from py.logger import Logger

# Debug flags
debug_flags = {
    "load_icons": False
}

# Log/system methods and variables

logger = Logger("Launcher")  # Initialize the main logger
if len(sys.argv) == 1:
    user = "root"
else:
    user = sys.argv[1]
logger.log("Running under user '" + user + "'")


def system(cmd):
    logger.log("> " + cmd)
    return os.popen(cmd).readlines()


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


def restart():
    logger.note("Restarting")
    close()
    system("reboot")


def shutdown():
    logger.note("Shutting down")
    close()
    system("shutdown now")


xid = ""  # The id of the launcher from xprop


# Application managing methods and variables

class AppManager:
    app_process = subprocess.Popen("uname -a".split(" "))
    force_out_app = Value("i", 0)
    in_app = False

    @staticmethod
    def app_active():
        AppManager.in_app = AppManager.app_process.poll() is None
        if (not AppManager.in_app) and (AppManager.force_out_app.value == 1):
            logger.log("Terminating process")
            AppManager.app_process.terminate()
            AppManager.force_out_app.value = 0
            AppManager.in_app = False
        return AppManager.in_app

    @staticmethod
    def kill_app():
        logger.log("Killing active app process")
        kill_id = system("xprop -root _NET_ACTIVE_WINDOW | cut -d\\# -f2")[0]
        if not kill_id == xid:
            system("xkill -id " + kill_id)
        else:
            logger.log("Kill id equals launcher id, cannot kill")
            AppManager.force_out_app.value = 1

    @staticmethod
    def launch(appname, run):
        AppManager.in_app = True

        bash = "sudo -H -u " + user + " bash -c"
        comm = bash.split(" ")
        comm.append(run)
        logger.log("> " + str(comm))
        logger.log("Starting application '" + appname + "'")
        try:
            AppManager.app_process = subprocess.Popen(comm)
        except Exception as e:
            logger.error(str(e))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Command Error")
            msg.setText("Error running application '" + appname + "':\n" + str(e))
            msg.exec_()


# Register all keyboard shortcuts
register_shortcut("Key.f4", AppManager.kill_app)
register_shortcut("Key.cmd", show_overlay)
start_listener(handle_overlay_input)


# Secondary object class allows attributes to be assigned in after declaration
class Object(object):
    pass


# Desktop file management methods
def parse_desktop_file(file):  # Creates an Object from a desktop file
    obj = Object()
    for line in file.split("\n"):
        attrib = line.split("=")
        if len(attrib) == 2:
            setattr(obj, attrib[0], attrib[1])
    return obj


def get_desktop_entries():  # Gets a list of all desktop files and puts them into a list of objects
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


def full_icon_path(icon):  # Locate the absolute path for any icons
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


def loadIcons():  # Expand all icon paths to avoid stuttering in the app
    logger.note("Expanding Icon paths")
    for entry in desktop_entries:
        if hasattr(entry, "Icon"):
            entry.Icon = full_icon_path(entry.Icon)
            logger.write("\tExpanded '" + entry.Name + "'")
        else:
            logger.write("\tEntry '" + entry.Name + "' does not have an icon, skipping")
    global icons_ready
    icons_ready = True


desktop_entries = get_desktop_entries()
icons_ready = not debug_flags["load_icons"]
if debug_flags["load_icons"]:  # Load full icon paths in another thread so that a loading screen can be displayed instead of the program just freezing on start
    asset_thread = threading.Thread(name="Asset loader", target=loadIcons)
    asset_thread.start()


def desktop_entries_by_category(category):  # Get desktop entries in a category on the backend to reduce load times in javascript
    ret = []
    for entry in desktop_entries:
        if entry.Type == "Application":
            if category == "All":
                ret.append(entry)
            elif hasattr(entry, "Categories") and category in entry.Categories.split(";"):
                ret.append(entry)
    return ret


def get_desktop_entry_attr(name, key):  # An error safe method of getting an attribute from a desktop file object
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

    @pyqtSlot()
    def onLoad(self):  # Method is run once the web page connects to the QWebChannel
        global xid  # Safe to assume that the launcher is the focussed task at this point
        xid = system("xprop -root _NET_ACTIVE_WINDOW | cut -d\\# -f2")[0]  # Gets the id of the active window (should be the launcher)
        logger.log("XID is " + xid)

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
        AppManager.launch(appname, comm)

    @pyqtSlot()
    def restart(self):
        restart()

    @pyqtSlot()
    def shutdown(self):
        shutdown()

    @pyqtSlot(result=bool)
    def in_app(self):
        return AppManager.app_active()

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
            path = get_desktop_entry_attr(name, "Path")
            comm = ""
            if path is not None:
                logger.write("\tPath: " + path)
                comm = "cd " + path + "; "
            comm += get_desktop_entry_attr(name, "Exec")
            logger.write("\tExec: " + comm)
            AppManager.launch(name, comm)
        except Exception as e:
            logger.error("Error occurred when opening app '" + name + "' using from desktop file:")
            logger.write("\t" + str(e))

    @pyqtSlot(str, result=str)
    def getDesktopEntryAttribute(self, name, key):
        return get_desktop_entry_attr(name, key)

    @pyqtSlot(str, result=str)
    def getDesktopIconPath(self, name):
        return get_desktop_entry_attr(name, "Icon")

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
    # Init the application and the web view
    app = QApplication.instance() or QApplication(sys.argv)
    view = WebApp()

    # Get screen size manually instead of just running showFullscreen() since there is no window manager
    logger.log("Getting screen size")
    size = system("xdpyinfo  | grep -oP 'dimensions:\\s+\\K\\S+'")[0]
    logger.note("Size: " + size.strip("\n"))
    width = int(size.split("x")[0])
    height = int(size.split("x")[1])

    logger.log("Initializing in-app overlay")
    start_overlay(width, height, shutdown, restart, AppManager.kill_app)

    logger.log("Starting launcher")
    view.setGeometry(0, 0, width, height)  # Make full-screen
    view.show()
    app.exec_()
    close()
