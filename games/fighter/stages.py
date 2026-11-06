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


class Crowd:
    """Arka plandaki tezahürat yapan seyirciler."""

    def __init__(self, seed, n, y, color_base, palette, spacing=36):
        rnd = random.Random(seed)
        self.people = []
        x = -40
        while x < _layer_w(0.78) + 40:
            self.people.append(dict(x=x, h=rnd.uniform(0.85, 1.15), c=rnd.choice(palette), ph=rnd.uniform(0, 6.28),
                                    sp=rnd.uniform(5, 9), arms=rnd.random() < 0.35, row=rnd.randint(0, 1)))
            x += rnd.randint(spacing - 10, spacing + 10)
        self.y = y
        self.base = color_base

    def draw(self, surf, camx, t, k=0.78, excite=0.0):
        off = -camx * k
        for p in sorted(self.people, key=lambda q: q["row"]):
            x = p["x"] + off + p["row"] * 14
            if x < -40 or x > W + 40:
                continue
            bob = abs(math.sin(t * p["sp"] * (0.5 + excite) + p["ph"])) * (3 + 6 * excite)
            y = self.y - p["row"] * 10 - bob
            h = 46 * p["h"]
            c = lerp_color(self.base, p["c"], 0.35 - p["row"] * 0.12)
            pygame.draw.rect(surf, c, (x - 11, y - h * 0.6, 22, h * 0.6 + 30), border_radius=9)
            pygame.draw.circle(surf, c, (int(x), int(y - h * 0.6 - 9)), 9)
            if p["arms"] or excite > 0.5:
                a = math.sin(t * p["sp"] + p["ph"]) * 0.4
                pygame.draw.line(surf, c, (x - 8, y - h * 0.45), (x - 16 + a * 10, y - h * 0.95), 6)
                pygame.draw.line(surf, c, (x + 8, y - h * 0.45), (x + 16 - a * 10, y - h * 0.95), 6)


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


