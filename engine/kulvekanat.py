"""Kül ve Kanat'ı Arcade'den kurma ve açma.

Windows: Arcade açılınca Kül ve Kanat arka planda indirilir ve kurulur
(%LOCALAPPDATA%\\Kanatix\\KulVeKanat), yeni sürüm çıkınca kendiliğinden güncellenir,
masaüstüne kısayol konur. Menüden seçince oyun açılır.
Android: yüklüyse doğrudan açılır; değilse APK indirmesi başlatılır (Android, bir uygulamanın
başka bir uygulamayı sessizce kurmasına izin vermez; "Yükle"ye kullanıcı basar).
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request

DEPO = "81Miralay81/KulVeKanat"
PAKET = "com.kanatix.kulvekanat"
SAYFA = f"https://github.com/{DEPO}/releases/latest"
APK = f"https://github.com/{DEPO}/releases/latest/download/KulVeKanat.apk"

durum = "bekliyor"      # bekliyor, kontrol, indiriliyor, hazir, yok, hata
ilerleme = 0.0
surum = ""
_kilit = threading.Lock()
_calisiyor = False


def android_mi():
    return "ANDROID_ARGUMENT" in os.environ or hasattr(sys, "getandroidapilevel")


def _klasor():
    kok = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    d = os.path.join(kok, "Kanatix", "KulVeKanat")
    os.makedirs(d, exist_ok=True)
    return d


def exe_yolu():
    return os.path.join(_klasor(), "KulVeKanat.exe")


def _kurulu_surum():
    try:
        with open(os.path.join(_klasor(), "surum.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _sayi(v):
    out = []
    for p in v.lstrip("vV").split("."):
        try:
            out.append(int(p))
        except ValueError:
            out.append(0)
    return tuple(out)


def _kisayol(hedef):
    """Masaüstüne 'Kül ve Kanat' kısayolu (bir kez)."""
    try:
        script = (
            "$s=(New-Object -ComObject WScript.Shell);"
            "$d=[Environment]::GetFolderPath('Desktop');"
            f"$l=$s.CreateShortcut((Join-Path $d 'Kül ve Kanat.lnk'));$l.TargetPath='{hedef}';"
            f"$l.WorkingDirectory='{os.path.dirname(hedef)}';$l.Save()")
        import base64
        enc = base64.b64encode(script.encode("utf-16-le")).decode()
        subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-EncodedCommand", enc],
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        pass


def _isci():
    global durum, ilerleme, surum, _calisiyor
    try:
        from engine.updater import _open
        durum = "kontrol"
        req = urllib.request.Request(f"https://api.github.com/repos/{DEPO}/releases/latest",
                                     headers={"User-Agent": "KanatixArcade-KulVeKanat"})
        with _open(req, 10) as r:
            bilgi = json.loads(r.read().decode("utf-8"))
        etiket = bilgi.get("tag_name", "")
        surum = etiket.lstrip("v")
        kurulu = _kurulu_surum()
        exe = exe_yolu()
        if os.path.exists(exe) and kurulu and _sayi(kurulu) >= _sayi(etiket):
            durum = "hazir"
            return
        varlik = next((a for a in bilgi.get("assets", []) if a.get("name") == "KulVeKanat.exe"), None)
        if not varlik:
            durum = "hazir" if os.path.exists(exe) else "yok"
            return
        durum = "indiriliyor"
        ilerleme = 0.0
        gecici = exe + ".indiriliyor"
        req = urllib.request.Request(varlik["browser_download_url"], headers={"User-Agent": "KanatixArcade-KulVeKanat"})
        with _open(req, 30) as r, open(gecici, "wb") as f:
            toplam = int(r.headers.get("Content-Length") or varlik.get("size") or 0)
            alinan = 0
            while True:
                parca = r.read(256 * 1024)
                if not parca:
                    break
                f.write(parca)
                alinan += len(parca)
                if toplam:
                    ilerleme = alinan / toplam
        ilk_kurulum = not os.path.exists(exe)
        try:
            os.replace(gecici, exe)
        except OSError:
            # Kül ve Kanat şu an açıksa dosya kilitli: bir sonraki açılışta tekrar denenir
            durum = "hazir"
            return
        with open(os.path.join(_klasor(), "surum.txt"), "w", encoding="utf-8") as f:
            f.write(surum)
        if ilk_kurulum:
            _kisayol(exe)
        durum = "hazir"
    except Exception as e:
        print("Kül ve Kanat indirilemedi:", e)
        durum = "hazir" if os.path.exists(exe_yolu()) else "hata"
    finally:
        _calisiyor = False


def baslat():
    """Arcade açılırken çağrılır: Windows'ta arka planda kur / güncelle."""
    global _calisiyor
    if android_mi() or not sys.platform.startswith("win"):
        return
    with _kilit:
        if _calisiyor:
            return
        _calisiyor = True
    threading.Thread(target=_isci, daemon=True).start()


def _android_yuklu_mu():
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        pm = activity.getPackageManager()
        return pm.getLaunchIntentForPackage(PAKET)
    except Exception:
        return None


def alt_yazi():
    if android_mi():
        return "Yüklü — açmak için seç" if _android_yuklu_mu() else "Yeni aksiyon RPG — seçince indirilir, sonra Yükle'ye bas"
    if not sys.platform.startswith("win"):
        return "Yeni aksiyon RPG — indirme sayfasını açar"
    if durum == "indiriliyor":
        return f"İndiriliyor... %{int(ilerleme * 100)}"
    if durum == "kontrol":
        return "Sürüm kontrol ediliyor..."
    if durum == "hazir":
        return f"Kuruldu {('v' + surum) if surum else ''} — açmak için seç"
    if durum == "hata":
        return "İndirilemedi — tekrar denemek için seç"
    return "Yeni aksiyon RPG: seviye, yetenek, eşya, boss"


def ac():
    """Menüden seçilince. Döndürdüğü metin ekranda kısa mesaj olarak gösterilir."""
    from engine.updater import open_url
    if android_mi():
        niyet = _android_yuklu_mu()
        if niyet is not None:
            try:
                from jnius import autoclass
                autoclass("org.kivy.android.PythonActivity").mActivity.startActivity(niyet)
                return "Kül ve Kanat açılıyor..."
            except Exception:
                pass
        open_url(APK)
        return "İndirme başladı: bitince bildirimden açıp Yükle'ye bas"
    if not sys.platform.startswith("win"):
        open_url(SAYFA)
        return "İndirme sayfası açıldı"
    exe = exe_yolu()
    if durum == "indiriliyor":
        return f"Kül ve Kanat iniyor (%{int(ilerleme * 100)}), az kaldı"
    if os.path.exists(exe):
        try:
            subprocess.Popen([exe], cwd=os.path.dirname(exe),
                             creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
            return "Kül ve Kanat açılıyor..."
        except Exception as e:
            return f"Açılamadı: {e}"
    baslat()
    return "Kül ve Kanat indiriliyor, birazdan hazır"
