[app]
title = PushPulse
package.name = pushpulse
package.domain = org.aissa.pushpulse

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy==2.3.1,kivymd==1.2.0,plyer,pillow,pyjnius

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
orientation = portrait
fullscreen = 0

android.permissions = POST_NOTIFICATIONS,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED

android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

# هذا هو الإصلاح
p4a.branch = develop
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
