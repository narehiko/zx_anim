import json
import re
from pathlib import Path

from PIL import Image, ImageSequence


class GifImportError(ValueError):
    pass


def import_gif_as_character(gif_path, destination_root, name=None):
    source = Path(gif_path)
    if not source.is_file():
        raise GifImportError("Select a valid GIF file.")

    character_name = (name or source.stem).strip() or "Imported GIF"
    pack_id = _unique_pack_id(destination_root, _slugify(character_name))
    pack_dir = Path(destination_root) / pack_id
    frames_dir = pack_dir / "actions" / "tap"
    frames_dir.mkdir(parents=True, exist_ok=False)

    try:
        with Image.open(source) as image:
            frames = _extract_frames(image, frames_dir)
            width, height = image.size
    except Exception as error:
        if pack_dir.exists():
            _remove_created_files(pack_dir)
        raise GifImportError(f"Could not import GIF: {error}") from error

    manifest = {
        "id": pack_id,
        "name": character_name,
        "canvas": {"width": width, "height": height},
        "default_action": "left",
        "actions": {
            "left": {
                "name": "Left Key",
                "frames": frames,
            },
            "right": {
                "name": "Right Key",
                "frames": frames,
            },
        },
    }
    (pack_dir / "character.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return pack_id


def _extract_frames(image, frames_dir):
    frames = []
    for index, frame in enumerate(ImageSequence.Iterator(image), start=1):
        frame_path = frames_dir / f"{index:04d}.png"
        frame.convert("RGBA").save(frame_path)
        frames.append(frame_path.relative_to(frames_dir.parents[1]).as_posix())
    if not frames:
        raise GifImportError("The GIF has no readable frames.")
    return frames


def _slugify(value):
    slug = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug or "imported-gif"


def _unique_pack_id(destination_root, base_id):
    destination = Path(destination_root)
    pack_id = base_id
    counter = 2
    while (destination / pack_id).exists():
        pack_id = f"{base_id}-{counter}"
        counter += 1
    return pack_id


def _remove_created_files(path):
    for item in sorted(path.rglob("*"), reverse=True):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            item.rmdir()
    path.rmdir()
