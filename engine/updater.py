"""Zorunlu otomatik güncelleme (yalnızca Windows .exe sürümünde çalışır).

Açılışta GitHub'daki son sürümü (Releases) kontrol eder. Yeni sürüm varsa
.exe dosyasını indirir, oyunu kapatıp yeni sürümle yeniden başlatır.
Repo private ise GitHub herkese açık sürüm bilgisi vermez, kontrol sessizce atlanır.
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request

from engine.core import VERSION

GITHUB_REPO = "81Miralay81/ARCANE"
ASSET_NAME = "KanatixArcade.exe"


def _ver(v):
    v = v.lstrip("vV")
    out = []
    for p in v.split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


def _worker(app):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "KanatixArcade-Updater"})
        with urllib.request.urlopen(req, timeout=6) as r:
            info = json.loads(r.read().decode("utf-8"))
        tag = info.get("tag_name", "")
        if _ver(tag) <= _ver(VERSION):
            return
        asset = next((a for a in info.get("assets", []) if a.get("name") == ASSET_NAME), None)
        if not asset:
            return
        app.update_status = f"Yeni sürüm {tag} indiriliyor..."
        tmp = os.path.join(tempfile.gettempdir(), "KanatixArcade_new.exe")
        req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "KanatixArcade-Updater"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
        exe = sys.executable
        bat = os.path.join(tempfile.gettempdir(), "kanatix_update.bat")
        with open(bat, "w", encoding="utf-8") as f:
            f.write("@echo off\r\n"
                    "timeout /t 2 /nobreak >nul\r\n"
                    f'copy /y "{tmp}" "{exe}" >nul\r\n'
                    f'start "" "{exe}"\r\n'
                    'del "%~f0"\r\n')
        app.update_status = f"Güncelleniyor: {tag}. Oyun yeniden başlatılacak..."
        subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
        app.running = False
    except Exception:
        app.update_status = None


APK_NAME = "KanatixArcade.apk"


def _android_worker(app):
    """Telefonda: yeni APK varsa zorunlu güncelleme ekranı gösterilir."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "KanatixArcade-Updater"})
        with urllib.request.urlopen(req, timeout=8) as r:
            info = json.loads(r.read().decode("utf-8"))
        tag = info.get("tag_name", "")
        if _ver(tag) <= _ver(VERSION):
            return
        asset = next((a for a in info.get("assets", []) if a.get("name") == APK_NAME), None)
        if asset:
            app.forced_update = (tag, asset["browser_download_url"])
    except Exception:
        pass


def open_url(url):
    try:
        from jnius import autoclass
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        activity.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        return
    except Exception:
        pass
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        pass


def check_update_async(app):
    app.update_status = None
    app.forced_update = None
    if getattr(app, "android", False):
        threading.Thread(target=_android_worker, args=(app,), daemon=True).start()
        return
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    threading.Thread(target=_worker, args=(app,), daemon=True).start()
