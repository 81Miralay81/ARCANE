"""Uzay İstilası (uzay atıcı)."""
import math
import random

import pygame

from engine.core import GOLD, WHITE, W, H, blit_glow, shade, text
from games.arcade_base import ArcadeGame

ALIEN_COLORS = [(255, 90, 160), (120, 230, 120), (90, 200, 255), (255, 200, 80)]

# 11x8 piksel desenleri (özgün)
SHAPES = [
    ["...X...X...", "....XXX....", "..XXXXXXX..", ".XX.XXX.XX.", "XXXXXXXXXXX", "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."],
    ["....XXX....", "..XXXXXXX..", ".XXXXXXXXX.", "XXX..X..XXX", "XXXXXXXXXXX", "..XX...XX..", ".XX.XXX.XX.", "XX.......XX"],
    ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.", "XXXXXXXXXXX", ".XXXXXXXXX.", "..X..X..X..", ".X.X...X.X."],
]


def make_sprite(shape, color, px=4):
    surf = pygame.Surface((len(shape[0]) * px, len(shape) * px), pygame.SRCALPHA)
    for y, row in enumerate(shape):
        for x, ch in enumerate(row):
            if ch == "X":
                pygame.draw.rect(surf, color, (x * px, y * px, px, px))
    return surf


class InvadersGame(ArcadeGame):
    key = "uzay"
    title = "UZAY İSTİLASI"
    help = "← → / A D hareket, BOŞLUK / F ateş\nİstilacıları yok et, kalkanların arkasına saklan\nKırmızı ana gemi = bonus puan"
    bg_top = (2, 2, 14)
    bg_bottom = (10, 6, 34)
    grid_color = (30, 20, 70)

    def reset(self):
        self.wave = 1
        self.lives = 3
        self.sprites = [[make_sprite(SHAPES[i % 3], ALIEN_COLORS[i % 4]), make_sprite(SHAPES[(i + 1) % 3], ALIEN_COLORS[i % 4])]
                        for i in range(4)]
        self.start_wave()

    def start_wave(self):
        self.ship_x = W / 2
        self.bullets = []
        self.ebullets = []
        self.aliens = []
        for r in range(5):
            for c in range(11):
                self.aliens.append(dict(x=200 + c * 72, y=120 + r * 52, row=r, alive=True))
        self.adir = 1
        self.astep = 0.0
        self.frame = 0
        self.cool = 0
        self.invuln = 60
        self.ufo = None
        self.shields = []
        for i in range(4):
            bx = 180 + i * 290
            for yy in range(4):
                for xx in range(10):
                    if yy == 3 and 3 <= xx <= 6:
                        continue
                    self.shields.append(pygame.Rect(bx + xx * 9, H - 170 + yy * 9, 9, 9))

    def play_event(self, e):
        pass

    def fire(self):
        if self.cool <= 0 and len(self.bullets) < 3:
            self.bullets.append([self.ship_x, H - 92])
            self.cool = 14
            self.app.audio.play("laser")

    def play_update(self, dt):
        self.frame += 1
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        shoot = keys[pygame.K_SPACE] or keys[pygame.K_f] or keys[pygame.K_UP]
        for j in self.app.joysticks[:1]:
            try:
                if abs(j.get_axis(0)) > 0.3:
                    dx = j.get_axis(0)
                if j.get_numhats() and j.get_hat(0)[0]:
                    dx = j.get_hat(0)[0]
                shoot = shoot or j.get_button(0)
            except Exception:
                pass
        self.ship_x = max(40, min(W - 40, self.ship_x + dx * 7))
        self.cool -= 1
        if self.invuln > 0:
            self.invuln -= 1
        if shoot:
            self.fire()
        alive = [a for a in self.aliens if a["alive"]]
        # istilacı hareketi: azaldıkça hızlanır
        speed = 0.6 + (55 - len(alive)) * 0.07 + self.wave * 0.25
        edge = False
        for a in alive:
            a["x"] += self.adir * speed
            if a["x"] < 50 or a["x"] > W - 50:
                edge = True
        if edge:
            self.adir *= -1
            for a in alive:
                a["y"] += 22
                a["x"] += self.adir * speed
        if alive and random.random() < 0.012 + self.wave * 0.004:
            cols = {}
            for a in alive:
                k = round(a["x"] / 10)
                if k not in cols or a["y"] > cols[k]["y"]:
                    cols[k] = a
            sh = random.choice(list(cols.values()))
            self.ebullets.append([sh["x"], sh["y"] + 20, random.random() < 0.3])
        # UFO
        if self.ufo is None and random.random() < 0.002:
            d = random.choice((-1, 1))
            self.ufo = [W + 60 if d < 0 else -60, 84, d]
        if self.ufo:
            self.ufo[0] += self.ufo[2] * 3
            if self.ufo[0] < -80 or self.ufo[0] > W + 80:
                self.ufo = None
        # mermiler
        for b in self.bullets:
            b[1] -= 13
            br = pygame.Rect(b[0] - 2, b[1] - 10, 4, 18)
            for sh in self.shields:
                if sh.colliderect(br):
                    self.shields.remove(sh)
                    b[1] = -100
                    break
            for a in alive:
                if a["alive"] and abs(a["x"] - b[0]) < 24 and abs(a["y"] - b[1]) < 18:
                    a["alive"] = False
                    b[1] = -100
                    self.score += (5 - a["row"]) * 10
                    col = ALIEN_COLORS[a["row"] % 4]
                    self.parts.emit(a["x"], a["y"], 24, col, speed=5, life=26, size=4, glow=True)
                    self.app.audio.play("brick")
                    break
            if self.ufo and abs(self.ufo[0] - b[0]) < 34 and abs(self.ufo[1] - b[1]) < 16:
                bonus = random.choice((100, 150, 300))
                self.score += bonus
                self.parts.emit(self.ufo[0], self.ufo[1], 40, (255, 80, 80), speed=6, life=34, size=5, glow=True)
                self.app.audio.play("powerup")
                self.ufo = None
                b[1] = -100
        self.bullets = [b for b in self.bullets if b[1] > 60]
        ship = pygame.Rect(self.ship_x - 26, H - 92, 52, 30)
        for b in self.ebullets:
            b[1] += 5.5 if not b[2] else 7.5
            br = pygame.Rect(b[0] - 3, b[1] - 8, 6, 16)
            hit_sh = next((sh for sh in self.shields if sh.colliderect(br)), None)
            if hit_sh:
                self.shields.remove(hit_sh)
                b[1] = H + 100
            elif ship.colliderect(br) and self.invuln <= 0:
                b[1] = H + 100
                self.die()
                if self.state != "play":
                    return
        self.ebullets = [b for b in self.ebullets if b[1] < H]
        for a in alive:
            if a["y"] > H - 140:
                for sh in list(self.shields):
                    if abs(sh.centerx - a["x"]) < 28 and abs(sh.centery - a["y"]) < 20:
                        self.shields.remove(sh)
            if a["y"] > H - 110:
                self.lives = 0
                self.die()
                return
        if not any(a["alive"] for a in self.aliens):
            self.wave += 1
            self.score += 250
            self.app.audio.play("win")
            self.start_wave()

    def die(self):
        self.lives -= 1
        self.shake = 16
        self.parts.emit(self.ship_x, H - 80, 60, (120, 220, 255), speed=7, life=40, size=5, glow=True)
        self.app.audio.play("boom")
        self.invuln = 90
        self.ebullets.clear()
        if self.lives <= 0:
            self.game_over()

    def play_draw(self, s):
        sx = random.randint(-self.shake, self.shake) if self.shake else 0
        anim = (self.frame // 30) % 2
        for a in self.aliens:
            if a["alive"]:
                spr = self.sprites[a["row"] % 4][anim]
                col = ALIEN_COLORS[a["row"] % 4]
                blit_glow(s, (int(a["x"]) + sx, int(a["y"])), 30, shade(col, 0.25))
                s.blit(spr, (a["x"] - spr.get_width() / 2 + sx, a["y"] - spr.get_height() / 2))
        for sh in self.shields:
            pygame.draw.rect(s, (80, 230, 140), sh.move(sx, 0))
        if self.ufo:
            ux, uy = int(self.ufo[0]) + sx, int(self.ufo[1])
            blit_glow(s, (ux, uy), 50, (90, 20, 20))
            pygame.draw.ellipse(s, (230, 60, 70), (ux - 34, uy - 8, 68, 18))
            pygame.draw.ellipse(s, (255, 190, 200), (ux - 14, uy - 18, 28, 18))
            for i in range(4):
                pygame.draw.circle(s, GOLD if (self.frame // 6 + i) % 2 else WHITE, (ux - 21 + i * 14, uy + 1), 3)
        for b in self.bullets:
            blit_glow(s, (int(b[0]) + sx, int(b[1])), 16, (20, 80, 100))
            pygame.draw.line(s, (180, 250, 255), (b[0] + sx, b[1] - 10), (b[0] + sx, b[1] + 8), 4)
        for b in self.ebullets:
            col = (255, 90, 90) if b[2] else (255, 220, 120)
            off = math.sin(b[1] * 0.2) * 3
            pygame.draw.line(s, col, (b[0] + off + sx, b[1] - 8), (b[0] - off + sx, b[1] + 8), 4)
        if self.invuln <= 0 or (self.frame // 4) % 2:
            x, y = self.ship_x + sx, H - 80
            blit_glow(s, (int(x), int(y + 22)), 30 + int(math.sin(self.t * 30) * 4), (20, 80, 140))
            pygame.draw.polygon(s, (80, 200, 255), [(x, y - 26), (x + 28, y + 14), (x + 12, y + 8), (x - 12, y + 8), (x - 28, y + 14)])
            pygame.draw.polygon(s, (220, 245, 255), [(x, y - 16), (x + 7, y + 2), (x - 7, y + 2)])
            pygame.draw.line(s, (255, 160, 60), (x - 8, y + 12), (x - 8, y + 20 + random.randint(0, 6)), 4)
            pygame.draw.line(s, (255, 160, 60), (x + 8, y + 12), (x + 8, y + 20 + random.randint(0, 6)), 4)
        for i in range(self.lives):
            x = W // 2 - 40 + i * 30
            pygame.draw.polygon(s, (80, 200, 255), [(x, 22), (x + 11, 40), (x - 11, 40)])
        text(s, f"DALGA {self.wave}", 22, (W // 2 + 80, 32), GOLD, anchor="midleft")
        pygame.draw.line(s, (80, 230, 140), (0, H - 46), (W, H - 46), 2)
