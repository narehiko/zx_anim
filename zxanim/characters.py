import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .paths import resource_path, user_characters_dir


PACK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class CharacterPackError(ValueError):
    pass


@dataclass(frozen=True)
class CharacterAction:
    action_id: str
    name: str
    frames: tuple


@dataclass(frozen=True)
class CharacterPack:
    pack_id: str
    name: str
    root: Path
    width: int
    height: int
    default_action: str
    actions: dict


class CharacterRepository:
    def __init__(self, bundled_dir=None, user_dir=None):
        self.bundled_dir = Path(bundled_dir or resource_path("characters"))
        self.user_dir = Path(user_dir or user_characters_dir())
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self._packs = {}
        self.refresh()

    def refresh(self):
        packs = {}
        for base_dir in (self.bundled_dir, self.user_dir):
            if not base_dir.exists():
                continue
            for manifest in sorted(base_dir.glob("*/character.json")):
                try:
                    pack = self._load_pack(manifest)
                except CharacterPackError:
                    continue
                packs[pack.pack_id] = pack
        self._packs = packs
        return self.all()

    def all(self):
        return sorted(self._packs.values(), key=lambda pack: pack.name.lower())

    def get(self, pack_id):
        return self._packs.get(pack_id)

    def require(self, pack_id):
        pack = self.get(pack_id)
        if pack:
            return pack
        if not self._packs:
            raise CharacterPackError("No valid character packs were found.")
        return self.all()[0]

    def import_pack(self, source_dir):
        source = Path(source_dir)
        manifest = source / "character.json"
        pack = self._load_pack(manifest)
        destination = self.user_dir / pack.pack_id
        shutil.copytree(source, destination, dirs_exist_ok=True)
        self.refresh()
        return self.require(pack.pack_id)

    def _load_pack(self, manifest_path):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CharacterPackError(f"Invalid manifest: {manifest_path}") from error

        pack_id = str(data.get("id", "")).strip().lower()
        name = str(data.get("name", "")).strip()
        if not PACK_ID_PATTERN.fullmatch(pack_id) or not name:
            raise CharacterPackError("Character id or name is invalid.")

        canvas = data.get("canvas", {})
        width = self._positive_int(canvas.get("width"), "canvas width")
        height = self._positive_int(canvas.get("height"), "canvas height")
        root = manifest_path.parent.resolve()
        actions = {}

        for action_id, action_data in data.get("actions", {}).items():
            normalized_id = str(action_id).strip().lower()
            if not PACK_ID_PATTERN.fullmatch(normalized_id):
                raise CharacterPackError(f"Invalid action id: {action_id}")
            action_name = str(action_data.get("name", normalized_id.title())).strip()
            frames = []
            for relative_frame in action_data.get("frames", []):
                relative_path = Path(str(relative_frame))
                absolute_path = (root / relative_path).resolve()
                if root not in absolute_path.parents or not absolute_path.is_file():
                    raise CharacterPackError(f"Missing frame: {relative_frame}")
                frames.append(relative_path.as_posix())
            if not frames:
                raise CharacterPackError(f"Action has no frames: {normalized_id}")
            actions[normalized_id] = CharacterAction(
                normalized_id,
                action_name,
                tuple(frames),
            )

        default_action = str(data.get("default_action", "")).strip().lower()
        if not actions or default_action not in actions:
            raise CharacterPackError("The default action is invalid.")

        return CharacterPack(
            pack_id,
            name,
            root,
            width,
            height,
            default_action,
            actions,
        )

    @staticmethod
    def _positive_int(value, label):
        try:
            result = int(value)
        except (TypeError, ValueError) as error:
            raise CharacterPackError(f"Invalid {label}.") from error
        if result <= 0:
            raise CharacterPackError(f"Invalid {label}.")
        return result
