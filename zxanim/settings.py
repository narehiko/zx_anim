import os
import shutil
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
)

from .characters import CharacterPackError
from .gif_importer import GifImportError, import_gif_as_character
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
        import_gif_button = QPushButton("Import GIF")
        import_gif_button.clicked.connect(self._import_gif)
        open_button = QPushButton("Open Character Folder")
        open_button.clicked.connect(self._open_character_folder)
        help_button = QPushButton("Import Help")
        help_button.clicked.connect(self._show_import_help)
        character_buttons.addWidget(import_button)
        character_buttons.addWidget(import_gif_button)
        character_buttons.addWidget(open_button)
        character_buttons.addWidget(help_button)
        form.addRow("", character_buttons)

        self.keys_layout = QFormLayout()
        form.addRow(QLabel("Key bindings"))
        form.addRow(self.keys_layout)

        self.smoothing_input = QSpinBox()
        self.smoothing_input.setRange(0, 200)
        self.smoothing_input.setSingleStep(10)
        self.smoothing_input.setSuffix(" ms")
        self.smoothing_input.setSpecialValueText("Off")
        self.smoothing_input.setValue(
            int(self.config.settings.get("rapid_tap_smoothing_ms", 70))
        )
        self.smoothing_input.setToolTip(
            "Limits visual frame changes during fast alternating taps. "
            "Input detection remains immediate."
        )
        form.addRow("Rapid tap smoothing:", self.smoothing_input)

        self.preview_scale_input = QSpinBox()
        self.preview_scale_input.setRange(25, 100)
        self.preview_scale_input.setSingleStep(5)
        self.preview_scale_input.setSuffix("%")
        self.preview_scale_input.setValue(
            int(self.config.settings.get("preview_scale_percent", 60))
        )
        form.addRow("Desktop preview size:", self.preview_scale_input)

        self.preview_startup_input = QCheckBox("Show preview when ZX Anim starts")
        self.preview_startup_input.setChecked(
            bool(self.config.settings.get("show_preview_on_startup", False))
        )
        form.addRow("", self.preview_startup_input)

        self.tap_sound_field = QLineEdit(self.config.settings.get("tap_sound_path", ""))
        self.tap_sound_field.setReadOnly(True)
        form.addRow("Tap sound:", self._file_row(self.tap_sound_field, self._choose_tap_sound))

        self.hold_sound_field = QLineEdit(self.config.settings.get("hold_sound_path", ""))
        self.hold_sound_field.setReadOnly(True)
        form.addRow(
            "Hold sound:",
            self._file_row(self.hold_sound_field, self._choose_hold_sound),
        )

        self.hold_delay_input = QSpinBox()
        self.hold_delay_input.setRange(0, 1000)
        self.hold_delay_input.setSingleStep(20)
        self.hold_delay_input.setSuffix(" ms")
        self.hold_delay_input.setValue(
            int(self.config.settings.get("hold_sound_delay_ms", 180))
        )
        form.addRow("Hold sound delay:", self.hold_delay_input)

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
        self.config.settings["rapid_tap_smoothing_ms"] = (
            self.smoothing_input.value()
        )
        self.config.settings["preview_scale_percent"] = (
            self.preview_scale_input.value()
        )
        self.config.settings["show_preview_on_startup"] = (
            self.preview_startup_input.isChecked()
        )
        self.config.settings["tap_sound_path"] = self.tap_sound_field.text()
        self.config.settings["hold_sound_path"] = self.hold_sound_field.text()
        self.config.settings["hold_sound_delay_ms"] = self.hold_delay_input.value()
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

    def _import_gif(self):
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Select a GIF",
            "",
            "GIF files (*.gif)",
        )
        if not source:
            return
        try:
            pack_id = import_gif_as_character(source, self.repository.user_dir)
            self.repository.refresh()
        except (GifImportError, OSError) as error:
            QMessageBox.critical(self, "GIF Import Failed", str(error))
            return
        self._reload_character_combo(pack_id)
        QMessageBox.information(
            self,
            "GIF Imported",
            "The GIF was converted into a responsive character. "
            "Set the key bindings and save when you are ready.",
        )

    def _open_character_folder(self):
        os.startfile(str(self.repository.user_dir))

    def _show_import_help(self):
        dialog = ImportHelpDialog(self)
        dialog.exec_()

    def _reload_character_combo(self, selected_pack_id):
        self.character_combo.clear()
        for available_pack in self.repository.all():
            self.character_combo.addItem(available_pack.name, available_pack.pack_id)
        self.character_combo.setCurrentIndex(
            self.character_combo.findData(selected_pack_id)
        )

    def _file_row(self, field, chooser):
        row = QHBoxLayout()
        choose_button = QPushButton("Choose WAV")
        clear_button = QPushButton("Clear")
        choose_button.clicked.connect(chooser)
        clear_button.clicked.connect(lambda: field.setText(""))
        row.addWidget(field)
        row.addWidget(choose_button)
        row.addWidget(clear_button)
        return row

    def _choose_tap_sound(self):
        self._choose_sound(self.tap_sound_field)

    def _choose_hold_sound(self):
        self._choose_sound(self.hold_sound_field)

    def _choose_sound(self, field):
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Select a WAV sound",
            "",
            "WAV files (*.wav)",
        )
        if not source:
            return
        try:
            field.setText(str(self._copy_sound(source)))
        except OSError as error:
            QMessageBox.critical(self, "Sound Import Failed", str(error))

    def _copy_sound(self, source):
        source_path = Path(source)
        audio_dir = self.config.data_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        destination = audio_dir / source_path.name
        counter = 2
        while destination.exists():
            destination = audio_dir / f"{source_path.stem}-{counter}{source_path.suffix}"
            counter += 1
        shutil.copy2(source_path, destination)
        return destination


class ImportHelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Character Import Help")
        self.setMinimumSize(520, 440)
        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(
            """
            <h2>Importing a GIF</h2>
            <ol>
              <li>Prepare one animated GIF.</li>
              <li>Transparent GIF is recommended for OBS Browser Source.</li>
              <li>Green-screen GIF also works if you prefer chroma key editing.</li>
              <li>Click <b>Import GIF</b>, choose the file, then set your keys.</li>
              <li>Use <b>Rapid tap smoothing</b> if streams look shaky.</li>
            </ol>
            <h3>Best GIF Settings</h3>
            <table border="1" cellspacing="0" cellpadding="6">
              <tr><td>Background</td><td>Transparent is best. Green is okay.</td></tr>
              <tr><td>Canvas</td><td>Keep empty space around the character small.</td></tr>
              <tr><td>Frames</td><td>Short loops feel more responsive for tapping.</td></tr>
              <tr><td>Size</td><td>Use a reasonable resolution, such as 512px wide.</td></tr>
            </table>
            <h3>Audio</h3>
            <p>Use WAV files. Tap sound plays on key press. Hold sound plays once
            after the hold delay while a key is still pressed.</p>
            """
        )
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(browser)
        layout.addWidget(close_button)
