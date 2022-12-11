from datetime import datetime
import os


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

        self.file = open(outfile + ".0.log", "a")
        self.write("Abyss Launcher Log (" + datetime.now().strftime("%H:%M:%S") + ")")
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
