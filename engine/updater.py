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


def _update_dir():
    root = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    d = os.path.join(root, "KanatixArcade", "guncelleme")
    os.makedirs(d, exist_ok=True)
    return d


def _install_path(app):
    """Oyunun asıl exe yolu. Güncelleme klasöründen çalışıyorsak kayıtlı yolu kullan."""
    exe = os.path.abspath(sys.executable)
    st = app.save.settings
    upd = os.path.abspath(_update_dir()).lower()
    tmp = os.path.abspath(tempfile.gettempdir()).lower()
    if not exe.lower().startswith(upd) and not exe.lower().startswith(tmp):
        st["install_path"] = exe
        app.save.save()
        return exe
    return st.get("install_path") or exe


def _worker(app):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "KanatixArcade-Updater"})
        with urllib.request.urlopen(req, timeout=8) as r:
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
            app.update_phase = None
            app.update_status = f"Yeni sürüm {tag} kurulamadı. GitHub Releases sayfasından elle indir."
            app.save.settings["update_attempt"] = ""
            app.save.save()
            return
        target = _install_path(app)
        app.update_tag = tag
        app.update_phase = "downloading"
        app.update_progress = 0.0
        # her sürüm için ayrı dosya: çalışan eski dosyanın üzerine yazmaya çalışmayız
        new = os.path.join(_update_dir(), f"KanatixArcade_{tag}.exe")
        total = asset.get("size") or 1
        if not (os.path.exists(new) and os.path.getsize(new) == total):
            part = new + ".part"
            req = urllib.request.Request(asset["browser_download_url"], headers={"User-Agent": "KanatixArcade-Updater"})
            done = 0
            with urllib.request.urlopen(req, timeout=60) as r, open(part, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    app.update_progress = min(1.0, done / total)
            if os.path.getsize(part) < total:
                raise IOError("indirme eksik kaldı")
            os.replace(part, new)
        app.update_progress = 1.0
        log = os.path.join(_update_dir(), "son_hata.txt")

        def q(x):
            return "'" + str(x).replace("'", "''") + "'"
        pids = ",".join(str(p) for p in {os.getpid(), os.getppid()})
        # PowerShell'e UTF-16 kodlu komut: Türkçe harfli klasör yolları bozulmaz.
        ps = (f"$exe={q(target)}; $new={q(new)}; $log={q(log)}; "
              f"foreach($p in @({pids})){{ $n=0; while((Get-Process -Id $p -ErrorAction SilentlyContinue) -and $n -lt 60)"
              "{ Start-Sleep -Milliseconds 300; $n++ } }; "
              "$ok=$false; $err=''; for($i=0; $i -lt 25; $i++){ try { Copy-Item -LiteralPath $new -Destination $exe "
              "-Force -ErrorAction Stop; $ok=$true; break } catch { $err=$_.Exception.Message; Start-Sleep -Seconds 1 } }; "
              "if($ok){ Start-Process -FilePath $exe } else { Set-Content -LiteralPath $log -Value $err -Encoding UTF8; "
              "Start-Process -FilePath $new }")
        import base64
        enc = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-EncodedCommand", enc]
        st = app.save.settings
        st["update_attempt"] = tag
        app.save.save()
        app.update_phase = "restarting"
        subprocess.Popen(cmd, creationflags=0x08000000 | 0x00000008)
        app.running = False
    except Exception as e:
        app.update_phase = None
        app.update_status = f"Güncelleme yapılamadı: {e}"[:110]


def _report_last_error(app):
    try:
        log = os.path.join(_update_dir(), "son_hata.txt")
        if os.path.exists(log):
            with open(log, encoding="utf-8-sig") as f:
                msg = f.read().strip()
            os.remove(log)
            app.update_status = ("Önceki güncelleme dosyayı değiştiremedi: " + msg)[:110]
    except Exception:
        pass


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
    _report_last_error(app)
    app.update_phase = "checking"
    threading.Thread(target=_worker, args=(app,), daemon=True).start()
