import multiprocessing
import time
from multiprocessing import Value
import tkinter as tk

from PIL import Image, ImageTk, ImageEnhance
from overlay import Window

win = Window(draggable=False, alpha=0)

should_join = Value("i", 0)
manual_show = Value("i", 0)
event = Value("i", 0)

selected = 0
buttons = []


def select_button(i):
    global selected
    buttons[selected].btn.configure(image=buttons[selected].dark_img)
    selected = i
    if selected != -1:
        buttons[selected].btn.configure(image=buttons[selected].light_img)


class Button:
    index = 0
    def button_hover(self, event):
        select_button(self.index)

    def button_leave(self, event):
        select_button(-1)

    def __init__(self, path, w, h, func):
        self.run = func
        self.btn = tk.Button(win.root, width=w, height=h, background="black",
                             activebackground="black",
                             borderwidth=0, highlightbackground="black", anchor="w", command=self.run)
        self.load = Image.open(path)
        self.img = ImageEnhance.Brightness(self.load)
        self.dark_img = ImageTk.PhotoImage(
            self.img.enhance(0.7).resize((int(height / 32), int(height / 32))))
        self.light_img = ImageTk.PhotoImage(
            self.img.enhance(1.0).resize((int(height / 32), int(height / 32))))

        self.btn.configure(image=self.dark_img)

        self.btn.bind("<Enter>", self.button_hover)
        self.btn.bind("<Leave>", self.button_leave)

    def pack(self, x, y, index):
        self.btn.grid(sticky=tk.N, column=x, row=y, padx=(int(height / 64), 0), pady=(int(height / 64), 0))
        self.index = index


alpha = 0.6
w = 0
height = 0
width = 0


def init_overlay(win_w, win_h, shutdown_func, restart_func, exit_func):
    global height, w, width, win
    width = win_w
    height = win_h
    win.size = (height / 100, height)
    w = height / 100

    buttons.append(Button("src/images/shutdown.png", int(height / 32), int(height / 32), shutdown_func))
    buttons.append(Button("src/images/restart.png", int(height / 32), int(height / 32), restart_func))
    buttons.append(Button("src/images/exit.png", int(height / 32), int(height / 32), exit_func))

    shutdown_label = tk.Label(win.root, text="Shutdown", background="black", foreground="white",
                              font=("Roboto " + str(int(height / 90)) + " bold"))
    shutdown_label.grid(sticky=tk.N, column=0, row=2, padx=(int(height / 64), 0), pady=(int(height / 64), 0))

    restart_label = tk.Label(win.root, text="Restart", background="black", foreground="white",
                             font=("Roboto " + str(int(height / 90)) + " bold"))
    restart_label.grid(sticky=tk.N, column=0, row=4, padx=(int(height / 64), 0), pady=(int(height / 64), 0))

    exit_label = tk.Label(win.root, text="Exit", background="black", foreground="white",
                          font=("Roboto " + str(int(height / 90)) + " bold"))
    exit_label.grid(sticky=tk.N, column=0, row=6, padx=(int(height / 64), 0), pady=(int(height / 64), 0))

    for i in range(0, len(buttons)):
        buttons[i].pack(0, (i*2)+1, i)

    win.root.configure(bg="black")
    win.root.after(10, update)

    win.root.mainloop()

    Window.launch()


visible = False


def show():
    win.root.lift()
    global w, visible
    visible = True
    w = height / 9
    global alpha
    alpha = 0.6
    win.focus()


def hide():
    global w, visible
    visible = False
    w = height / 100
    global alpha
    alpha = 0.2


def animate():
    win.size = ((w + (win.size[0] * 4)) / 3, height)
    win.alpha = (alpha + (win.alpha * 4)) / 3


def update():
    if should_join.value == 1:
        win.destroy()
        return

    x, y = win.root.winfo_pointerxy()
    if x < w or manual_show.value == 1:
        if not visible:
            show()
        if manual_show.value == 1 and x < w:
            manual_show.value = 0
    elif visible:
        hide()

    if visible:
        global selected
        if event.value == 1 and selected > 0:
            select_button(selected-1)
            event.value = 0
        if event.value == 2 and selected < len(buttons)-1:
            select_button(selected+1)
            event.value = 0
        if event.value == 5:
            buttons[selected].run()

    animate()
    win.root.after(10, update)


overlay_process = multiprocessing.Process()


def start_overlay(win_w, win_h, shutdown_func, restart_func, exit_func):
    global overlay_process
    overlay_process = multiprocessing.Process(target=init_overlay,
                                              args=(win_w, win_h, shutdown_func, restart_func, exit_func))
    overlay_process.start()


def stop_overlay():
    should_join.value = 1
    # Wait for window close
    time.sleep(1)

    overlay_process.join(5)
    overlay_process.terminate()
