"""Kodla çizilen, paralaks kayan, ışıklandırılmış dövüş arenaları."""
import math
import random

import pygame

from engine.core import W, H, blit_glow, lerp_color, shade, text, vgradient
from games.fighter.fighter import GROUND

STAGE_W = 1900
FLOOR_TOP = GROUND - 34


def _layer_w(k):
    return int(W + (STAGE_W - W) * k)


def _ss_layer(w, h, painter, ss=2):
    """Katmanı 2 kat büyük çizip yumuşatarak küçült (pürüzsüz kenarlar)."""
    big = pygame.Surface((w * ss, h * ss), pygame.SRCALPHA)
    painter(big, ss)
    return pygame.transform.smoothscale(big, (w, h))


def _soft_ellipse(surf, color, rect, alpha):
    g = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    steps = 8
    for i in range(steps):
        k = i / steps
        r = pygame.Rect(0, 0, rect[2] * (1 - k * 0.6), rect[3] * (1 - k * 0.6))
        r.center = (rect[2] // 2, rect[3] // 2)
        pygame.draw.ellipse(g, color + (int(alpha / steps * 1.6),), r)
    surf.blit(g, (rect[0], rect[1]))


def _vignette():
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(40):
        k = i / 40
        a = int(150 * (1 - k) ** 2.2)
        pygame.draw.rect(v, (0, 0, 0, a), (int(k * 260), int(k * 150), W - int(k * 520), H - int(k * 300)), 8)
    return pygame.transform.smoothscale(pygame.transform.smoothscale(v, (W // 8, H // 8)), (W, H))


_VIG = None


class Stage:
    name = ""
    music = "fight"

    def __init__(self):
        global _VIG
        self.t = 0.0
        self.excite = 0.0
        if _VIG is None:
            _VIG = _vignette()
        self.build()

    def build(self):
        pass

    def update(self, dt):
        self.t += dt
        self.excite = max(0.0, self.excite - dt * 0.5)

    def blit_layer(self, surf, layer, k, camx, y=0):
        surf.blit(layer, (-int(camx * k), y))

    def draw_tiles(self, surf, camx, c1, c2, line, rows=6, tile=130, reflect=None):
        """Perspektifli karo zemin."""
        top = FLOOR_TOP
        pygame.draw.rect(surf, c1, (0, top, W, H - top))
        vx = W / 2
        ys = [top + (H - top) * ((i / rows) ** 1.6) for i in range(rows + 1)]
        spread_top, spread_bot = 1.0, 2.8
        n0 = int((camx * 1.0) // tile)
        frac = (camx * 1.0) % tile
        for r in range(rows):
            y0, y1 = ys[r], ys[r + 1]
            k0 = spread_top + (spread_bot - spread_top) * ((y0 - top) / (H - top))
            k1 = spread_top + (spread_bot - spread_top) * ((y1 - top) / (H - top))
            for i in range(-9, 10):
                xa = i * tile - frac
                xb = xa + tile
                p = [(vx + xa * k0, y0), (vx + xb * k0, y0), (vx + xb * k1, y1), (vx + xa * k1, y1)]
                if p[1][0] < -50 and p[2][0] < -50 or p[0][0] > W + 50 and p[3][0] > W + 50:
                    continue
                col = c1 if (i + n0 + r) % 2 == 0 else c2
                col = lerp_color(col, shade(col, 1.18), r / rows)
                pygame.draw.polygon(surf, col, p)
                pygame.draw.lines(surf, line, True, p, 2)
        # ufuk çizgisinde parlama
        g = pygame.Surface((W, 60), pygame.SRCALPHA)
        for i in range(60):
            pygame.draw.line(g, (0, 0, 0, int(110 * (1 - i / 60) ** 2)), (0, i), (W, i))
        surf.blit(g, (0, top))
        if reflect:
            r = pygame.Surface((W, H - top), pygame.SRCALPHA)
            r.fill(reflect)
            surf.blit(r, (0, top))

    def draw_back(self, surf, camx):
        pass

    def draw_front(self, surf, camx):
        surf.blit(_VIG, (0, 0))


# ============================================================================ resimli arenalar
class ImageStage(Stage):
    """StreetFighter2D-Game reposundan (MIT) alınan boyalı arka planlar + canlı efektler."""
    file = ""
    effect = "embers"
    tint = (255, 140, 60)

    def build(self):
        from engine.core import resource_path
        rnd = random.Random(self.file)
        try:
            img = pygame.image.load(resource_path("assets", "stages", self.file)).convert()
        except Exception:
            img = pygame.Surface((1500, 844))
            img.fill((30, 20, 40))
        h = 790
        w = int(img.get_width() * h / img.get_height())
        self.bg = pygame.transform.smoothscale(img, (w, h))
        self.k = (w - W) / max(1, STAGE_W - W)
        self.parts = [[rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0.3, 1.0)] for _ in range(90)]
        self.crowd = None

    def draw_back(self, surf, camx):
        surf.blit(self.bg, (-int(camx * self.k), -40))
        t = self.t
        if self.effect == "embers":
            for p in self.parts:
                p[1] -= 0.8 * p[2]
                p[0] += math.sin(t * 2 + p[2] * 9) * 0.5
                if p[1] < -10:
                    p[1] = H + 10
                    p[0] = random.uniform(0, W)
                r = 2 + int(p[2] * 2)
                blit_glow(surf, (int(p[0]), int(p[1])), r * 4, (int(120 * p[2]), int(50 * p[2]), 10), 1.0)
                pygame.draw.circle(surf, (255, 190, 90), (int(p[0]), int(p[1])), r)
            for tx in (0.18, 0.82):
                x = int(W * tx - camx * self.k * 0.2)
                blit_glow(surf, (x, 470), 160 + int(math.sin(t * 9 + tx * 10) * 12), (90, 40, 10), 1.0)
        elif self.effect == "rain":
            for p in self.parts:
                p[1] += 16 * p[2] + 6
                p[0] -= 3 * p[2]
                if p[1] > H:
                    p[1] = random.uniform(-80, 0)
                    p[0] = random.uniform(0, W + 100)
                c = (int(120 + 80 * p[2]), int(140 + 80 * p[2]), 200)
                pygame.draw.line(surf, c, (p[0], p[1]), (p[0] - 4 * p[2], p[1] - 22 * p[2]), 1)
            # neon titremesi
            if int(t * 7) % 23 == 0:
                fl = pygame.Surface((W, H), pygame.SRCALPHA)
                fl.fill(self.tint + (18,))
                surf.blit(fl, (0, 0))
        g = pygame.Surface((W, 140), pygame.SRCALPHA)
        for i in range(140):
            pygame.draw.line(g, (0, 0, 0, int(120 * (i / 140) ** 1.5)), (0, i), (W, i))
        surf.blit(g, (0, H - 140))
        # zemin parlaması (yansıma)
        gl = pygame.Surface((W, 60), pygame.SRCALPHA)
        for i in range(60):
            pygame.draw.line(gl, self.tint + (int(30 * (1 - i / 60)),), (0, i), (W, i))
        surf.blit(gl, (0, FLOOR_TOP + 20))


class FortressStage(ImageStage):
    name = "Ejder Kalesi"
    file = "stage1.jpg"
    effect = "embers"
    tint = (255, 140, 60)


class RooftopStage(ImageStage):
    name = "Neon Çatı"
    file = "stage2.jpg"
    effect = "rain"
    tint = (255, 60, 120)


class MetroStage(ImageStage):
    name = "Gece Metrosu"
    file = "stage3.jpg"
    effect = "rain"
    tint = (90, 160, 255)


STAGES = [FortressStage, RooftopStage, MetroStage]
