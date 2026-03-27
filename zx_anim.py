import sys, os, json, ctypes
import keyboard
import winsound

from PyQt5.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QMenu, QAction,
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtGui import QPainter, QPixmap, QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QObject

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("zx_anim.overlay.v2.1")

def resource_path(path):
    try:
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, path)

# ================= 1. MODEL (Config) =================
class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.pos_file = "position.json"
        
        self.settings = {
            "fps": 60,
            "frame_speed": 5, 
            "keys": {"q": "A", "w": "B"},
            "bg_mode": 0 # 0: Transparan, 1: Hijau, 2: Magenta
        }
        self.position = {"x": 0, "y": 0, "locked": False}
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.settings.update(json.load(f))
            except: pass
        if os.path.exists(self.pos_file):
            try:
                with open(self.pos_file, "r") as f:
                    self.position.update(json.load(f))
            except: pass

    def save_position(self, x, y, locked):
        self.position.update({"x": x, "y": y, "locked": locked})
        try:
            with open(self.pos_file, "w") as f:
                json.dump(self.position, f)
        except: pass

    def save_settings(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.settings, f)
        except: pass

# ================= 2. CONTROLLER (Input) =================
class InputHandler(QObject):
    keyPressed = pyqtSignal(str)
    keyReleased = pyqtSignal(str)
    toggleLock = pyqtSignal()
    openSettingsRequested = pyqtSignal()
    toggleBgRequested = pyqtSignal() # Signal ganti background

    def __init__(self, key_map):
        super().__init__()
        self.key_map = key_map
        self.active_keys = set()
        self.ctrl_pressed = False
        keyboard.hook(self._on_key_event)

    def _on_key_event(self, event):
        if event.name == 'ctrl':
            self.ctrl_pressed = (event.event_type == keyboard.KEY_DOWN)

        # Shortcut: Ctrl + HOME (Buka Settings)
        if event.name == 'home' and event.event_type == keyboard.KEY_DOWN and self.ctrl_pressed:
            self.openSettingsRequested.emit()
            return

        # Shortcut: Ctrl + G (Ganti Background / Green Screen)
        if event.name == 'g' and event.event_type == keyboard.KEY_DOWN and self.ctrl_pressed:
            self.toggleBgRequested.emit()
            return

        # Shortcut: HOME (Lock/Unlock)
        if event.name == 'home' and event.event_type == keyboard.KEY_DOWN and not self.ctrl_pressed:
            self.toggleLock.emit()
            return

        # Handle mapped keys (perbaikan bug nyangkut)
        if event.name in self.key_map:
            if event.event_type == keyboard.KEY_DOWN and event.name not in self.active_keys:
                self.active_keys.add(event.name)
                self.keyPressed.emit(self.key_map[event.name])
                
            elif event.event_type == keyboard.KEY_UP and event.name in self.active_keys:
                self.active_keys.remove(event.name)
                self.keyReleased.emit(self.key_map[event.name])

# ================= 3. VIEW (Settings GUI) =================
class SettingsWindow(QDialog):
    def __init__(self, config_mgr, input_handler):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.config_mgr = config_mgr
        self.input_handler = input_handler
        self.setWindowTitle("Pengaturan Keybind v2.1")
        self.resize(300, 150)
        
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.inputs = {}

        current_keys = self.config_mgr.settings.get("keys", {})
        sorted_keys = sorted(current_keys.items(), key=lambda x: x[1])

        for key, folder in sorted_keys:
            input_field = QLineEdit(key)
            self.inputs[folder] = input_field
            self.form_layout.addRow(f"Tombol Folder '{folder}':", input_field)

        layout.addLayout(self.form_layout)

        save_btn = QPushButton("Simpan & Terapkan")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        self.setLayout(layout)

    def save_settings(self):
        new_keys = {}
        for folder, line_edit in self.inputs.items():
            new_key = line_edit.text().strip().lower()
            if new_key:
                new_keys[new_key] = folder

        self.config_mgr.settings["keys"] = new_keys
        self.config_mgr.save_settings()

        keyboard.unhook_all()
        self.input_handler.key_map = new_keys
        self.input_handler.active_keys.clear()
        self.input_handler.ctrl_pressed = False
        keyboard.hook(self.input_handler._on_key_event)

        QMessageBox.information(self, "Sukses", "Keybind diperbarui!\nCoba tombol barumu.")
        self.accept()

