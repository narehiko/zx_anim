import sys, os, json, ctypes
import keyboard
import winsound

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtGui import QPainter, QPixmap, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QObject

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("zx_anim.overlay")

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
            "keys": {"q": "A", "w": "B"}
        }
        self.position = {"x": 0, "y": 0, "locked": False}
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                self.settings.update(json.load(f))
        if os.path.exists(self.pos_file):
            with open(self.pos_file, "r") as f:
                self.position.update(json.load(f))

    def save_position(self, x, y, locked):
        self.position.update({"x": x, "y": y, "locked": locked})
        with open(self.pos_file, "w") as f:
            json.dump(self.position, f)

# ================= 2. CONTROLLER (Input) =================
class InputHandler(QObject):
    keyPressed = pyqtSignal(str)
    keyReleased = pyqtSignal(str)
    toggleLock = pyqtSignal()

    def __init__(self, key_map):
        super().__init__()
        self.key_map = key_map
        self.active_keys = set()
        keyboard.hook(self._on_key_event)

    def _on_key_event(self, event):
        if event.name == 'home' and event.event_type == keyboard.KEY_DOWN:
            self.toggleLock.emit()
            return

        if event.name in self.key_map:
            if event.event_type == keyboard.KEY_DOWN and event.name not in self.active_keys:
                self.active_keys.add(event.name)
                self.keyPressed.emit(self.key_map[event.name])
                
            elif event.event_type == keyboard.KEY_UP and event.name in self.active_keys:
                self.active_keys.remove(event.name)
                self.keyReleased.emit(self.key_map[event.name])

