# ZX Anim

ZX Anim is a lightweight keyboard-reactive character overlay for rhythm games
and livestreams. Ikuyo Kita is included as the default character, and custom
character packs can be imported from the Settings window.

![ZX Anim preview](preview/preview.gif)

## Features

- Global keyboard-reactive animation
- Custom character packs with any number of actions and PNG frames
- Transparent OBS Browser Source output
- Movable desktop preview with lock and background controls
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

## OBS Setup

1. Start ZX Anim.
2. Open the tray menu and select **Copy OBS Browser Source URL**.
3. In OBS, add a **Browser** source.
4. Paste the URL and set the source size to `585x427`.
5. Keep **Shutdown source when not visible** disabled.

The Browser Source has a transparent background and does not depend on OBS
Window Capture support for translucent Qt windows.

## Custom Characters

Create a folder with a `character.json` file and PNG frames, then use
**Settings > Import Character**.

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

## Maintaining the README

Update this file whenever a change affects installation, controls, OBS setup,
character pack structure, or the development workflow.

For a normal feature update:

1. Update **Features** when user-visible behavior changes.
2. Update **Controls** when shortcuts or input behavior change.
3. Update **OBS Setup** when the capture workflow changes.
4. Update **Custom Characters** when the manifest format changes.
5. Update **Build** when dependencies or packaging commands change.
6. Replace `preview/preview.gif` when the interface or default animation
   changes significantly.

Keep the README focused on current behavior. Historical changes belong in the
GitHub Release notes rather than being appended to this file.

## Release Checklist

1. Update `zxanim/__init__.py` with the new semantic version.
2. Update the fallback `AppVersion` in `installer/zx_anim.iss`.
3. Update the README if user-facing behavior changed.
4. Run the tests and build:

   ```powershell
   python -m unittest discover -s tests
   pyinstaller --clean --noconfirm zx_anim.spec
   ```

5. Commit and push the changes.
6. Create and push a matching version tag:

   ```powershell
   git tag -a v3.0.0 -m "Release v3.0.0"
   git push origin main
   git push origin v3.0.0
   ```

The tag version is passed to Inno Setup automatically by the release workflow.
