"""Kanatix Arcade simgesi: Kanatix ortak logosu (marka/uret.py) + oyun kolu rozeti.

Çalıştırma: python marka/arcade.py
Üretir: assets/icon.png, assets/icon.ico, assets/logo_mark.png (menüde kullanılan kanat işareti)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uret  # noqa: E402

ROZET = "#D63A63"
# Oyun kolu: beyaz gövde, rozet renginde yön tuşu ve düğmeler
uret.GLYPH["oyun"] = (
    '<g fill="#FFFFFF"><rect x="-48" y="-24" width="96" height="44" rx="22"/>'
    '<circle cx="-30" cy="14" r="20"/><circle cx="30" cy="14" r="20"/></g>'
    f'<g fill="{ROZET}"><rect x="-38" y="-6" width="22" height="8" rx="2"/><rect x="-31" y="-13" width="8" height="22" rx="2"/>'
    '<circle cx="22" cy="-7" r="5.5"/><circle cx="33" cy="4" r="5.5"/></g>')

ARCADE = dict(bg1="#1E1A30", bg2="#0C0A14", rozet="oyun", rozet_renk=ROZET)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


def mark_svg(size=512):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="-256 -256 512 512"><defs>{uret.DEFS}</defs>
<g transform="scale(1.25)"><use href="#mark"/></g></svg>'''


if __name__ == "__main__":
    svg = uret.icon_svg(ARCADE["bg1"], ARCADE["bg2"], ARCADE["rozet"], ARCADE["rozet_renk"])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcade-icon.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    uret.png(svg, 512, os.path.join(ASSETS, "icon.png"))
    uret.ico(svg, os.path.join(ASSETS, "icon.ico"))
    uret.png(mark_svg(), 512, os.path.join(ASSETS, "logo_mark.png"))
    print("Kanatix Arcade simgesi üretildi")
