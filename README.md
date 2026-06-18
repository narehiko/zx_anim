# ZX Anim

ZX Anim is a lightweight keyboard-reactive character overlay for rhythm games
and livestreams. Ikuyo Kita is included as the default character, and custom
character packs can be imported from the Settings window.

![ZX Anim preview](preview/preview.gif)

## Features

- Global keyboard-reactive animation
- GIF import for quick character creation
- Custom character packs with any number of actions and PNG frames
- Optional WAV tap and hold sounds
- Transparent OBS Browser Source output
- Optional desktop preview with configurable size, lock, and background controls
- System tray controls
- Settings stored in `%APPDATA%\ZX Anim`
- Windows installer and portable release builds

## Run from Source

```powershell
python -m pip install -r requirements.txt
python zx_anim.py
```

## Controls

- `Q` and `W`: Default Ikuyo animation actions
- `Home`: Lock or unlock the preview position
- `Ctrl+Home`: Open Settings
- `Ctrl+G`: Change the desktop preview background
- Mouse drag: Move the unlocked preview
- Mouse wheel: Change animation speed
- System tray **Show Desktop Preview**: Open the local testing preview

Rapid alternating taps are visually rate-limited by the **Rapid tap
smoothing** setting. The default is `70 ms`; set it to `0` to restore direct
frame changes for every key event.

The desktop preview is hidden on startup by default. This does not affect the
OBS Browser Source. Use the system tray when you need to test the animation
locally.

## OBS Setup

1. Start ZX Anim.
2. Open the tray menu and select **Copy OBS Browser Source URL**.
3. In OBS, add a **Browser** source.
4. Paste the URL and set the source size to `585x427`.
5. Keep **Shutdown source when not visible** disabled.

The Browser Source has a transparent background and does not depend on OBS
Window Capture support for translucent Qt windows.

## Custom Characters

The easiest option is **Settings > Import GIF**. ZX Anim converts the GIF into
PNG frames and creates a responsive two-key character automatically.

Transparent GIFs are recommended for OBS Browser Source. Green-screen GIFs also
work if you prefer using a Chroma Key filter in OBS.

For advanced characters, create a folder with a `character.json` file and PNG
frames, then use **Settings > Import Character**.

```text
my-character/
  character.json
  actions/
    left/
      1.png
      2.png
    right/
      1.png
      2.png
```

Example manifest:

```json
{
  "id": "my-character",
  "name": "My Character",
  "canvas": {
    "width": 585,
    "height": 427
  },
  "default_action": "left",
  "actions": {
    "left": {
      "name": "Left Key",
      "frames": [
        "actions/left/1.png",
        "actions/left/2.png"
      ]
    },
    "right": {
      "name": "Right Key",
      "frames": [
        "actions/right/1.png",
        "actions/right/2.png"
      ]
    }
  }
}
```

Character IDs and action IDs may contain lowercase letters, numbers,
underscores, and hyphens.

## Build

Build the application folder with PyInstaller:

```powershell
pyinstaller --clean --noconfirm zx_anim.spec
```

Build the installer after installing Inno Setup:

```powershell
iscc installer/zx_anim.iss
```

The distributable installer is written to `installer/output`. The `dist`
directory is only a local build artifact and should not be committed or shared
as the primary installation method.

Pushing a tag such as `v3.0.0` runs the GitHub Actions release workflow, builds
the installer and portable ZIP, and uploads both to GitHub Releases.
