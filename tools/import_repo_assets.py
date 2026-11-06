"""StreetFighter2D-Game (Sujal V Kanchan, MIT lisansı) reposundaki çizimleri
oyunun kullanacağı biçime çevirir.

Kullanım:
    python tools/import_repo_assets.py <StreetFighter2D-Game klasörü>

Yaptıkları:
- Karakter karelerini Unity'deki ölçeğine (pixelsPerUnit) göre aynı boyuta getirir
- Kare sayısını azaltır, küçültür, yarı saydam gürültüyü temizler
- Her kare için ayak hizası, gövde kutusu ve vuruş noktasını meta.json'a yazar
- Arena arka planlarını JPEG olarak kaydeder
"""
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")

PX_PER_UNIT = 66.0          # 1 Unity birimi = 66 ekran pikseli (boy yaklaşık 300 px)
CHARS = {1: "jax", 2: "kaito", 3: "titus", 4: "daiki"}
ANIMS = {  # animasyon: hedef kare sayısı
    "Idle": 12, "Walk": 14, "JumpStart": 6, "JumpLoop": 10, "Land": 8,
    "Attack_1": 10, "Attack_2": 12, "Attack_3": 12, "Block": 8, "Hit": 12, "Knockout": 26,
}


def ppu(meta_path):
    try:
        with open(meta_path, encoding="utf-8") as f:
            m = re.search(r"spritePixelsToUnits:\s*([\d.]+)", f.read())
        return float(m.group(1)) if m else 100.0
    except OSError:
        return 100.0


def clean(im):
    a = np.array(im.convert("RGBA"))
    alpha = a[:, :, 3].astype(np.int32)
    alpha[alpha < 70] = 0
    a[:, :, 3] = alpha.astype(np.uint8)
    return Image.fromarray(a)


def solid_bbox(im, thr=160):
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > thr)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def reach_point(im, anchor_x):
    """Karakterin en öne (sağa) uzanan noktası: vuruş noktası."""
    a = np.array(im)[:, :, 3]
    cols = np.where((a > 160).any(axis=0))[0]
    if len(cols) == 0:
        return 0, 0
    x = int(cols.max())
    ys = np.where(a[:, x] > 160)[0]
    return x - anchor_x, int(ys.mean())


def import_chars(src):
    for num, cid in CHARS.items():
        base = os.path.join(src, "Assets", "Art", "Characters", f"Character{num}")
        dst = os.path.join(OUT, "sprites", cid)
        os.makedirs(dst, exist_ok=True)
        for old in glob.glob(os.path.join(dst, "*.png")):
            os.remove(old)
        meta = {"anims": {}}
        for anim, want in ANIMS.items():
            files = sorted(glob.glob(os.path.join(base, anim, "*.png")))
            if not files:
                continue
            scale = PX_PER_UNIT / ppu(files[0] + ".meta")
            n = len(files)
            pick = [files[round(i * (n - 1) / max(1, want - 1))] for i in range(min(want, n))]
            # yatay çapa: ilk karedeki gövdenin ortası (animasyon boyunca sabit)
            first = clean(Image.open(files[0]))
            fb = solid_bbox(first) or (0, 0, first.width, first.height)
            anchor_src = (fb[0] + fb[2]) / 2
            frames = []
            for i, f in enumerate(pick):
                im = clean(Image.open(f))
                bb = solid_bbox(im, 60)
                if bb is None:
                    continue
                pad = 4
                crop = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
                w, h = max(1, round(crop.width * scale)), max(1, round(crop.height * scale))
                small = crop.resize((w, h), Image.LANCZOS)
                # ekran koordinatı: çapa (ayak ortası) = (0, 0)
                ox = (max(0, bb[0] - pad) - anchor_src) * scale
                oy = -h
                body = solid_bbox(small, 200) or (0, 0, w, h)
                rx, ry = reach_point(small, -ox)
                name = f"{anim}_{i:02d}.png"
                small.save(os.path.join(dst, name), optimize=True)
                frames.append(dict(f=name, ox=round(ox, 1), oy=oy, w=w, h=h,
                                   body=[round(body[0] + ox, 1), body[1] + oy, round(body[2] + ox, 1), body[3] + oy],
                                   reach=[rx, ry + oy]))
            meta["anims"][anim] = frames
            print(cid, anim, len(frames), "kare")
        idle = meta["anims"]["Idle"][0]
        meta["height"] = idle["h"]
        meta["width"] = idle["body"][2] - idle["body"][0]
        with open(os.path.join(dst, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
        # karakter seçim portresi
        port = os.path.join(src, "Assets", "Art", "CharactersFiles", cid.capitalize(), f"{cid.capitalize()}.png")
        if os.path.exists(port):
            im = Image.open(port).convert("RGBA")
            im.thumbnail((420, 620), Image.LANCZOS)
            im.save(os.path.join(dst, "portrait.png"), optimize=True)


def import_stages(src):
    dst = os.path.join(OUT, "stages")
    os.makedirs(dst, exist_ok=True)
    for i in (1, 2, 3):
        p = os.path.join(src, "Assets", "Art", "Backgrounds", f"Stage{i}", f"Background Stage {i}.png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im = im.resize((1500, round(im.height * 1500 / im.width)), Image.LANCZOS)
            im.save(os.path.join(dst, f"stage{i}.jpg"), quality=88, optimize=True)
            print("arena", i)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    import_chars(sys.argv[1])
    import_stages(sys.argv[1])
    with open(os.path.join(sys.argv[1], "LICENSE"), encoding="utf-8") as f:
        lic = f.read()
    with open(os.path.join(OUT, "LICENSE-StreetFighter2D-Game.txt"), "w", encoding="utf-8") as f:
        f.write("Karakter ve arena çizimleri: https://github.com/sujalvk888/StreetFighter2D-Game\n\n" + lic)
