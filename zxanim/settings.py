import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .characters import CharacterPackError
from .paths import resource_path


class SettingsWindow(QDialog):
    settings_applied = pyqtSignal()

    def __init__(self, config, repository, obs_url):
        super().__init__()
        self.config = config
        self.repository = repository
        self.obs_url = obs_url
        self.key_inputs = {}
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("ZX Anim Settings")
        self.setMinimumWidth(420)
        icon_path = resource_path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.character_combo = QComboBox()
        for pack in self.repository.all():
            self.character_combo.addItem(pack.name, pack.pack_id)
        selected_index = self.character_combo.findData(
            self.config.settings.get("character")
        )
        self.character_combo.setCurrentIndex(max(0, selected_index))
        self.character_combo.currentIndexChanged.connect(self._rebuild_key_inputs)
        form.addRow("Character:", self.character_combo)

        character_buttons = QHBoxLayout()
        import_button = QPushButton("Import Character")
        import_button.clicked.connect(self._import_character)
        open_button = QPushButton("Open Character Folder")
        open_button.clicked.connect(self._open_character_folder)
        character_buttons.addWidget(import_button)
        character_buttons.addWidget(open_button)
        form.addRow("", character_buttons)

        self.keys_layout = QFormLayout()
        form.addRow(QLabel("Key bindings"))
        form.addRow(self.keys_layout)

        obs_row = QHBoxLayout()
        obs_field = QLineEdit(self.obs_url)
        obs_field.setReadOnly(True)
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(self.obs_url)
        )
        obs_row.addWidget(obs_field)
        obs_row.addWidget(copy_button)
        form.addRow("OBS Browser Source:", obs_row)

        layout.addLayout(form)
        save_button = QPushButton("Save and Apply")
        save_button.clicked.connect(self._save)
        layout.addWidget(save_button)
        self._rebuild_key_inputs()

    def _rebuild_key_inputs(self):
        while self.keys_layout.rowCount():
            self.keys_layout.removeRow(0)
        self.key_inputs = {}
        pack = self.repository.require(self.character_combo.currentData())
        configured = self.config.settings.get("keys", {})
        action_keys = {action: key for key, action in configured.items()}
        for action in pack.actions.values():
            field = QLineEdit(action_keys.get(action.action_id, ""))
            field.setPlaceholderText("Example: q")
            self.key_inputs[action.action_id] = field
            self.keys_layout.addRow(f"{action.name}:", field)

    def _save(self):
        new_keys = {}
        for action_id, field in self.key_inputs.items():
            key = field.text().strip().lower()
            if key:
                new_keys[key] = action_id
        if not new_keys:
            QMessageBox.warning(
                self,
                "Missing Key Bindings",
                "Assign at least one key before saving.",
            )
            return
        self.config.settings["character"] = self.character_combo.currentData()
        self.config.settings["keys"] = new_keys
        self.config.save_settings()
        self.settings_applied.emit()
        self.accept()

    def _import_character(self):
        source = QFileDialog.getExistingDirectory(
            self,
            "Select a Character Pack Folder",
        )
        if not source:
            return
        try:
            pack = self.repository.import_pack(source)
        except (CharacterPackError, OSError) as error:
            QMessageBox.critical(self, "Import Failed", str(error))
            return
        self.character_combo.clear()
        for available_pack in self.repository.all():
            self.character_combo.addItem(available_pack.name, available_pack.pack_id)
        self.character_combo.setCurrentIndex(
            self.character_combo.findData(pack.pack_id)
        )

    def _open_character_folder(self):
        os.startfile(str(self.repository.user_dir))
