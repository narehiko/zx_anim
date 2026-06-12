import keyboard
from PyQt5.QtCore import QObject, pyqtSignal


class InputHandler(QObject):
    key_pressed = pyqtSignal(str)
    key_released = pyqtSignal(str)
    toggle_lock_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    toggle_background_requested = pyqtSignal()

    def __init__(self, key_map):
        super().__init__()
        self.key_map = dict(key_map)
        self.active_keys = set()
        self._hook = keyboard.hook(self._on_key_event)

    def update_key_map(self, key_map):
        self.key_map = dict(key_map)
        self.active_keys.clear()

    def close(self):
        if self._hook:
            keyboard.unhook(self._hook)
            self._hook = None

    def _on_key_event(self, event):
        name = str(event.name).lower()
        is_down = event.event_type == keyboard.KEY_DOWN
        ctrl_pressed = keyboard.is_pressed("ctrl")

        if name == "home" and is_down:
            if ctrl_pressed:
                self.open_settings_requested.emit()
            else:
                self.toggle_lock_requested.emit()
            return

        if name == "g" and is_down and ctrl_pressed:
            self.toggle_background_requested.emit()
            return

        action = self.key_map.get(name)
        if not action:
            return

        if is_down and name not in self.active_keys:
            self.active_keys.add(name)
            self.key_pressed.emit(action)
        elif not is_down and name in self.active_keys:
            self.active_keys.remove(name)
            self.key_released.emit(action)
