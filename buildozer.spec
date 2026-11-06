[app]
title = Kanatix Arcade
package.name = kanatixarcade
package.domain = com.kanatix
source.dir = .
source.include_exts = py,png,jpg,ttf,json,txt
source.exclude_dirs = tools,.github,build,dist,bin,.buildozer,__pycache__
version.regex = VERSION = "(.*)"
version.filename = %(source.dir)s/engine/core.py
requirements = python3,pygame,openssl,pyjnius
orientation = landscape
fullscreen = 1
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/icon.png
android.presplash_color = #1a0a2e
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0
