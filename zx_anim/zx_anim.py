import sys, os, json, ctypes
import keyboard
import winsound

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QRect

# ================= WINDOWS TASKBAR ID =================
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("zx_anim")

# ================= RESOURCE PATH =================
def resource_path(path):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, path)

# ================= CONFIG =================
FPS = 240
POS_FILE = "position.json"

class ZXAnim(QWidget):
    def __init__(self):
        super().__init__()

        # ============== WINDOW ==============
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(260, 200)
        self.setWindowTitle("ZX Anim")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        # ============== LOAD STATE ==============
        self.locked = False
        if os.path.exists(POS_FILE):
            with open(POS_FILE, "r") as f:
                d = json.load(f)
                self.move(d.get("x", 200), d.get("y", 200))
                self.locked = d.get("locked", False)

        # ============== LOAD FRAMES ==============
        self.frames = []
        frames_dir = resource_path("frames")

        for name in sorted(os.listdir(frames_dir)):
            if name.lower().endswith(".png"):
                self.frames.append(
                    QPixmap(resource_path(f"frames/{name}"))
                )

        if not self.frames:
            raise RuntimeError("Frame PNG tidak ditemukan")

        self.frame_index = 0

        # ============== INPUT STATE (EDGE) ==============
        self.z_last = False
        self.x_last = False
        self.home_last = False

        # ============== DRAG ==============
        self.drag_pos = None

        # ============== NOTIFICATION ==============
        self.notif = ""
        self.notif_timer = 0

        # ============== TIMER ==============
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_logic)
        self.timer.start(1000 // FPS)

    # ================= LOGIC =================
    def update_logic(self):
        z = keyboard.is_pressed("z")
        x = keyboard.is_pressed("x")
        home = keyboard.is_pressed("home")

        # Z / X → advance 1 frame per tap
        if (z and not self.z_last) or (x and not self.x_last):
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        # HOME → LOCK / UNLOCK
        if home and not self.home_last:
            self.locked = not self.locked
            sound = "lock.wav" if self.locked else "unlock.wav"

            winsound.PlaySound(
                resource_path(sound),
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )

            self.notif = "LOCKED" if self.locked else "UNLOCKED"
            self.notif_timer = 90

        self.z_last = z
        self.x_last = x
        self.home_last = home

        if self.notif_timer > 0:
            self.notif_timer -= 1

        self.update()

    # ================= DRAG WINDOW =================
    def mousePressEvent(self, e):
        if not self.locked and e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos and not self.locked:
            self.move(e.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    # ================= DRAW =================
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        frame = self.frames[self.frame_index]
        fw, fh = frame.width(), frame.height()
        ww, wh = self.width(), self.height()

        scale = min(ww / fw, wh / fh) * 0.9
        nw, nh = int(fw * scale), int(fh * scale)

        p.drawPixmap(
            QRect(ww // 2 - nw // 2, wh // 2 - nh // 2, nw, nh),
            frame
        )

        if self.notif_timer > 0:
            p.setFont(QFont("Segoe UI", 12, QFont.Bold))
            p.setPen(Qt.red if self.locked else Qt.green)
            p.drawText(
                QRect(0, wh - 28, ww, 24),
                Qt.AlignCenter,
                self.notif
            )

    # ================= SAVE STATE =================
    def closeEvent(self, e):
        with open(POS_FILE, "w") as f:
            json.dump({
                "x": self.x(),
                "y": self.y(),
                "locked": self.locked
            }, f)

# ================= RUN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ZXAnim()
    w.show()
    sys.exit(app.exec_())
