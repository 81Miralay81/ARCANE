"""Telefon için ekran üstü oyun kolu: solda yön çemberi, sağda saldırı ve özel hareket tuşları."""
import math
import os
import sys

import pygame

from engine.core import GOLD, W, H, blit_glow, text


def is_android():
    return "ANDROID_ARGUMENT" in os.environ or "ANDROID_PRIVATE" in os.environ or hasattr(sys, "getandroidapilevel")


class Button:
    def __init__(self, key, x, y, r, label, color):
        self.key, self.x, self.y, self.r, self.label, self.color = key, x, y, r, label, color
        self.down = False

    def hit(self, px, py):
        return (px - self.x) ** 2 + (py - self.y) ** 2 <= (self.r * 1.18) ** 2


class TouchPad:
    """Çoklu dokunuşu takip eder. Dövüş sahnesi her karede durumunu okur."""

    STICK = (190, 545)
    STICK_R = 110

    def __init__(self):
        self.fingers = {}        # id -> (x, y, owner)
        self.stick_id = None
        self.knob = (0.0, 0.0)
        self.center = self.STICK      # yön çemberi parmağın ilk değdiği yere gelir
        self.buttons = [
            Button("P", 1080, 620, 62, "YUMRUK", (255, 90, 80)),
            Button("K", 1200, 540, 62, "TEKME", (80, 170, 255)),
            Button("S0", 950, 640, 46, "", (255, 170, 60)),
            Button("S1", 960, 515, 46, "", (120, 230, 140)),
            Button("S2", 1075, 465, 46, "", (200, 120, 255)),
            Button("SUP", 1200, 405, 52, "SÜPER", (255, 210, 60)),
        ]
        self.pause_btn = Button("PAUSE", W // 2, 122, 28, "II", (230, 230, 240))
        self.pressed = set()     # bu karede yeni basılanlar
        self.labels = {}

    def set_skill_labels(self, ch):
        for i, sp in enumerate(ch["specials"][:3]):
            self.labels["S%d" % i] = sp["name"]
        self.labels["SUP"] = ch["super"]["name"]

    def _pos(self, e):
        """Dokunma konumunu oyunun 1280x720 koordinatına çevirir.
        Telefon ekranı daha geniş olduğu için iki yanda siyah boşluk kalır; onu hesaba katar."""
        if e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            try:
                ww, wh = pygame.display.get_window_size()
            except Exception:
                ww, wh = W, H
            if ww <= 0 or wh <= 0:
                ww, wh = W, H
            sc = min(ww / W, wh / H)
            ox = (ww - W * sc) / 2
            oy = (wh - H * sc) / 2
            return (e.x * ww - ox) / sc, (e.y * wh - oy) / sc
        return e.pos

    def handle(self, e):
        """Olay dokunmatik kontrole aitse True döner."""
        if e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            if getattr(e, "touch", False):
                return True          # dokunuştan üretilen sahte fare olayı: yoksay
            fid = "mouse"
            if e.type == pygame.MOUSEMOTION and fid not in self.fingers:
                return False
            kind = {pygame.MOUSEBUTTONDOWN: "down", pygame.MOUSEBUTTONUP: "up", pygame.MOUSEMOTION: "move"}[e.type]
        elif e.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            fid = e.finger_id
            kind = {pygame.FINGERDOWN: "down", pygame.FINGERUP: "up", pygame.FINGERMOTION: "move"}[e.type]
        else:
            return False
        x, y = self._pos(e)
        if kind == "down":
            if self.pause_btn.hit(x, y):
                self.pressed.add("PAUSE")
                return True
            if x < W * 0.45 and y > H * 0.3:
                self.stick_id = fid
                self.fingers[fid] = (x, y, "stick")
                self.center = (max(self.STICK_R, min(W * 0.45 - 20, x)), max(H * 0.3 + 40, min(H - 60, y)))
                self._stick(x, y)
                return True
            for b in self.buttons:
                if b.hit(x, y):
                    b.down = True
                    self.pressed.add(b.key)
                    self.fingers[fid] = (x, y, b.key)
                    return True
            return False
        if kind == "move":
            if fid == self.stick_id:
                self._stick(x, y)
                return True
            if fid in self.fingers:
                # parmak kaydırılırsa başka tuşa geçebilir
                old = self.fingers[fid][2]
                for b in self.buttons:
                    if b.hit(x, y) and b.key != old:
                        for o in self.buttons:
                            if o.key == old:
                                o.down = False
                        b.down = True
                        self.pressed.add(b.key)
                        self.fingers[fid] = (x, y, b.key)
                return True
            return False
        # up
        if fid == self.stick_id:
            self.stick_id = None
            self.knob = (0.0, 0.0)
            self.center = self.STICK
        info = self.fingers.pop(fid, None)
        if info:
            for b in self.buttons:
                if b.key == info[2]:
                    b.down = False
            return True
        return False

    def _stick(self, x, y):
        cx, cy = self.center
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d > self.STICK_R:
            dx, dy = dx / d * self.STICK_R, dy / d * self.STICK_R
        self.knob = (dx / self.STICK_R, dy / self.STICK_R)

    def dirs(self):
        kx, ky = self.knob
        if math.hypot(kx, ky) < 0.32:
            return False, False, False, False
        a = math.degrees(math.atan2(ky, kx)) % 360
        # 8 yön
        sector = int(((a + 22.5) % 360) // 45)
        right = sector in (7, 0, 1)
        down = sector in (1, 2, 3)
        left = sector in (3, 4, 5)
        up = sector in (5, 6, 7)
        return left, right, up, down

    def held(self, key):
        return any(b.down for b in self.buttons if b.key == key)

    def take(self, key):
        if key in self.pressed:
            self.pressed.discard(key)
            return True
        return False

    def clear(self):
        self.pressed.clear()

    def draw(self, s, fighter=None, t=0.0):
        cx, cy = (int(self.center[0]), int(self.center[1]))
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(ov, (255, 255, 255, 34), (cx, cy), self.STICK_R)
        pygame.draw.circle(ov, (255, 255, 255, 110), (cx, cy), self.STICK_R, 3)
        for k in range(8):
            a = math.radians(k * 45)
            px, py = cx + math.cos(a) * (self.STICK_R - 22), cy + math.sin(a) * (self.STICK_R - 22)
            pts = [(px + math.cos(a) * 10, py + math.sin(a) * 10),
                   (px + math.cos(a + 2.3) * 9, py + math.sin(a + 2.3) * 9),
                   (px + math.cos(a - 2.3) * 9, py + math.sin(a - 2.3) * 9)]
            pygame.draw.polygon(ov, (255, 255, 255, 120), pts)
        kx, ky = self.knob
        kp = (int(cx + kx * self.STICK_R * 0.8), int(cy + ky * self.STICK_R * 0.8))
        pygame.draw.circle(ov, (255, 255, 255, 120 if self.stick_id is not None else 70), kp, 46)
        pygame.draw.circle(ov, (255, 255, 255, 190), kp, 46, 3)
        meter_ready = fighter is not None and fighter.meter >= 100
        for b in self.buttons:
            alpha = 200 if b.down else 105
            col = b.color
            if b.key == "SUP" and not meter_ready:
                col = (110, 100, 120)
            pygame.draw.circle(ov, col + (alpha,), (b.x, b.y), b.r)
            pygame.draw.circle(ov, (255, 255, 255, 200), (b.x, b.y), b.r, 3)
        pb = self.pause_btn
        pygame.draw.circle(ov, (0, 0, 0, 110), (pb.x, pb.y), pb.r)
        pygame.draw.circle(ov, (255, 255, 255, 160), (pb.x, pb.y), pb.r, 2)
        s.blit(ov, (0, 0))
        if meter_ready:
            sb = self.buttons[-1]
            blit_glow(s, (sb.x, sb.y), int(sb.r * 1.8 + math.sin(t * 8) * 6), (110, 90, 20), 1.0)
        for b in self.buttons:
            lab = b.label or self.labels.get(b.key, "")
            words = lab.split()
            size = 17 if b.r > 50 else 14
            if len(words) > 1 and b.r < 50:
                text(s, words[0], size, (b.x, b.y - 8), (255, 255, 255), outline=1)
                text(s, " ".join(words[1:]), size, (b.x, b.y + 9), (255, 255, 255), outline=1)
            else:
                text(s, lab, size, (b.x, b.y), GOLD if b.key == "SUP" and meter_ready else (255, 255, 255), outline=1)
        pygame.draw.rect(s, (255, 255, 255), (pb.x - 8, pb.y - 10, 5, 20))
        pygame.draw.rect(s, (255, 255, 255), (pb.x + 3, pb.y - 10, 5, 20))
