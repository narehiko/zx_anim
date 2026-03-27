# ZX Anim (v2.1)

![ZX Anim Preview](preview/preview.gif)

**ZX Anim** is a lightweight, interactive animation overlay for rhythm games like **osu!**.
The animation reacts **in real time** to your keyboard inputs, making streams and taps visually synced on screen.

---

## 🌟 New in v2.1
* 🎨 **Chroma Key / Green Screen Mode:** Easily switch the background to bright green or magenta for compatibility with TikTok Live Studio and other streaming apps.
* ⚙️ **Dynamic Keybind Settings GUI:** Change your active keys directly from the System Tray (no JSON editing required).
* 🗕 **System Tray Integration:** Runs cleanly in the background without cluttering your Taskbar.
* 📉 **Optimized Engine:** Rebuilt with an event-driven architecture for zero-lag input detection and smooth hold-key looping.

## Features

* 🎮 Responsive animation synced with your custom key presses
* 🖼️ Custom animation frames (PNG)
* 🔒 Lock / Unlock window position
* 🔊 Custom lock / unlock sounds
* 🎥 OBS & TikTok Live Studio compatible
* 💾 Auto-saves window position, speed, and settings automatically

---

## How to Use

#### 1. Download or clone the repository
Bash: git clone [https://github.com/USERNAME/zx_anim.git](https://github.com/USERNAME/zx_anim.git)
cd zx_anim
(Make sure to run pip install -r requirements.txt if running from source)

#### 2. Run the App
Double click zx_anim.exe (if you downloaded the release) or run python zx_anim.py.
The app will appear as an overlay and an icon will be placed in your System Tray (bottom right corner of Windows).

#### 3. Build the Executable (For Developers)
To compile the app into a single standalone .exe that includes the tray icon and all assets, run:

Bash: 
pyinstaller --onefile --noconsole --icon=icon.ico --add-data "frames;frames" --add-data "lock.wav;." --add-data "unlock.wav;." --add-data "icon.ico;." zx_anim.py

## Controls & Shortcuts
* Custom Keys (Default: Q / W) → Advance animation frame

* HOME → Lock / Unlock window position

* Ctrl + HOME → Open Settings / Keybind GUI

* Ctrl + G → Toggle Background Color (Transparent → Green Screen → Pink Screen)

* Mouse Drag → Move window (when unlocked)

* Mouse Scroll → Adjust animation frame speed

* Right-Click System Tray Icon → Access menus or Quit

## 🎥 Streaming Guide (OBS & TikTok Live Studio)
If you get a Black Screen when capturing the application, follow these steps:

# For OBS Studio:
1. Add a Window Capture source and select zx_anim.exe.
2. In the capture properties, change the Capture Method from "Automatic" to "Windows 10 (1903 and up)". The background will instantly become transparent.

# For TikTok Live Studio (or apps without Alpha Channel support):
1. Press Ctrl + G while the overlay is focused to change the background to Green Screen.
2. Add a Window Capture in your streaming software.
3. Apply a Chroma Key (Kunci Warna) filter/effect to the capture and select Green. The background will disappear, leaving only your character.