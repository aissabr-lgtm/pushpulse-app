[app]
title = PushPulse
package.name = pushpulse
package.domain = org.aissa.pushpulse

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

# Pure-Python deps first, then Kivy/KivyMD, then plyer for notifications/vibration
requirements = python3,kivy==2.3.1,kivymd==1.2.0,plyer,pillow

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
orientation = portrait
fullscreen = 0

# Android permissions: notifications (Android 13+), vibration, and keeping
# the reminder checker alive a little more reliably while the app is open.
android.permissions = POST_NOTIFICATIONS,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED

android.api = 34
android.minapi = 23
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