# ================= 4. VIEW (UI Overlay) =================
class OverlayWindow(QWidget):
    def __init__(self, config_mgr, input_handler):
        super().__init__()
        self.config_mgr = config_mgr
        self.input_handler = input_handler
        self.settings = config_mgr.settings

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(260, 200)
        
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.locked = self.config_mgr.position.get("locked", False)
        self.move(self.config_mgr.position.get("x", 0), self.config_mgr.position.get("y", 0))
        
        # PERBAIKAN LOGIKA HOLD: Pakai Set/List untuk melacak grup aktif
        self.active_groups = set() 
        self.current_group = "A" 
        
        self.drag_pos = None
        self.notif = ""
        self.notif_timer = 0
        self.frames = {}
        self.indices = {}

        self._load_frames()

        self.input_handler.keyPressed.connect(self.on_key_press)
        self.input_handler.keyReleased.connect(self.on_key_release)
        self.input_handler.toggleLock.connect(self.on_toggle_lock)
        self.input_handler.openSettingsRequested.connect(self.open_settings)
        self.input_handler.toggleBgRequested.connect(self.on_toggle_bg)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(1000 // self.settings.get("fps", 60))
        self.frame_counter = 0

        self.settings_window = None 
        self.setup_tray_icon()

    def _load_frames(self):
        for folder in self.settings.get("keys", {}).values():
            self.frames[folder] = []
            self.indices[folder] = 0
            path = resource_path(f"frames/{folder}")
            if os.path.exists(path):
                files = sorted([f for f in os.listdir(path) if f.endswith(".png")])
                for f in files:
                    self.frames[folder].append(QPixmap(os.path.join(path, f)))
        
        if not self.frames.get("A") and self.frames:
            self.current_group = list(self.frames.keys())[0]

    def setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))

        tray_menu = QMenu()

        self.lock_action = QAction("Unlock Position" if self.locked else "Lock Position", self)
        self.lock_action.triggered.connect(self.toggle_lock_from_tray)
        tray_menu.addAction(self.lock_action)

        settings_action = QAction("Pengaturan Keybind", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        bg_action = QAction("Ganti Background (Transparan/Hijau/Pink)", self)
        bg_action.triggered.connect(self.on_toggle_bg)
        tray_menu.addAction(bg_action)

        tray_menu.addSeparator()

        quit_action = QAction("Keluar", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def open_settings(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = SettingsWindow(self.config_mgr, self.input_handler)
        self.settings_window.exec_()

    def toggle_lock_from_tray(self):
        self.on_toggle_lock()
        if hasattr(self, 'lock_action'):
            self.lock_action.setText("Unlock Position" if self.locked else "Lock Position")

    def quit_app(self):
        self.config_mgr.save_position(self.x(), self.y(), self.locked)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide() 
        QApplication.quit()

    # --- PERBAIKAN BUG ANIMASI ---
    def on_key_press(self, group):
        self.active_groups.add(group)
        self.current_group = group
        self.frame_counter = 0 # Reset waktu agar langsung ganti frame!
        if self.frames.get(group):
            self.indices[group] = (self.indices[group] + 1) % len(self.frames[group])
        self.update()

    def on_key_release(self, group):
        if group in self.active_groups:
            self.active_groups.remove(group)
        # Jika tombol saat ini dilepas, tapi tombol lain masih ditahan, pindah ke tombol lain
        if self.active_groups and self.current_group not in self.active_groups:
            self.current_group = list(self.active_groups)[0]
            self.frame_counter = 0

    def on_toggle_lock(self):
        self.locked = not self.locked
        sound = "lock.wav" if self.locked else "unlock.wav"
        if os.path.exists(resource_path(sound)):
            winsound.PlaySound(resource_path(sound), winsound.SND_ASYNC)
        
        self.notif = "LOCKED" if self.locked else "UNLOCKED"
        self.notif_timer = int(self.settings.get("fps", 60) * 1.5)
        if hasattr(self, 'lock_action'):
            self.lock_action.setText("Unlock Position" if self.locked else "Lock Position")
        self.update()

    def on_toggle_bg(self):
        # Rotasi Background: 0 (Transparan) -> 1 (Hijau) -> 2 (Magenta)
        self.settings["bg_mode"] = (self.settings.get("bg_mode", 0) + 1) % 3
        self.config_mgr.save_settings()
        
        mode_names = {0: "TRANSPARAN", 1: "LAYAR HIJAU", 2: "LAYAR PINK"}
        self.notif = f"BG: {mode_names[self.settings['bg_mode']]}"
        self.notif_timer = int(self.settings.get("fps", 60) * 1.5)
        self.update()

    def update_animation(self):
        needs_update = False
        
        # Animasi tahan yang sudah diperbaiki
        if self.active_groups and self.frames.get(self.current_group):
            self.frame_counter += 1
            if self.frame_counter >= self.settings.get("frame_speed", 5):
                self.frame_counter = 0
                self.indices[self.current_group] = (self.indices[self.current_group] + 1) % len(self.frames[self.current_group])
                needs_update = True

        if self.notif_timer > 0:
            self.notif_timer -= 1
            needs_update = True

        if needs_update:
            self.update()

    def mousePressEvent(self, e):
        if not self.locked and e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos and not self.locked:
            self.move(e.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def wheelEvent(self, e):
        # Batasi minimum speed 1 dan maksimum 20 supaya tidak seolah "nyangkut"
        current_speed = self.settings.get("frame_speed", 5)
        new_speed = current_speed - (1 if e.angleDelta().y() > 0 else -1)
        self.settings["frame_speed"] = max(1, min(new_speed, 20))
        self.config_mgr.save_settings()
        
        self.notif = f"SPEED: {self.settings['frame_speed']}"
        self.notif_timer = self.settings.get("fps", 60)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        # Gambar Background Solid (Jika tidak transparan)
        bg_mode = self.settings.get("bg_mode", 0)
        if bg_mode == 1:
            p.fillRect(self.rect(), QColor(0, 255, 0)) # Hijau Terang
        elif bg_mode == 2:
            p.fillRect(self.rect(), QColor(255, 0, 255)) # Magenta

        # Gambar Karakter
        frames_list = self.frames.get(self.current_group, [])
        if frames_list:
            frame = frames_list[self.indices[self.current_group]]
            fw, fh = frame.width(), frame.height()
            ww, wh = self.width(), self.height()

            scale = min(ww / fw, wh / fh) * 0.9
            nw, nh = int(fw * scale), int(fh * scale)

            p.drawPixmap(QRect(ww//2-nw//2, wh//2-nh//2, nw, nh), frame)

        if self.notif_timer > 0:
            p.setFont(QFont("Segoe UI", 11, QFont.Bold))
            p.setPen(Qt.black if bg_mode != 0 else (Qt.green if not self.locked else Qt.red))
            p.drawText(QRect(0, self.height()-26, self.width(), 22), Qt.AlignCenter, self.notif)

    def closeEvent(self, e):
        self.quit_app()

# ================= RUN =================
if __name__ == "__main__":
    QApplication.setQuitOnLastWindowClosed(False) 
    app = QApplication(sys.argv)
    
    config = ConfigManager()
    input_handler = InputHandler(config.settings.get("keys", {}))
    window = OverlayWindow(config, input_handler)
    
    window.show()
    sys.exit(app.exec_())