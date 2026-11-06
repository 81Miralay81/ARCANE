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
        if app.save.settings.get("update_attempt") == tag:
            # bu sürüme güncelleme daha önce denendi ama olmadı: döngüye girme
            app.update_phase = None
            app.update_status = f"Yeni sürüm {tag} kurulamadı. GitHub Releases sayfasından elle indir."
            app.save.settings["update_attempt"] = ""
            app.save.save()
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
        # PyInstaller tek dosya exe'de dosyayı kilitleyen asıl süreç üst süreçtir (bootloader).
        # PowerShell'e UTF-16 kodlu komut veriyoruz: kullanıcı klasöründe Türkçe harf olsa da yol bozulmaz.
        def q(x):
            return "'" + str(x).replace("'", "''") + "'"
        pids = ",".join(str(p) for p in {os.getpid(), os.getppid()})
        ps = (f"$exe={q(exe)}; $tmp={q(tmp)}; "
              f"foreach($p in @({pids})){{ while(Get-Process -Id $p -ErrorAction SilentlyContinue){{ Start-Sleep -Milliseconds 300 }} }}; "
              "$ok=$false; for($i=0; $i -lt 20; $i++){ try { Copy-Item -LiteralPath $tmp -Destination $exe -Force -ErrorAction Stop; "
              "$ok=$true; break } catch { Start-Sleep -Seconds 1 } }; "
              # kopyalanamadıysa eski sürümü değil, indirilen yeni sürümü aç (döngüye girmesin)
              "if($ok){ Start-Process -FilePath $exe } else { Start-Process -FilePath $tmp }")
        import base64
        enc = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-EncodedCommand", enc]
        st = app.save.settings
        st["update_attempt"] = tag
        app.save.save()
        app.update_phase = "restarting"
        subprocess.Popen(cmd, creationflags=0x08000000 | 0x00000008)  # pencere yok + bağımsız süreç
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
