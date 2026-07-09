# PushPulse - Mobile (Android) Version 💪📱

This is the Kivy/KivyMD rebuild of PushPulse, made to be packaged into an
Android APK with Buildozer. The core logic (training plan, storage,
statistics) is the same as the desktop version — only the interface was
rebuilt with mobile-native widgets.

## ⚠️ Important: why you can't just "convert" the Python file

Android does not run Tkinter/CustomTkinter apps. This folder is a full
rebuild using Kivy + KivyMD, which *can* be compiled into a real `.apk`.
Compiling that APK requires downloading the Android SDK/NDK (several GB,
from Google's servers) and running a full build — that has to happen on
a real machine or in the cloud, not inside this chat.

## The easiest way to get your APK (no setup on your side): GitHub Actions

1. Create a free GitHub account if you don't have one (github.com).
2. Create a new **public** repository (e.g. `pushpulse-app`).
3. Upload every file in this folder (including the hidden `.github` folder)
   to that repository — keep the same folder structure.
4. Go to the **Actions** tab of your repository. A workflow called
   "Build PushPulse APK" will run automatically (takes ~15-25 minutes the
   first time).
5. When it finishes (green check ✅), click on the workflow run, scroll to
   **Artifacts**, and download `PushPulse-APK`. Unzip it — inside is your
   `.apk` file.
6. Transfer the `.apk` to your phone (via USB, Telegram/WhatsApp to
   yourself, Google Drive, etc.) and open it.
7. Android will warn about "unknown source" apps — go to
   Settings → allow install from this source (browser/file manager) → Install.

## Alternative: build it yourself with Buildozer (Linux/WSL only)

```bash
pip install buildozer cython
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf \
    libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev
buildozer android debug
```

The finished APK will appear in `bin/pushpulse-1.0-arm64-v8a-debug.apk`.
Buildozer is **not supported on Windows or macOS directly** — use WSL2 on
Windows, or a Linux VM/Docker container on macOS.

## Honest limitations of this mobile build

- **Reminders fire while the app is open** (or kept alive in the
  background by your phone's battery settings). True "notify me even
  when the app is fully closed" requires a native Android background
  Service — a bigger project beyond a single Kivy app. This matches how
  most simple habit-tracker apps built this way behave out of the box.
- First install will ask for notification permission (Android 13+) —
  accept it so reminders can show.
- This is a **debug** APK (fine for personal use on your own phone).
  Publishing to the Play Store requires a signed **release** build and a
  Google Play Developer account.

## Project structure

| File | Responsibility |
|---|---|
| `main.py` | KivyMD UI: Home / Statistics / Calendar / Settings tabs |
| `notifications.py` | Reminder scheduling (Kivy Clock-based) |
| `storage.py` | JSON persistence + training plan logic |
| `settings_data.py` | User preferences |
| `statistics.py` | Streaks, averages, completion rate, CSV export |
| `buildozer.spec` | Android packaging configuration |
| `.github/workflows/build.yml` | Cloud APK build (GitHub Actions) |
