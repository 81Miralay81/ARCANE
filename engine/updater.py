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
        with urllib.request.urlopen(req, timeout=5) as r:
            info = json.loads(r.read().decode("utf-8"))
        tag = info.get("tag_name", "")
        if _ver(tag) <= _ver(VERSION):
            app.update_phase = None
            return
        asset = next((a for a in info.get("assets", []) if a.get("name") == ASSET_NAME), None)
        if not asset:
            app.update_phase = None
            return
        app.update_tag = tag
        app.update_phase = "downloading"
        app.update_progress = 0.0
        tmp = os.path.join(tempfile.gettempdir(), "KanatixArcade_new.exe")
        req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "KanatixArcade-Updater"})
        total = asset.get("size") or 1
        done = 0
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                app.update_progress = min(1.0, done / total)
        if os.path.getsize(tmp) < total * 0.98:
            raise IOError("eksik indirme")
        exe = sys.executable
        bat = os.path.join(tempfile.gettempdir(), "kanatix_update.bat")
        with open(bat, "w", encoding="utf-8") as f:
            # eski exe kapanana kadar dene, sonra yenisini başlat
            f.write("@echo off\r\n"
                    "set n=0\r\n"
                    ":dene\r\n"
                    "timeout /t 1 /nobreak >nul\r\n"
                    f'copy /y "{tmp}" "{exe}" >nul 2>&1\r\n'
                    "if errorlevel 1 (set /a n+=1 & if %n% lss 20 goto dene)\r\n"
                    f'start "" "{exe}"\r\n'
                    'del "%~f0"\r\n')
        app.update_phase = "restarting"
        subprocess.Popen(["cmd", "/c", bat], creationflags=0x08000000)
        app.running = False
    except Exception:
        app.update_phase = None


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
    app.update_phase = None
    app.update_progress = 0.0
    if getattr(app, "android", False):
        threading.Thread(target=_android_worker, args=(app,), daemon=True).start()
        return
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return
    app.update_phase = "checking"
    threading.Thread(target=_worker, args=(app,), daemon=True).start()
