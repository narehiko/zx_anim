# ZX Anim

<p align="center">
  <img src="preview/preview.png" width="400">
</p>

## Lock / Unlock State

<table>
  <tr>
    <th>Locked</th>
    <th>Unlocked</th>
  </tr>
  <tr>
    <td><img src="preview/locked.png" width="250"></td>
    <td><img src="preview/unlocked.png" width="250"></td>
  </tr>
</table>


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