# ================= 3. VIEW (Settings GUI) =================
class SettingsWindow(QDialog):
    def __init__(self, config_mgr, input_handler, overlay_window):
        super().__init__()
        self.config_mgr = config_mgr
        self.input_handler = input_handler
        self.overlay_window = overlay_window
        
        self.setWindowTitle("Pengaturan Keybind")
        self.resize(300, 150)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.inputs = {}

        # Membaca konfigurasi saat ini dan membuat form input secara dinamis
        # Misalnya: {"q": "A"} -> Input untuk Folder "A" isinya "q"
        for key, folder in self.config_mgr.settings["keys"].items():
            input_field = QLineEdit(key)
            self.inputs[folder] = input_field
            self.form_layout.addRow(f"Tombol untuk Folder '{folder}':", input_field)

        layout.addLayout(self.form_layout)

        # Tombol Simpan
        save_btn = QPushButton("Simpan & Terapkan")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_settings(self):
        new_keys = {}
        # Mengambil data dari text box
        for folder, line_edit in self.inputs.items():
            new_key = line_edit.text().strip().lower()
            if new_key:
                new_keys[new_key] = folder

        # 1. Simpan ke ConfigManager & File JSON
        self.config_mgr.settings["keys"] = new_keys
        with open(self.config_mgr.config_file, "w") as f:
            json.dump(self.config_mgr.settings, f)

        # 2. Update InputHandler secara dinamis (Dynamic Reconfiguration)
        keyboard.unhook_all() # Lepas semua deteksi keyboard lama
        self.input_handler.key_map = new_keys
        self.input_handler.active_keys.clear()
        keyboard.hook(self.input_handler._on_key_event) # Pasang deteksi baru

        # 3. Beritahu pengguna
        QMessageBox.information(self, "Sukses", "Keybind berhasil diperbarui!\nCoba tekan tombol barumu.")
        self.accept() # Tutup jendela dialog

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
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        # --- Inisialisasi State yang terlewat ---
        self.locked = self.config_mgr.position.get("locked", False)
        self.move(self.config_mgr.position.get("x", 0), self.config_mgr.position.get("y", 0))
        
        self.current_group = "A" 
        self.is_holding = False
        self.drag_pos = None
        self.notif = ""
        self.notif_timer = 0

        # Load gambar dan siapkan indeks
        self._load_frames()

        # Hubungkan sinyal dari keyboard ke fungsi UI
        self.input_handler.keyPressed.connect(self.on_key_press)
        self.input_handler.keyReleased.connect(self.on_key_release)
        self.input_handler.toggleLock.connect(self.on_toggle_lock)

        # Mulai timer animasi
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.start(1000 // self.settings["fps"])
        self.frame_counter = 0

        # --- Setup System Tray ---
        self.setup_tray_icon()

    def _load_frames(self):
        """Memuat gambar ke memori."""
        self.frames = {}
        self.indices = {}
        for folder in self.settings["keys"].values():
            self.frames[folder] = []
            self.indices[folder] = 0
            path = resource_path(f"frames/{folder}")
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if f.endswith(".png"):
                        self.frames[folder].append(QPixmap(os.path.join(path, f)))

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("icon.ico")))

        tray_menu = QMenu()

        # Action: Lock/Unlock
        self.lock_action = QAction("Unlock Position" if self.locked else "Lock Position", self)
        self.lock_action.triggered.connect(self.toggle_lock_from_tray)
        tray_menu.addAction(self.lock_action)

        # Action: Settings (BARU)
        settings_action = QAction("Pengaturan Keybind", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # Action: Keluar
        quit_action = QAction("Keluar", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    # Tambahkan fungsi ini di bawah setup_tray_icon
    def open_settings(self):
        """Membuka jendela pengaturan di atas aplikasi lain."""
        # Melewatkan referensi (config, input, dan jendela ini sendiri) ke SettingsWindow
        self.settings_window = SettingsWindow(self.config_mgr, self.input_handler, self)
        # Menjaga agar jendela settings tampil di atas (berguna jika main game borderless)
        self.settings_window.setWindowFlags(self.settings_window.windowFlags() | Qt.WindowStaysOnTopHint)
        self.settings_window.exec_() # exec_() membuat jendela bersifat modal (fokus ke jendela ini)

    def toggle_lock_from_tray(self):
        self.on_toggle_lock()
        if self.locked:
            self.lock_action.setText("Unlock Position")
        else:
            self.lock_action.setText("Lock Position")

    def quit_app(self):
        self.config_mgr.save_position(self.x(), self.y(), self.locked)
        self.tray_icon.hide() 
        QApplication.quit()

    # --- Event Slots ---
    def on_key_press(self, group):
        self.current_group = group
        self.is_holding = True
        if self.frames.get(group):
            self.indices[group] = (self.indices[group] + 1) % len(self.frames[group])
        self.update()

    def on_key_release(self, group):
        self.is_holding = False

    def on_toggle_lock(self):
        self.locked = not self.locked
        sound = "lock.wav" if self.locked else "unlock.wav"
        if os.path.exists(resource_path(sound)):
            winsound.PlaySound(resource_path(sound), winsound.SND_ASYNC)
        
        self.notif = "LOCKED" if self.locked else "UNLOCKED"
        self.notif_timer = int(self.settings["fps"] * 1.5)
        self.update()

    # --- Game Loop ---
    def update_animation(self):
        needs_update = False
        
        if self.is_holding and self.frames.get(self.current_group):
            self.frame_counter += 1
            if self.frame_counter >= self.settings["frame_speed"]:
                self.frame_counter = 0
                self.indices[self.current_group] = (self.indices[self.current_group] + 1) % len(self.frames[self.current_group])
                needs_update = True

        if self.notif_timer > 0:
            self.notif_timer -= 1
            needs_update = True

        if needs_update:
            self.update()

    # --- Mouse Events ---
    def mousePressEvent(self, e):
        if not self.locked and e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag_pos and not self.locked:
            self.move(e.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, e):
        self.drag_pos = None

    def wheelEvent(self, e):
        self.settings["frame_speed"] = max(1, self.settings["frame_speed"] - (1 if e.angleDelta().y() > 0 else -1))
        self.notif = f"SPEED: {self.settings['frame_speed']}"
        self.notif_timer = self.settings["fps"]
        self.update()

    # --- Drawing ---
    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

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
            p.setPen(Qt.green if not self.locked else Qt.red)
            p.drawText(QRect(0, self.height()-26, self.width(), 22), Qt.AlignCenter, self.notif)

    def closeEvent(self, e):
        # Saat ditutup manual, panggil logika exit yang aman
        self.quit_app()

# ================= RUN =================
if __name__ == "__main__":
    # Menjaga agar aplikasi tidak langsung mati saat jendela utama disembunyikan
    QApplication.setQuitOnLastWindowClosed(False) 
    
    app = QApplication(sys.argv)
    
    config = ConfigManager()
    input_handler = InputHandler(config.settings["keys"])
    window = OverlayWindow(config, input_handler)
    
    window.show()
    sys.exit(app.exec_())