import winsound

from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QStyle, QSystemTrayIcon, QWidget

from .constants import BACKGROUND_NAMES
from .paths import resource_path
from .settings import SettingsWindow


class OverlayWindow(QWidget):
    def __init__(self, config, input_handler, repository, obs_server, obs_state):
        super().__init__()
        self.config = config
        self.input_handler = input_handler
        self.repository = repository
        self.obs_server = obs_server
        self.obs_state = obs_state
        self.settings = config.settings
        self.pack = None
        self.frames = {}
        self.indices = {}
        self.active_actions = []
        self.current_action = ""
        self.frame_counter = 0
        self.drag_position = None
        self.notification = ""
        self.notification_timer = 0
        self.settings_window = None

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(585, 427)
        icon_path = resource_path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.locked = bool(self.config.position.get("locked", False))
        self.move(
            int(self.config.position.get("x", 0)),
            int(self.config.position.get("y", 0)),
        )

        self.input_handler.key_pressed.connect(self.on_key_press)
        self.input_handler.key_released.connect(self.on_key_release)
        self.input_handler.toggle_lock_requested.connect(self.on_toggle_lock)
        self.input_handler.open_settings_requested.connect(self.open_settings)
        self.input_handler.toggle_background_requested.connect(
            self.on_toggle_background
        )

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(self._timer_interval())
        self.reload_character()
        self.setup_tray_icon()

    def reload_character(self):
        self.repository.refresh()
        self.pack = self.repository.require(self.settings.get("character"))
        self.settings["character"] = self.pack.pack_id
        self.frames = {}
        self.indices = {}
        for action_id, action in self.pack.actions.items():
            self.frames[action_id] = [
                QPixmap(str(self.pack.root / frame)) for frame in action.frames
            ]
            self.indices[action_id] = 0
        self.resize(self.pack.width, self.pack.height)
        self.active_actions.clear()
        self.current_action = self.pack.default_action
        self.frame_counter = 0
        self.input_handler.update_key_map(self.settings.get("keys", {}))
        self.animation_timer.setInterval(self._timer_interval())
        self._publish_frame()
        self.update()

    def setup_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = resource_path("icon.ico")
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(
                self.style().standardIcon(QStyle.SP_ComputerIcon)
            )

        tray_menu = QMenu()
        self.lock_action = QAction(self._lock_action_text(), self)
        self.lock_action.triggered.connect(self.on_toggle_lock)
        tray_menu.addAction(self.lock_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)

        copy_obs_action = QAction("Copy OBS Browser Source URL", self)
        copy_obs_action.triggered.connect(
            lambda: QApplication.clipboard().setText(self.obs_server.url)
        )
        tray_menu.addAction(copy_obs_action)

        background_action = QAction("Change Preview Background", self)
        background_action.triggered.connect(self.on_toggle_background)
        tray_menu.addAction(background_action)
        tray_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def open_settings(self):
        if self.settings_window and self.settings_window.isVisible():
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        self.settings_window = SettingsWindow(
            self.config,
            self.repository,
            self.obs_server.url,
        )
        self.settings_window.settings_applied.connect(self.reload_character)
        self.settings_window.show()

    def quit_app(self):
        self.config.save_position(self.x(), self.y(), self.locked)
        self.input_handler.close()
        self.obs_server.stop()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        QApplication.quit()

    def on_key_press(self, action):
        if action not in self.frames:
            return
        if action not in self.active_actions:
            self.active_actions.append(action)
        self.current_action = action
        self.frame_counter = 0
        self._advance_frame()

    def on_key_release(self, action):
        if action in self.active_actions:
            self.active_actions.remove(action)
        if self.current_action == action:
            self.current_action = (
                self.active_actions[-1]
                if self.active_actions
                else self.pack.default_action
            )
            self.frame_counter = 0
            self._publish_frame()
            self.update()

    def on_toggle_lock(self):
        self.locked = not self.locked
        sound_name = "lock.wav" if self.locked else "unlock.wav"
        sound_path = resource_path(sound_name)
        if sound_path.exists():
            winsound.PlaySound(str(sound_path), winsound.SND_ASYNC)
        self.notification = "LOCKED" if self.locked else "UNLOCKED"
        self.notification_timer = int(self.settings.get("fps", 60) * 1.5)
        if hasattr(self, "lock_action"):
            self.lock_action.setText(self._lock_action_text())
        self.update()

    def on_toggle_background(self):
        mode = (int(self.settings.get("bg_mode", 0)) + 1) % 3
        self.settings["bg_mode"] = mode
        self.config.save_settings()
        self.notification = f"PREVIEW: {BACKGROUND_NAMES[mode].upper()}"
        self.notification_timer = int(self.settings.get("fps", 60) * 1.5)
        self.update()

    def update_animation(self):
        needs_update = False
        if self.active_actions and self.frames.get(self.current_action):
            self.frame_counter += 1
            if self.frame_counter >= int(self.settings.get("frame_speed", 5)):
                self.frame_counter = 0
                self._advance_frame()
                needs_update = True
        if self.notification_timer > 0:
            self.notification_timer -= 1
            needs_update = True
        if needs_update:
            self.update()

    def mousePressEvent(self, event):
        if not self.locked and event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPos() - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self.drag_position is not None and not self.locked:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def wheelEvent(self, event):
        current_speed = int(self.settings.get("frame_speed", 5))
        delta = -1 if event.angleDelta().y() > 0 else 1
        self.settings["frame_speed"] = max(1, min(current_speed + delta, 20))
        self.config.save_settings()
        self.notification = f"SPEED: {self.settings['frame_speed']}"
        self.notification_timer = int(self.settings.get("fps", 60))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        background_mode = int(self.settings.get("bg_mode", 0))
        if background_mode == 1:
            painter.fillRect(self.rect(), QColor(0, 255, 0))
        elif background_mode == 2:
            painter.fillRect(self.rect(), QColor(255, 0, 255))

        frame_list = self.frames.get(self.current_action, [])
        if frame_list:
            frame = frame_list[self.indices[self.current_action]]
            scale = min(
                self.width() / frame.width(),
                self.height() / frame.height(),
            )
            width = int(frame.width() * scale)
            height = int(frame.height() * scale)
            painter.drawPixmap(
                QRect(
                    (self.width() - width) // 2,
                    (self.height() - height) // 2,
                    width,
                    height,
                ),
                frame,
            )

        if self.notification_timer > 0:
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            if background_mode:
                painter.setPen(Qt.black)
            else:
                painter.setPen(Qt.red if self.locked else Qt.green)
            painter.drawText(
                QRect(0, self.height() - 26, self.width(), 22),
                Qt.AlignCenter,
                self.notification,
            )

    def closeEvent(self, event):
        self.quit_app()
        event.accept()

    def _advance_frame(self):
        frame_list = self.frames.get(self.current_action, [])
        if frame_list:
            self.indices[self.current_action] = (
                self.indices[self.current_action] + 1
            ) % len(frame_list)
        self._publish_frame()
        self.update()

    def _publish_frame(self):
        action = self.pack.actions[self.current_action]
        index = self.indices[self.current_action]
        relative_path = action.frames[index]
        self.obs_state.update(
            f"/asset/{self.pack.pack_id}/{relative_path}"
        )

    def _timer_interval(self):
        fps = max(1, int(self.settings.get("fps", 60)))
        return max(1, 1000 // fps)

    def _lock_action_text(self):
        return "Unlock Position" if self.locked else "Lock Position"
