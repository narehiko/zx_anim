import ctypes
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

from .characters import CharacterPackError, CharacterRepository
from .config import ConfigManager
from .constants import APP_ID, APP_NAME
from .input import InputHandler
from .obs_server import ObsServer, ObsState
from .overlay import OverlayWindow


def run():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    QApplication.setQuitOnLastWindowClosed(False)
    application = QApplication(sys.argv)
    application.setApplicationName(APP_NAME)

    config = ConfigManager()
    repository = CharacterRepository()
    try:
        repository.require(config.settings.get("character"))
    except CharacterPackError as error:
        QMessageBox.critical(None, "ZX Anim", str(error))
        return 1

    obs_state = ObsState()
    obs_server = ObsServer(
        repository,
        obs_state,
        config.settings.get("obs_port", 17841),
    )
    obs_server.start()
    input_handler = InputHandler(config.settings.get("keys", {}))
    window = OverlayWindow(
        config,
        input_handler,
        repository,
        obs_server,
        obs_state,
    )
    if config.settings.get("show_preview_on_startup", False):
        window.show()
    return application.exec_()
