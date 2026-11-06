"""Neon Pong: bilgisayara karşı ya da iki oyunculu."""
import math
import random

import pygame

from engine.core import GOLD, WHITE, W, H, blit_glow, text
from games.arcade_base import ArcadeGame, neon_rect

WIN_SCORE = 7


class PongGame(ArcadeGame):
    key = "pong"
    title = "NEON PONG"
    help = "Sol oyuncu: W / S     Sağ oyuncu: ↑ / ↓\nSağ tarafa kimse basmazsa bilgisayar oynar\n7 sayıya ulaşan kazanır"
    grid_color = (20, 40, 90)

    def __init__(self, app, net=None):
        self.net = net
        self.rng = random.Random(net.seed + net.round if net else None)
        self.net_in = (0.0, 0.0)
        self.acc = 0.0
        super().__init__(app)
        if net:
            self.state = "play"

    def reset(self):
        self.pl = pygame.Rect(50, H // 2 - 60, 16, 120)
        self.pr = pygame.Rect(W - 66, H // 2 - 60, 16, 120)
        self.sl = self.sr = 0
        self.human_r = bool(self.net)
        self.serve(self.rng.choice((-1, 1)))
        self.winner = None

    def serve(self, d):
        self.bx, self.by = W / 2, H / 2 + 20
        a = self.rng.uniform(-0.5, 0.5)
        self.vx, self.vy = math.cos(a) * 7 * d, math.sin(a) * 7
        self.wait = 50
        self.trail = []

    def local_dy(self):
        """Ağ oyununda bu bilgisayarın raket hareketi (-1..1)."""
        keys = pygame.key.get_pressed()
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        pad = self.pl if self.net.side == 0 else self.pr
        if pygame.mouse.get_pressed()[0]:
            my = pygame.mouse.get_pos()[1]
            dy = max(-1.4, min(1.4, (my - pad.centery) * 0.04))
        for j in self.app.joysticks[:1]:
            try:
                ay = j.get_axis(1)
                if abs(ay) > 0.3:
                    dy = ay
            except Exception:
                pass
        return round(float(dy), 3)

    def update(self, dt):
        if not self.net:
            return super().update(dt)
        from engine.net import INPUT_DELAY
        ls = self.net
        ls.pump()
        msgs, ls.remote_msgs = ls.remote_msgs, []
        for m in msgs:
            if m.get("t") == "bye":
                ls.disconnected = True
            elif m.get("t") == "menu" and ls.side == 1:
                self.net_choice(m["c"])
                return
        self.t += dt
        self.state_t += dt
        self.parts.update()
        if self.shake > 0:
            self.shake -= 1
        if ls.disconnected or self.state != "play":
            return
        self.acc += min(dt, 1 / 20)
        STEP = 1 / 60
        n = 0
        while self.acc >= STEP and n < 4:
            if ls.frame + INPUT_DELAY > ls.sent_upto:
                ls.push_local(self.local_dy())
            ls.pump()
            if not ls.ready():
                break
            a, b = ls.take()
            self.net_in = (a or 0.0, b or 0.0)
            self.play_update(STEP)
            ls.checksum(round(self.bx + self.by + self.pl.y + self.pr.y, 1))
            self.acc -= STEP
            n += 1
            if self.state != "play":
                break
        if self.acc > STEP * 4:
            self.acc = STEP * 4

    def net_choice(self, c):
        if c == "again":
            self.net = self.net.restart()
            self.rng = random.Random(self.net.seed + self.net.round)
            self.score = 0
            self.reset()
            self.state = "play"
            self.acc = 0.0
        else:
            self.app.pop()

    def handle(self, e):
        if not self.net:
            return super().handle(e)
        esc = e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_AC_BACK)
        if esc or (self.net.disconnected and (e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN)):
            self.net.conn.send({"t": "bye"})
            self.app.pop()
            return
        if self.state == "over" and self.net.side == 0 and self.state_t > 1.0:
            from engine.core import is_confirm, nav_dir
            tap = e.pos if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) else None
            if tap:
                for i in range(2):
                    if pygame.Rect(W // 2 - 170, 380 + i * 70, 340, 54).collidepoint(tap):
                        self.menu_i = i
                        e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            d = nav_dir(e)
            if d and d[1]:
                self.menu_i = (self.menu_i + d[1]) % 2
            elif is_confirm(e):
                c = "again" if self.menu_i == 0 else "leave"
                self.net.conn.send({"t": "menu", "c": c})
                self.net_choice(c)

    def play_update(self, dt):
        if self.net:
            dl, dr = self.net_in
            self.pl.y += int(dl * 10)
            self.pr.y += int(dr * 10)
            self.human_r = True
            self._ball_step()
            return
        keys = pygame.key.get_pressed()
        dl = keys[pygame.K_s] - keys[pygame.K_w]
        dr = keys[pygame.K_DOWN] - keys[pygame.K_UP]
        if dr:
            self.human_r = True
        js = self.app.joysticks
        try:
            if js:
                ay = js[0].get_axis(1) if js[0].get_numaxes() > 1 else 0
                if abs(ay) > 0.3:
                    dl = ay
            if len(js) > 1:
                ay = js[1].get_axis(1) if js[1].get_numaxes() > 1 else 0
                if abs(ay) > 0.3:
                    dr = ay
                    self.human_r = True
        except Exception:
            pass
        self.pl.y += int(dl * 10)
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if mx < W // 2:
                self.pl.centery += int(max(-14, min(14, (my - self.pl.centery) * 0.4)))
        if self.human_r:
            self.pr.y += int(dr * 10)
        else:
            target = self.by if self.vx > 0 else H / 2
            diff = target - self.pr.centery
            self.pr.y += int(max(-7.5, min(7.5, diff * 0.12)))
        self._ball_step()

    def _ball_step(self):
        for p in (self.pl, self.pr):
            p.clamp_ip(pygame.Rect(0, 80, W, H - 110))
        if self.wait > 0:
            self.wait -= 1
            return
        self.bx += self.vx
        self.by += self.vy
        if self.by < 90 or self.by > H - 40:
            self.vy *= -1
            self.by = max(90, min(H - 40, self.by))
            self.app.audio.play("bounce", 0.5)
        br = pygame.Rect(self.bx - 10, self.by - 10, 20, 20)
        for p, d in ((self.pl, 1), (self.pr, -1)):
            if br.colliderect(p) and self.vx * d < 0:
                off = (self.by - p.centery) / (p.h / 2)
                sp = min(17, math.hypot(self.vx, self.vy) * 1.06)
                a = off * 0.9
                self.vx, self.vy = math.cos(a) * sp * d, math.sin(a) * sp
                self.app.audio.play("bounce")
                self.parts.emit(self.bx, self.by, 14, (90, 220, 255) if d > 0 else (255, 90, 200), speed=5, life=20,
                                size=4, glow=True)
                self.shake = 4
                if d > 0:
                    self.score += 1
        self.trail.append((self.bx, self.by))
        self.trail = self.trail[-14:]
        if self.bx < -20 or self.bx > W + 20:
            left_scored = self.bx > W
            if left_scored:
                self.sl += 1
                self.score += 10
            else:
                self.sr += 1
            self.app.audio.play("coin" if left_scored else "boom")
            self.parts.emit(max(0, min(W, self.bx)), self.by, 40, GOLD, speed=7, life=34, size=5, glow=True)
            self.shake = 10
            if self.sl >= WIN_SCORE or self.sr >= WIN_SCORE:
                if self.sl >= WIN_SCORE:
                    self.score += 100
                self.game_over()
                if self.sl >= WIN_SCORE:
                    self.app.audio.play("win")
                return
            self.serve(-1 if left_scored else 1)

    def play_draw(self, s):
        neon_rect(s, pygame.Rect(20, 76, W - 40, H - 100), (80, 120, 255), 3)
        for y in range(90, H - 30, 30):
            pygame.draw.rect(s, (60, 80, 160), (W // 2 - 2, y, 4, 16))
        text(s, str(self.sl), 90, (W // 2 - 120, 160), (90, 220, 255), outline=3)
        text(s, str(self.sr), 90, (W // 2 + 120, 160), (255, 90, 200), outline=3)
        lbl = "2. OYUNCU" if self.human_r else "BİLGİSAYAR"
        text(s, "1. OYUNCU", 20, (W // 2 - 120, 220), (150, 200, 230))
        text(s, lbl, 20, (W // 2 + 120, 220), (230, 150, 210))
        for p, c in ((self.pl, (90, 220, 255)), (self.pr, (255, 90, 200))):
            blit_glow(s, p.center, 80, tuple(v // 4 for v in c))
            pygame.draw.rect(s, c, p, border_radius=8)
            pygame.draw.rect(s, WHITE, p.inflate(-10, -10), border_radius=4)
        for i, (x, y) in enumerate(self.trail):
            k = i / len(self.trail)
            pygame.draw.circle(s, (int(80 * k), int(60 * k), int(160 * k)), (int(x), int(y)), int(3 + 7 * k))
        blit_glow(s, (int(self.bx), int(self.by)), 34, (80, 80, 40))
        pygame.draw.circle(s, WHITE, (int(self.bx), int(self.by)), 10)

    def game_over(self):
        super().game_over()
        self.winner = "1. OYUNCU" if self.sl >= WIN_SCORE else ("2. OYUNCU" if self.human_r else "BİLGİSAYAR")

    def draw(self, s):
        super().draw(s)
        if self.net:
            side = "SOL raket (W/S, ↑/↓)" if self.net.side == 0 else "SAĞ raket (W/S, ↑/↓)"
            text(s, "AĞ OYUNU  •  Sen: " + side + "  •  ESC: çık", 16, (W // 2, H - 14), (190, 210, 255))
            if self.net.disconnected:
                text(s, "BAĞLANTI KOPTU — bir tuşa bas", 40, (W // 2, H // 2), (255, 90, 90), outline=3)
            elif self.state == "over" and self.net.side == 1:
                text(s, "Kurucunun seçimi bekleniyor...", 22, (W // 2, 530), (200, 190, 230), outline=2)
        if self.state == "over" and self.winner:
            text(s, f"{self.winner} KAZANDI", 30, (W // 2, 140), GOLD, outline=2)
