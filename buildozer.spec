[app]
title = Kanatix Arcade
package.name = kanatixarcade
package.domain = com.kanatix
source.dir = .
source.include_exts = py,png,jpg,ttf,json,txt
source.exclude_dirs = tools,.github,build,dist,bin,.buildozer,__pycache__,p4a-recipes
version.regex = VERSION = "(.*)"
version.filename = %(source.dir)s/engine/core.py
requirements = python3,pygame,pyjnius,certifi
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
# Python 3.11 kullanan kararlı python-for-android sürümü + pygame 2.6.1 tarifi
p4a.branch = v2024.01.21
p4a.local_recipes = ./p4a-recipes
android.ndk = 25b

[buildozer]
log_level = 2
warn_on_root = 0
