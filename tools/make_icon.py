"""Kanatix ikonunu üretir: assets/icon.png ve assets/icon.ico"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
pygame.init()
from engine.core import draw_kanatix_logo, vgradient
S = 256
surf = pygame.Surface((S * 2, S * 2), pygame.SRCALPHA)
bg = vgradient(S * 2, S * 2, (40, 14, 70), (120, 20, 70))
mask = pygame.Surface((S * 2, S * 2), pygame.SRCALPHA)
pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=100)
bg = bg.convert_alpha() if pygame.display.get_init() and pygame.display.get_surface() else bg
tmp = pygame.Surface((S * 2, S * 2), pygame.SRCALPHA)
tmp.blit(bg, (0, 0))
tmp.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
surf.blit(tmp, (0, 0))
draw_kanatix_logo(surf, (S - 30, S), 3.3)
icon = pygame.transform.smoothscale(surf, (S, S))
os.makedirs("assets", exist_ok=True)
pygame.image.save(icon, "assets/icon.png")
try:
    from PIL import Image
    Image.open("assets/icon.png").save("assets/icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
except Exception as e:
    print("ico oluşturulamadı:", e)
print("ikon hazır")
