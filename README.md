# ZX Anim

![ZX Anim Preview](preview/preview.gif)

**ZX Anim** is a lightweight animation overlay for **osu!**.
The animation reacts **in real time** to your **Z / X key inputs**, making streams and taps visually synced on screen.

---

## Lock / Unlock State

![Locked](preview/locked.png)
![Unlocked](preview/unlocked.png)

---

## Features

* 🎮 Responsive ZX animation synced with Z / X key presses
* 🔒 Lock / Unlock window position (**HOME** key)
* 🖼️ Custom animation frames (PNG)
* 🔊 Custom lock / unlock sounds
* 🎥 OBS / screen recording compatible
* 🪟 Transparent background overlay
* 💾 Window position saved automatically

---

## How to Use

### Option 1 — Use the Executable (Recommended)

1. Download the project from GitHub.
2. Extract the ZIP file.
3. Open the extracted folder.
4. Run **`zx_anim.exe`**.

> No Python installation is required for the executable version.

---

### Option 2 — Build from Source (Developer)

#### 1. Download or clone the repository

```bash
git clone https://github.com/USERNAME/zx_anim.git
cd zx_anim
```

Or download the ZIP file and extract it.

#### 2. Install dependencies

```bash
pip install -r requirements.txt
```

#### 3. Build the executable

```bash
pyinstaller ^
--onefile ^
--noconsole ^
--icon=icon.ico ^
--add-data "frames;frames" ^
--add-data "lock.wav;." ^
--add-data "unlock.wav;." ^
zx_anim.py
```

The executable will be generated in:

```
dist/zx_anim.exe
```

---

## Controls

* **Z / X** → Advance animation frame
* **HOME** → Lock / Unlock window position
* **Mouse Drag** → Move window (when unlocked)

---

## Notes

* Designed as an overlay (frameless & transparent)
* Works with OBS Window Capture
* Best used in borderless or fullscreen gameplay