# ============================================================================ Boğaz
class BosphorusStage(Stage):
    name = "Boğaz Gün Batımı"

    def build(self):
        rnd = random.Random(3)
        self.sky = vgradient(W, H, (34, 18, 64), (250, 132, 72))
        # bulutlar
        self.clouds = []
        for _ in range(9):
            self.clouds.append((rnd.uniform(0, W + 600), rnd.uniform(40, 260), rnd.uniform(160, 420), rnd.uniform(0.3, 1.0)))
        fw = _layer_w(0.22)

        def far_paint(s, k):
            col = (78, 42, 86, 255)
            x = 0
            while x < fw:
                w = rnd.randint(40, 120)
                h = rnd.randint(20, 70)
                pygame.draw.rect(s, col, (x * k, (480 - h) * k, w * k, (h + 80) * k))
                x += w + rnd.randint(-5, 20)
            # camiler (kubbe + minare)
            for cx in range(160, fw, 420):
                cx += rnd.randint(-60, 60)
                base = 470
                dome_r = rnd.randint(46, 62)
                pygame.draw.rect(s, col, ((cx - dome_r - 40) * k, (base - 50) * k, (dome_r * 2 + 80) * k, 80 * k))
                pygame.draw.circle(s, col, (cx * k, (base - 50) * k), dome_r * k)
                for sx in (-1, 1):
                    pygame.draw.circle(s, col, ((cx + sx * (dome_r + 18)) * k, (base - 46) * k), 24 * k)
                pygame.draw.rect(s, col, ((cx - 2) * k, (base - 50 - dome_r - 26) * k, 4 * k, 30 * k))
                pygame.draw.circle(s, col, (cx * k, (base - 50 - dome_r - 28) * k), 4 * k)
                n_min = rnd.choice((2, 4))
                for j in range(n_min):
                    side = -1 if j % 2 == 0 else 1
                    mx = cx + side * (dome_r + 40 + (j // 2) * 46)
                    mh = 150 + (0 if j < 2 else -20)
                    pygame.draw.rect(s, col, ((mx - 5) * k, (base - mh) * k, 10 * k, mh * k))
                    for bh in (0.45, 0.72):
                        pygame.draw.rect(s, col, ((mx - 9) * k, (base - mh * bh) * k, 18 * k, 5 * k))
                    pygame.draw.polygon(s, col, [((mx - 6) * k, (base - mh) * k), ((mx + 6) * k, (base - mh) * k),
                                                 (mx * k, (base - mh - 34) * k)])
        self.far = _ss_layer(fw, H, far_paint)

        mw = _layer_w(0.5)

        def mid_paint(s, k):
            bc = (46, 22, 58, 255)
            py1, py2 = 420, 1350
            pygame.draw.rect(s, bc, (0, 466 * k, mw * k, 12 * k))
            for px in (py1, py2):
                pygame.draw.rect(s, bc, (px * k, 280 * k, 14 * k, 200 * k))
                pygame.draw.rect(s, bc, ((px + 40) * k, 280 * k, 14 * k, 200 * k))
                pygame.draw.rect(s, bc, (px * k, 300 * k, 54 * k, 8 * k))
                pygame.draw.rect(s, bc, (px * k, 380 * k, 54 * k, 8 * k))
            pts = [((py1 + 27 + (py2 - py1) * i / 60) * k, (290 + 168 * (1 - (2 * i / 60 - 1) ** 2)) * k) for i in range(61)]
            pygame.draw.lines(s, bc, False, pts, int(4 * k))
            for i in range(0, 61, 2):
                pygame.draw.line(s, bc, pts[i], (pts[i][0], 468 * k), max(1, k))
            pygame.draw.line(s, bc, (0, 466 * k), ((py1 + 27) * k, 290 * k), int(4 * k))
            pygame.draw.line(s, bc, ((py2 + 27) * k, 290 * k), (mw * k, 466 * k), int(4 * k))
            self.bridge_pts = [(x / k, y / k) for x, y in pts]
        self.mid = _ss_layer(mw, H, mid_paint)
        self.boats = [dict(x=rnd.uniform(0, W), y=rnd.uniform(500, 560), sp=rnd.uniform(6, 14) * rnd.choice((-1, 1)),
                           sc=rnd.uniform(0.6, 1.0)) for _ in range(3)]
        self.gulls = [(rnd.uniform(0, W), rnd.uniform(100, 300), rnd.uniform(20, 40), rnd.uniform(0, 6)) for _ in range(6)]
        self.crowd = Crowd(5, 40, FLOOR_TOP - 4, (40, 20, 40), [(200, 60, 60), (60, 120, 200), (230, 190, 70), (90, 180, 110)])
        # zemin karo dokusu
        self.lamp_x = list(range(100, STAGE_W, 380))

    def draw_back(self, surf, camx):
        surf.blit(self.sky, (0, 0))
        sun = (W // 2 + 160 - int(camx * 0.05), 420)
        blit_glow(surf, sun, 420, (110, 50, 20), 1.0)
        blit_glow(surf, sun, 160, (160, 90, 40), 1.0)
        pygame.draw.circle(surf, (255, 222, 150), sun, 74)
        for cx, cy, cw, a in self.clouds:
            x = (cx + self.t * 6 * a - camx * 0.08) % (W + 600) - 300
            _soft_ellipse(surf, (255, 170, 140) if cy > 160 else (140, 80, 140), (int(x), int(cy), int(cw), int(cw * 0.22)), 120 * a)
        for gx, gy, gs, ph in self.gulls:
            x = (gx + self.t * gs) % (W + 100) - 50
            y = gy + math.sin(self.t + ph) * 10
            f = math.sin(self.t * 8 + ph) * 6
            pygame.draw.lines(surf, (40, 20, 50), False, [(x - 10, y - f), (x, y), (x + 10, y - f)], 2)
        self.blit_layer(surf, self.far, 0.22, camx)
        self.blit_layer(surf, self.mid, 0.5, camx)
        # köprü ışıkları
        off = -camx * 0.5
        for i, (bx, by) in enumerate(self.bridge_pts[::3]):
            x = bx + off
            if 0 < x < W:
                c = (255, 230, 160) if (i + int(self.t * 3)) % 6 else (255, 255, 255)
                pygame.draw.circle(surf, c, (int(x), int(by)), 2)
        # deniz
        top = 478
        sea = vgradient(W, FLOOR_TOP - top, (90, 52, 104), (44, 26, 70))
        surf.blit(sea, (0, top))
        # güneş yansıması sütunu
        for i in range(14):
            yy = top + 4 + i * 9
            wdt = 60 + i * 9 + math.sin(self.t * 3 + i) * 10
            c = lerp_color((255, 220, 150), (200, 110, 110), i / 14)
            pygame.draw.line(surf, c, (sun[0] - wdt / 2 + math.sin(self.t * 2 + i * 1.7) * 8, yy),
                             (sun[0] + wdt / 2 + math.sin(self.t * 2 + i * 1.7) * 8, yy), 3)
        for i in range(9):
            yy = top + 8 + i * 15
            for j in range(10):
                xx = (j * 160 + math.sin(self.t * 1.3 + i * 2 + j) * 24 - camx * (0.5 + i * 0.04)) % (W + 200) - 100
                pygame.draw.line(surf, lerp_color((230, 150, 140), (120, 70, 130), i / 9), (xx, yy), (xx + 36, yy), 2)
        # vapurlar
        for b in self.boats:
            b["x"] = (b["x"] + b["sp"] / 60) % (W + 300)
            x, y, sc = (b["x"] - camx * 0.4) % (W + 300) - 150, b["y"], b["sc"]
            hull = [(x - 60 * sc, y), (x + 60 * sc, y), (x + 48 * sc, y + 14 * sc), (x - 50 * sc, y + 14 * sc)]
            pygame.draw.polygon(surf, (30, 18, 40), hull)
            pygame.draw.rect(surf, (230, 220, 210), (x - 40 * sc, y - 16 * sc, 80 * sc, 16 * sc))
            for k in range(6):
                pygame.draw.rect(surf, (255, 200, 110), (x - 34 * sc + k * 12 * sc, y - 12 * sc, 6 * sc, 6 * sc))
            pygame.draw.rect(surf, (30, 18, 40), (x - 4 * sc, y - 30 * sc, 8 * sc, 14 * sc))
        # rıhtım korkuluğu + seyirci
        self.crowd.draw(surf, camx, self.t, 0.78, self.excite)
        rail_y = FLOOR_TOP - 34
        off = -camx * 0.85
        pygame.draw.rect(surf, (40, 26, 40), (0, rail_y, W, 6))
        pygame.draw.rect(surf, (40, 26, 40), (0, rail_y + 24, W, 4))
        for i in range(-1, W // 40 + 2):
            x = i * 40 + off % 40
            pygame.draw.rect(surf, (40, 26, 40), (x, rail_y, 5, 34))
        for lx in self.lamp_x:
            x = lx + off
            if -60 < x < W + 60:
                pygame.draw.rect(surf, (30, 20, 34), (x - 4, FLOOR_TOP - 190, 8, 190))
                pygame.draw.rect(surf, (30, 20, 34), (x - 14, FLOOR_TOP - 196, 28, 10), border_radius=4)
                blit_glow(surf, (int(x), FLOOR_TOP - 176), 70, (120, 80, 30), 1.0)
                pygame.draw.circle(surf, (255, 220, 150), (int(x), FLOOR_TOP - 178), 9)
        self.draw_tiles(surf, camx, (118, 84, 92), (100, 70, 82), (80, 54, 66))
        g = pygame.Surface((W, 120), pygame.SRCALPHA)
        for i in range(120):
            pygame.draw.line(g, (255, 140, 80, int(45 * (1 - i / 120))), (0, i), (W, i))
        surf.blit(g, (0, FLOOR_TOP))


# ============================================================================ Kapadokya
class CappadociaStage(Stage):
    name = "Kapadokya Şafağı"

    def build(self):
        rnd = random.Random(9)
        self.sky = vgradient(W, H, (70, 130, 210), (255, 196, 150))

        def chimney(s, k, x, base, h, w, c):
            body = [((x - w) * k, base * k), ((x - w * 0.45) * k, (base - h * 0.7) * k), ((x - w * 0.22) * k, (base - h) * k),
                    ((x + w * 0.22) * k, (base - h) * k), ((x + w * 0.45) * k, (base - h * 0.7) * k), ((x + w) * k, base * k)]
            pygame.draw.polygon(s, c, body)
            shd = [((x + w * 0.05) * k, (base - h) * k), ((x + w * 0.22) * k, (base - h) * k),
                   ((x + w * 0.45) * k, (base - h * 0.7) * k), ((x + w) * k, base * k), ((x + w * 0.35) * k, base * k)]
            pygame.draw.polygon(s, shade(c, 0.82), shd)
            for j in range(4):
                yy = base - h * (0.2 + j * 0.18)
                pygame.draw.line(s, shade(c, 0.9), ((x - w * (0.9 - j * 0.15)) * k, yy * k), ((x + w * (0.9 - j * 0.15)) * k, yy * k), max(1, k))
            cap = pygame.Rect(0, 0, w * 1.05 * k, 36 * k)
            cap.center = (x * k, (base - h - 8) * k)
            pygame.draw.ellipse(s, shade(c, 0.6), cap)
            pygame.draw.ellipse(s, shade(c, 0.72), cap.inflate(-8 * k, -14 * k).move(-4 * k, -4 * k))

        fw = _layer_w(0.2)

        def far_paint(s, k):
            pts = [(0, 520 * k)]
            for x in range(0, fw + 60, 60):
                pts.append((x * k, (440 + math.sin(x * 0.01) * 30 + rnd.uniform(-10, 10)) * k))
            pts += [(fw * k, H * k), (0, H * k)]
            pygame.draw.polygon(s, (214, 168, 150, 255), pts)
            for _ in range(26):
                chimney(s, k, rnd.randint(0, fw), 500, rnd.randint(60, 140), rnd.randint(22, 38), (216, 170, 148, 255))
        self.far = _ss_layer(fw, H, far_paint)
        mw = _layer_w(0.5)

        def mid_paint(s, k):
            pts = [(0, 560 * k)]
            for x in range(0, mw + 80, 80):
                pts.append((x * k, (520 + math.sin(x * 0.006 + 1) * 30) * k))
            pts += [(mw * k, H * k), (0, H * k)]
            pygame.draw.polygon(s, (220, 164, 124, 255), pts)
            for _ in range(13):
                x = rnd.randint(0, mw)
                h = rnd.randint(170, 320)
                w = rnd.randint(50, 90)
                chimney(s, k, x, 600, h, w, (230, 176, 132, 255))
                for _ in range(rnd.randint(2, 4)):
                    wx, wy = x + rnd.randint(-w // 3, w // 3), 600 - rnd.randint(40, int(h * 0.75))
                    pygame.draw.ellipse(s, (96, 60, 44, 255), ((wx - 7) * k, (wy - 11) * k, 14 * k, 22 * k))
                    pygame.draw.rect(s, (96, 60, 44, 255), ((wx - 7) * k, wy * k, 14 * k, 11 * k))
        self.mid = _ss_layer(mw, H, mid_paint)
        self.balloons = [(rnd.uniform(0, 1), rnd.uniform(50, 320), rnd.uniform(0.45, 1.1),
                          rnd.choice([(228, 64, 56), (250, 196, 60), (70, 150, 226), (110, 196, 90), (236, 110, 176)]),
                          rnd.choice([(250, 250, 240), (40, 40, 60), (250, 196, 60)]))
                         for _ in range(10)]
        self.balloons.sort(key=lambda b: b[2])
        self.crowd = Crowd(11, 30, FLOOR_TOP - 4, (120, 80, 60), [(220, 80, 60), (60, 110, 180), (230, 200, 80), (240, 240, 230)],
                           spacing=58)
        self.rocks = [(rnd.randint(0, STAGE_W), rnd.randint(12, 26)) for _ in range(14)]

    def draw_balloon(self, surf, x, y, sc, col, stripe):
        r = 30 * sc
        env = pygame.Rect(0, 0, r * 2, r * 2.3)
        env.center = (x, y)
        pygame.draw.ellipse(surf, col, env)
        for k in (-0.45, 0.0, 0.45):
            sr = pygame.Rect(0, 0, r * 2 * (1 - abs(k)) * 0.45, r * 2.3)
            sr.center = (x + k * r * 1.1, y)
            pygame.draw.ellipse(surf, stripe, sr)
        pygame.draw.ellipse(surf, shade(col, 0.75), env, max(1, int(3 * sc)))
        pygame.draw.ellipse(surf, (255, 255, 255), (x - r * 0.6, y - r * 0.8, r * 0.35, r * 0.6))
        pygame.draw.polygon(surf, shade(col, 0.8), [(x - r * 0.7, y + r * 0.9), (x + r * 0.7, y + r * 0.9), (x + r * 0.25, y + r * 1.35),
                                                   (x - r * 0.25, y + r * 1.35)])
        for sx in (-0.22, 0.22):
            pygame.draw.line(surf, (80, 60, 40), (x + sx * r, y + r * 1.35), (x + sx * r * 0.7, y + r * 1.75), max(1, int(2 * sc)))
        pygame.draw.rect(surf, (110, 76, 46), (x - r * 0.25, y + r * 1.72, r * 0.5, r * 0.36), border_radius=2)
        if int(self.t * 2 + x) % 7 == 0:
            blit_glow(surf, (int(x), int(y + r * 1.5)), int(14 * sc), (120, 80, 20), 1.0)

    def draw_back(self, surf, camx):
        surf.blit(self.sky, (0, 0))
        sun = (240 - int(camx * 0.05), 470)
        blit_glow(surf, sun, 360, (120, 90, 40), 1.0)
        pygame.draw.circle(surf, (255, 236, 190), sun, 54)
        for bx, by, sc, col, st in self.balloons[:5]:
            x = (bx * (W + 400) + self.t * 7 * sc - camx * 0.12 * sc) % (W + 400) - 200
            self.draw_balloon(surf, x, by + math.sin(self.t * 0.7 + bx * 10) * 8, sc * 0.7, lerp_color(col, (200, 170, 190), 0.35),
                              lerp_color(st, (200, 170, 190), 0.35))
        self.blit_layer(surf, self.far, 0.2, camx)
        haze = pygame.Surface((W, 200), pygame.SRCALPHA)
        for i in range(200):
            pygame.draw.line(haze, (255, 210, 180, int(70 * (i / 200))), (0, i), (W, i))
        surf.blit(haze, (0, 340))
        for bx, by, sc, col, st in self.balloons[5:]:
            x = (bx * (W + 400) + self.t * 9 * sc - camx * 0.3 * sc) % (W + 400) - 200
            self.draw_balloon(surf, x, by + math.sin(self.t * 0.6 + bx * 10) * 10, sc, col, st)
        self.blit_layer(surf, self.mid, 0.5, camx)
        self.crowd.draw(surf, camx, self.t, 0.78, self.excite)
        self.draw_tiles(surf, camx, (196, 146, 104), (184, 134, 94), (160, 112, 78), tile=150)
        for rx, rs in self.rocks:
            x = rx - camx
            if -40 < x < W + 40:
                pygame.draw.ellipse(surf, (150, 104, 74), (x - rs, H - 40 - rs * 0.3, rs * 2, rs))
                pygame.draw.ellipse(surf, (176, 128, 92), (x - rs * 0.7, H - 40 - rs * 0.35, rs * 1.2, rs * 0.5))


# ============================================================================ Gece çarşısı
class NightMarketStage(Stage):
    name = "Gece Çarşısı"

    def build(self):
        rnd = random.Random(21)
        self.sky = vgradient(W, H, (6, 4, 22), (44, 20, 74))
        self.stars = [(rnd.randint(0, W), rnd.randint(0, 300), rnd.random()) for _ in range(110)]
        fw = _layer_w(0.3)

        def far_paint(s, k):
            x = 0
            while x < fw:
                w = rnd.randint(70, 150)
                h = rnd.randint(150, 330)
                c = (22, 18, 44, 255)
                pygame.draw.rect(s, c, (x * k, (560 - h) * k, w * k, (h + 100) * k))
                if rnd.random() < 0.3:
                    pygame.draw.polygon(s, c, [(x * k, (560 - h) * k), ((x + w) * k, (560 - h) * k), ((x + w / 2) * k, (560 - h - 40) * k)])
                for wy in range(560 - h + 16, 540, 24):
                    for wx in range(x + 10, x + w - 14, 20):
                        if rnd.random() < 0.35:
                            pygame.draw.rect(s, rnd.choice([(255, 210, 120, 255), (120, 220, 255, 255), (255, 140, 200, 255)]),
                                             (wx * k, wy * k, 9 * k, 12 * k))
                x += w + rnd.randint(4, 20)
        self.far = _ss_layer(fw, H, far_paint)
        mw = _layer_w(0.6)
        self.signs = []
        self.stalls = []

        def mid_paint(s, k):
            x = 40
            while x < mw:
                w = rnd.randint(170, 240)
                pygame.draw.rect(s, (36, 24, 48, 255), (x * k, 420 * k, w * k, 200 * k))
                awning = rnd.choice([(196, 40, 70), (30, 140, 160), (220, 150, 40), (120, 60, 180)])
                for i in range(0, w, 22):
                    c = awning if (i // 22) % 2 == 0 else shade(awning, 1.45)
                    pygame.draw.polygon(s, c + (255,), [((x + i) * k, 420 * k), ((x + i + 22) * k, 420 * k), ((x + i + 22) * k, 462 * k),
                                                        ((x + i + 11) * k, 470 * k), (((x + i) * k), 462 * k)])
                pygame.draw.rect(s, (70, 44, 60, 255), ((x + 8) * k, 520 * k, (w - 16) * k, 56 * k), border_radius=6 * k)
                goods = rnd.choice(["fruit", "lamps", "spice"])
                for j in range(6):
                    gx = x + 26 + j * (w - 52) / 5
                    if goods == "fruit":
                        for q in range(3):
                            pygame.draw.circle(s, rnd.choice([(250, 120, 40), (250, 200, 60), (120, 200, 80), (200, 50, 60)]) + (255,),
                                               ((gx - 8 + q * 8) * k, (514 + (q % 2) * -6) * k), 7 * k)
                    elif goods == "spice":
                        c = rnd.choice([(200, 60, 40), (230, 170, 40), (140, 90, 40), (80, 140, 60)])
                        pygame.draw.polygon(s, c + (255,), [((gx - 12) * k, 520 * k), ((gx + 12) * k, 520 * k), (gx * k, 500 * k)])
                    else:
                        c = rnd.choice([(80, 160, 220), (220, 80, 120), (240, 200, 80), (120, 220, 160)])
                        pygame.draw.ellipse(s, c + (255,), ((gx - 8) * k, 498 * k, 16 * k, 20 * k))
                        pygame.draw.line(s, (200, 170, 90, 255), (gx * k, 482 * k), (gx * k, 498 * k), max(1, k))
                self.signs.append((x + w // 2, 392, awning))
                self.stalls.append((x + w // 2, goods))
                x += w + rnd.randint(50, 90)
        self.mid = _ss_layer(mw, H, mid_paint)
        self.crowd = Crowd(31, 40, FLOOR_TOP - 4, (20, 14, 34), [(220, 60, 120), (60, 200, 220), (240, 200, 70), (150, 90, 230)])
        self.steam = []

    def draw_back(self, surf, camx):
        surf.blit(self.sky, (0, 0))
        for sx, sy, k in self.stars:
            b = int(140 + 110 * math.sin(self.t * 2 + k * 20))
            surf.set_at((sx, sy), (b, b, b))
        mx = 1000 - int(camx * 0.05)
        blit_glow(surf, (mx, 110), 120, (40, 40, 60), 1.0)
        pygame.draw.circle(surf, (240, 240, 220), (mx, 110), 38)
        pygame.draw.circle(surf, (14, 8, 34), (mx + 16, 100), 34)
        self.blit_layer(surf, self.far, 0.3, camx)
        off = -int(camx * 0.6)
        surf.blit(self.mid, (off, 0))
        for i, (sx, sy, c) in enumerate(self.signs):
            x = sx + off
            if -100 < x < W + 100:
                fl = 0.75 + 0.25 * math.sin(self.t * 5 + i * 3) * (1 if (i + int(self.t * 2)) % 7 else 0.2)
                blit_glow(surf, (x, sy), 80, tuple(int(v * 0.55 * fl) for v in c), 1.0)
                pygame.draw.rect(surf, shade(c, 1.5), (x - 54, sy - 15, 108, 30), border_radius=9)
                pygame.draw.rect(surf, (255, 255, 255), (x - 54, sy - 15, 108, 30), 2, border_radius=9)
                word = ("ÇAY", "SİMİT", "KEBAP", "LOKUM", "BAHARAT", "KUMPİR", "DONDURMA")[i % 7]
                text(surf, word, 18, (x, sy), (30, 10, 30), shadow=False)
        # buhar
        if random.random() < 0.3:
            sx, _ = random.choice(self.stalls)
            self.steam.append([sx + random.uniform(-30, 30), 500, 0.0])
        alive = []
        for p in self.steam:
            p[1] -= 0.6
            p[2] += 1 / 60
            if p[2] < 2.4:
                alive.append(p)
                a = int(60 * (1 - p[2] / 2.4))
                r = int(8 + p[2] * 14)
                g = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(g, (220, 220, 240, a), (r, r), r)
                surf.blit(g, (p[0] + off - r + math.sin(p[2] * 3) * 6, p[1] - r))
        self.steam = alive[-60:]
        # fener ipi
        off2 = -int(camx * 0.8)
        pts = [(i * 60 + off2, 150 + math.sin(i * 0.52) * 18) for i in range(0, 60)]
        pygame.draw.lines(surf, (30, 20, 30), False, pts, 2)
        for i in range(2, 60, 3):
            x, y = pts[i]
            if -40 < x < W + 40:
                c = [(255, 80, 60), (255, 190, 60), (255, 120, 200)][(i // 3) % 3]
                sw = math.sin(self.t * 2 + i) * 3
                blit_glow(surf, (int(x + sw), int(y + 22)), 46, tuple(v // 3 for v in c), 1.0)
                pygame.draw.ellipse(surf, c, (x - 11 + sw, y + 8, 22, 28))
                pygame.draw.ellipse(surf, shade(c, 1.3), (x - 5 + sw, y + 12, 8, 14))
                pygame.draw.rect(surf, (60, 40, 30), (x - 7 + sw, y + 5, 14, 5))
                pygame.draw.line(surf, (30, 20, 30), (x, y), (x + sw, y + 5), 2)
        self.crowd.draw(surf, camx, self.t, 0.78, self.excite)
        self.draw_tiles(surf, camx, (38, 30, 56), (32, 24, 48), (60, 44, 84), tile=110)
        # ıslak zeminde ışık yansımaları
        for i, (sx, sy, c) in enumerate(self.signs):
            x = sx + off
            if -100 < x < W + 100:
                for j in range(6):
                    yy = FLOOR_TOP + 20 + j * 14
                    wdt = 40 - j * 4 + math.sin(self.t * 3 + j + i) * 6
                    col = tuple(int(v * (0.5 - j * 0.07)) for v in c)
                    pygame.draw.line(surf, col, (x - wdt / 2, yy), (x + wdt / 2, yy), 4)


STAGES = [BosphorusStage, CappadociaStage, NightMarketStage]


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


STAGES = [FortressStage, RooftopStage, MetroStage] + STAGES
