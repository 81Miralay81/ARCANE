"""Mini oyunlar için ortak taban: neon arka plan, duraklatma, oyun sonu ekranı."""
import math
import random

import pygame

from engine.core import GOLD, WHITE, W, H, Particles, Scene, is_back, is_confirm, nav_dir, text, vgradient


class ArcadeGame(Scene):
    key = "oyun"
    title = "OYUN"
    help = ""
    bg_top = (10, 8, 30)
    bg_bottom = (30, 10, 50)
    grid_color = (50, 30, 90)

    def __init__(self, app):
        super().__init__(app)
        self.parts = Particles()
        self.bg = vgradient(W, H, self.bg_top, self.bg_bottom)
        self.t = 0.0
        self.state = "ready"   # ready / play / pause / over
        self.state_t = 0.0
        self.menu_i = 0
        self.score = 0
        self.shake = 0
        self.new_best = False
        self.stars = [(random.randint(0, W), random.randint(0, H), random.random()) for _ in range(70)]
        self.reset()

    def on_enter(self):
        self.app.audio.play_music("game")

    # alt sınıflar doldurur
    def reset(self):
        pass

    def play_event(self, e):
        pass

    def play_update(self, dt):
        pass

    def play_draw(self, s):
        pass

    def game_over(self):
        self.state = "over"
        self.state_t = 0
        self.menu_i = 0
        self.new_best = self.app.save.submit(self.key, self.score)
        self.app.audio.play("lose")

    def handle(self, e):
        if self.state == "play":
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p)) or \
                    (e.type == pygame.JOYBUTTONDOWN and e.button in (7, 9)):
                self.state = "pause"
                self.menu_i = 0
                self.app.audio.play("back")
                return
            self.play_event(e)
        elif self.state == "ready":
            if is_back(e):
                self.app.pop()
            elif is_confirm(e) or (e.type == pygame.KEYDOWN and e.key not in (pygame.K_ESCAPE,)):
                self.state = "play"
                self.app.audio.play("select")
        elif self.state in ("pause", "over"):
            d = nav_dir(e)
            if d and d[1]:
                self.menu_i = (self.menu_i + d[1]) % 2
                self.app.audio.play("menu")
            elif is_confirm(e) and (self.state == "pause" or self.state_t > 0.8):
                self.app.audio.play("select")
                if self.menu_i == 0:
                    if self.state == "pause":
                        self.state = "play"
                    else:
                        self.score = 0
                        self.reset()
                        self.state = "play"
                else:
                    self.app.pop()
            elif is_back(e):
                if self.state == "pause":
                    self.state = "play"
                else:
                    self.app.pop()

    def update(self, dt):
        self.t += dt
        self.state_t += dt
        if self.shake > 0:
            self.shake -= 1
        if self.state == "play":
            self.play_update(dt)
        self.parts.update()

    def draw_bg(self, s):
        s.blit(self.bg, (0, 0))
        for x, y, k in self.stars:
            b = int(90 + 90 * math.sin(self.t * 2 + k * 30))
            s.set_at((x, y), (b, b, min(255, b + 40)))
        # alt kısımda kayan neon ızgara
        hor = H - 160
        for i in range(12):
            yy = hor + (i ** 1.8) * 1.6 + (self.t * 30 % 20) * (i / 12)
            if yy < H:
                pygame.draw.line(s, self.grid_color, (0, yy), (W, yy), 1)
        for i in range(-12, 13):
            pygame.draw.line(s, self.grid_color, (W / 2 + i * 40, hor), (W / 2 + i * 200, H), 1)

    def draw(self, s):
        self.draw_bg(s)
        self.play_draw(s)
        self.parts.draw(s)
        best = max(self.app.save.best(self.key), self.score)
        text(s, f"SKOR  {self.score}", 30, (30, 30), WHITE, anchor="midleft", outline=2)
        text(s, f"REKOR  {best}", 24, (W - 30, 30), GOLD, anchor="midright", outline=2)
        if self.state == "ready":
            self._overlay(s, 150)
            text(s, self.title, 84, (W // 2, H // 2 - 90), GOLD, outline=4)
            for i, line in enumerate(self.help.split("\n")):
                text(s, line, 24, (W // 2, H // 2 + i * 34), WHITE)
            if int(self.t * 2) % 2:
                text(s, "Başlamak için bir tuşa bas", 26, (W // 2, H // 2 + 150), (120, 220, 255))
        elif self.state in ("pause", "over"):
            self._overlay(s, 170)
            if self.state == "pause":
                text(s, "DURAKLATILDI", 64, (W // 2, 220), GOLD, outline=4)
                opts = ["Devam Et", "Ana Menü"]
            else:
                text(s, "OYUN BİTTİ", 76, (W // 2, 200), (255, 80, 80), outline=4)
                text(s, f"Skor: {self.score}", 36, (W // 2, 280), WHITE)
                if self.new_best:
                    text(s, "YENİ REKOR!", 34, (W // 2, 325), GOLD, outline=2)
                opts = ["Tekrar Oyna", "Ana Menü"]
            for i, opt in enumerate(opts):
                sel = i == self.menu_i
                r = pygame.Rect(W // 2 - 170, 380 + i * 70, 340, 54)
                pygame.draw.rect(s, (60, 30, 90) if sel else (25, 18, 40), r, border_radius=12)
                if sel:
                    pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
                text(s, opt, 28, r.center, WHITE if sel else (170, 160, 190))

    def _overlay(self, s, a):
        o = pygame.Surface((W, H), pygame.SRCALPHA)
        o.fill((5, 0, 15, a))
        s.blit(o, (0, 0))


def neon_rect(s, rect, color, width=3, radius=6, glow=True):
    if glow:
        g = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
        for i in range(4):
            pygame.draw.rect(g, color + (28,), pygame.Rect(12 - i * 3, 12 - i * 3, rect.w + i * 6, rect.h + i * 6),
                             border_radius=radius + i * 3)
        s.blit(g, (rect.x - 12, rect.y - 12))
    pygame.draw.rect(s, color, rect, width, border_radius=radius)
