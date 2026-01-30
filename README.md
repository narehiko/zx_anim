# ZX Anim

![ZX Anim Preview](preview/preview.png)

## Lock / Unlock State

**Locked**
![Locked](preview/locked.png)

**Unlocked**
![Unlocked](preview/unlocked.png)

A lightweight ZX animation overlay for osu!  
The animation reacts in real time to Z and X key inputs.

## Features
- Responsive ZX animation synced with key presses
- Lock / Unlock window position (HOME key)
- Custom animation frames and sounds
- OBS / screen recording compatible

## Build
```bash
pip install -r requirements.txt
pyinstaller --onefile --noconsole zx_anim.py
