"""Tuğla Kırıcı."""
import math
import random

import pygame

from engine.core import GOLD, WHITE, W, H, blit_glow, lerp_color, shade, text
from games.arcade_base import ArcadeGame, neon_rect

ROW_COLORS = [(255, 70, 110), (255, 150, 60), (255, 220, 70), (90, 230, 120), (70, 200, 255), (160, 110, 255)]


class BreakoutGame(ArcadeGame):
    key = "tugla"
    title = "TUĞLA KIRICI"
    help = "← → / A D ile raketi kaydır, BOŞLUK ile topu fırlat\nTüm tuğlaları kır, düşen güçlendirmeleri yakala\nGeniş raket • Çoklu top • Ekstra can"
    grid_color = (60, 30, 80)

    def reset(self):
        self.level = 1
        self.lives = 3
        self.build_level()

    def build_level(self):
        self.paddle = pygame.Rect(W // 2 - 70, H - 70, 140, 16)
        self.paddle_w = 140
        self.wide_t = 0
        self.balls = []
        self.stuck = True
        self.bricks = []
        cols, rows = 14, 6 + min(3, self.level - 1)
        bw, bh = 78, 26
        x0 = (W - cols * (bw + 6)) // 2 + 3
        for r in range(rows):
            for c in range(cols):
                if self.level % 2 == 0 and (r + c) % 5 == 0:
                    continue
                hp = 2 if (self.level >= 2 and r < 2) else 1
                self.bricks.append(dict(rect=pygame.Rect(x0 + c * (bw + 6), 100 + r * (bh + 8), bw, bh),
                                        color=ROW_COLORS[r % len(ROW_COLORS)], hp=hp))
        self.drops = []
        self.new_ball()

    def new_ball(self):
        self.balls = [dict(x=self.paddle.centerx, y=self.paddle.top - 10, vx=0.0, vy=0.0, trail=[])]
        self.stuck = True

    def launch(self):
        if self.stuck:
            sp = 7.0 + self.level * 0.6
            a = random.uniform(-0.5, 0.5)
            for b in self.balls:
                b["vx"], b["vy"] = math.sin(a) * sp, -math.cos(a) * sp
            self.stuck = False
            self.app.audio.play("bounce")

    def play_event(self, e):
        if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.PAUSE_RECT.collidepoint(e.pos)) or \
                (e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)) or \
                (e.type == pygame.JOYBUTTONDOWN and e.button == 0):
            self.launch()

    def play_update(self, dt):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        for j in self.app.joysticks[:1]:
            try:
                ax = j.get_axis(0)
                if abs(ax) > 0.3:
                    dx = ax
                if j.get_numhats():
                    dx = dx or j.get_hat(0)[0]
            except Exception:
                pass
        self.paddle.x += int(dx * 11)
        if pygame.mouse.get_pressed()[0]:
            mx = pygame.mouse.get_pos()[0]
            self.paddle.centerx += int(max(-16, min(16, (mx - self.paddle.centerx) * 0.35)))
        if self.wide_t > 0:
            self.wide_t -= dt
            target = 220
        else:
            target = 140
        self.paddle_w += (target - self.paddle_w) * 0.2
        c = self.paddle.centerx
        self.paddle.w = int(self.paddle_w)
        self.paddle.centerx = c
        self.paddle.clamp_ip(pygame.Rect(20, 0, W - 40, H))
        if self.stuck:
            for b in self.balls:
                b["x"], b["y"] = self.paddle.centerx, self.paddle.top - 10
        R = 9
        for b in self.balls:
            if self.stuck:
                continue
            steps = 3
            for _ in range(steps):
                b["x"] += b["vx"] / steps
                b["y"] += b["vy"] / steps
                if b["x"] < 20 + R or b["x"] > W - 20 - R:
                    b["vx"] *= -1
                    b["x"] = max(20 + R, min(W - 20 - R, b["x"]))
                    self.app.audio.play("bounce", 0.5)
                if b["y"] < 70 + R:
                    b["vy"] = abs(b["vy"])
                    self.app.audio.play("bounce", 0.5)
                br = pygame.Rect(b["x"] - R, b["y"] - R, R * 2, R * 2)
                if br.colliderect(self.paddle) and b["vy"] > 0:
                    off = (b["x"] - self.paddle.centerx) / (self.paddle.w / 2)
                    sp = math.hypot(b["vx"], b["vy"]) * 1.01
                    sp = min(sp, 15)
                    a = off * 1.05
                    b["vx"], b["vy"] = math.sin(a) * sp, -abs(math.cos(a) * sp)
                    self.app.audio.play("bounce")
                    self.parts.emit(b["x"], self.paddle.top, 6, (120, 220, 255), speed=3, life=14, size=3)
                for br_ in self.bricks:
                    if br.colliderect(br_["rect"]):
                        r = br_["rect"]
                        ox = min(br.right - r.left, r.right - br.left)
                        oy = min(br.bottom - r.top, r.bottom - br.top)
                        if ox < oy:
                            b["vx"] *= -1
                        else:
                            b["vy"] *= -1
                        self.hit_brick(br_)
                        break
            b["trail"].append((b["x"], b["y"]))
            b["trail"] = b["trail"][-10:]
        self.bricks = [x for x in self.bricks if x["hp"] > 0]
        alive = [b for b in self.balls if b["y"] < H + 20]
        if not alive and not self.stuck:
            self.lives -= 1
            self.shake = 10
            self.app.audio.play("lose" if self.lives <= 0 else "boom")
            if self.lives <= 0:
                self.game_over()
                return
            self.new_ball()
        else:
            self.balls = alive or self.balls
        for d in self.drops:
            d["y"] += 3.2
            if pygame.Rect(d["x"] - 16, d["y"] - 10, 32, 20).colliderect(self.paddle):
                d["y"] = H + 100
                self.app.audio.play("powerup")
                self.score += 50
                if d["k"] == "W":
                    self.wide_t = 12
                elif d["k"] == "M":
                    nb = []
                    for b in self.balls[:2]:
                        for a in (-0.4, 0.4):
                            sp = max(6, math.hypot(b["vx"], b["vy"]))
                            ang = math.atan2(b["vx"], -b["vy"]) + a
                            nb.append(dict(x=b["x"], y=b["y"], vx=math.sin(ang) * sp, vy=-abs(math.cos(ang) * sp), trail=[]))
                    self.balls.extend(nb)
                else:
                    self.lives = min(5, self.lives + 1)
        self.drops = [d for d in self.drops if d["y"] < H + 30]
        if not self.bricks:
            self.level += 1
            self.score += 500
            self.app.audio.play("win")
            self.build_level()

    def hit_brick(self, b):
        b["hp"] -= 1
        r = b["rect"]
        self.app.audio.play("brick")
        if b["hp"] <= 0:
            self.score += 10 * self.level
            self.parts.emit(r.centerx, r.centery, 16, b["color"], speed=5, life=26, size=4, glow=True)
            if random.random() < 0.12:
                self.drops.append(dict(x=r.centerx, y=r.centery, k=random.choice("WWMML")))
        else:
            self.parts.emit(r.centerx, r.centery, 6, WHITE, speed=3, life=12, size=3)

    def play_draw(self, s):
        sx = random.randint(-self.shake, self.shake) if self.shake else 0
        neon_rect(s, pygame.Rect(16 + sx, 66, W - 32, H - 40), (180, 90, 255), 3)
        for b in self.bricks:
            r = b["rect"].move(sx, 0)
            c = b["color"] if b["hp"] == 1 else shade(b["color"], 0.65)
            pygame.draw.rect(s, shade(c, 0.5), r.move(0, 4), border_radius=6)
            pygame.draw.rect(s, c, r, border_radius=6)
            pygame.draw.rect(s, shade(c, 1.35), (r.x + 4, r.y + 3, r.w - 8, 6), border_radius=3)
            if b["hp"] > 1:
                pygame.draw.rect(s, WHITE, r, 2, border_radius=6)
        for d in self.drops:
            col = {"W": (90, 200, 255), "M": (255, 120, 220), "L": (255, 80, 80)}[d["k"]]
            rr = pygame.Rect(d["x"] - 18, d["y"] - 11, 36, 22)
            blit_glow(s, rr.center, 30, shade(col, 0.4))
            pygame.draw.rect(s, col, rr, border_radius=11)
            text(s, {"W": "↔", "M": "×3", "L": "♥"}[d["k"]], 18, rr.center, (20, 10, 30), shadow=False)
        p = self.paddle.move(sx, 0)
        blit_glow(s, p.center, p.w // 2 + 20, (20, 60, 90))
        pygame.draw.rect(s, (80, 210, 255), p, border_radius=8)
        pygame.draw.rect(s, (200, 245, 255), (p.x + 6, p.y + 3, p.w - 12, 4), border_radius=2)
        for b in self.balls:
            for i, (tx, ty) in enumerate(b["trail"]):
                k = i / max(1, len(b["trail"]))
                pygame.draw.circle(s, lerp_color((40, 20, 80), (255, 220, 120), k), (int(tx) + sx, int(ty)), int(2 + 6 * k))
            blit_glow(s, (int(b["x"]) + sx, int(b["y"])), 26, (90, 70, 20))
            pygame.draw.circle(s, WHITE, (int(b["x"]) + sx, int(b["y"])), 9)
        for i in range(self.lives):
            pygame.draw.circle(s, (255, 80, 100), (W // 2 - (self.lives - 1) * 14 + i * 28, 32), 9)
        text(s, f"SEVİYE {self.level}", 22, (W // 2 + 140, 32), GOLD, anchor="midleft")
        if self.stuck and self.state == "play":
            text(s, "BOŞLUK: Fırlat", 22, (W // 2, H - 30), (180, 220, 255))
