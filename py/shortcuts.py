from pynput.keyboard import Key, Listener
import threading

shift = False
ctrl = False

shortcuts = {}
key_event = None


def register_shortcut(key, func):
    shortcuts[key] = func


def listen_key(key):
    if key_event is not None:
        key_event(key)
    if key in shortcuts:
        shortcuts[key]()


def compress_key(key):
    out = str(key)
    if str(key)[0] == "'":
        out = str(key)[1:-1]
    if shift:
        out = out.upper()
    if ctrl:
        out = "^" + out
    return out


def on_press(key):
    if key == Key.ctrl:
        global ctrl
        ctrl = True
    elif key == Key.shift:
        global shift
        shift = True
    else:
        listen_key(compress_key(key))


def on_release(key):
    if key == Key.ctrl:
        global ctrl
        ctrl = False
    if key == Key.shift:
        global shift
        shift = False


listener = None


def _listener_init():
    global listener
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


shortcuts_thread = None


def start_listener(key_func):
    global shortcuts_thread, key_event
    key_event = key_func
    shortcuts_thread = threading.Thread(name="Shortcuts Thread", target=_listener_init)
    shortcuts_thread.start()


def stop_listener():
    listener.stop()
    shortcuts_thread.join(5)
