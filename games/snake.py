"""Neon Yılan."""
import random

import pygame

from engine.core import GOLD, W, H, blit_glow, lerp_color, text
from games.arcade_base import ArcadeGame, neon_rect

CELL = 28
COLS, ROWS = 36, 21
OX = (W - COLS * CELL) // 2
OY = 90


class SnakeGame(ArcadeGame):
    key = "yilan"
    title = "NEON YILAN"
    help = "Yön tuşları / WASD ile yönlendir\nElmaları ye, büyü, kendine ve duvara çarpma\nAltın elma = 5 puan + hız"
    grid_color = (20, 60, 50)
    bg_top = (5, 18, 20)
    bg_bottom = (10, 30, 40)

    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.body = [(cx - i, cy) for i in range(4)]
        self.dir = (1, 0)
        self.queue = []
        self.step_t = 0.0
        self.speed = 8.0
        self.food = None
        self.gold = None
        self.gold_t = 0
        self.place_food()

    def place_food(self, gold=False):
        free = [(x, y) for x in range(COLS) for y in range(ROWS) if (x, y) not in self.body]
        p = random.choice(free)
        if gold:
            self.gold = p
            self.gold_t = 7.0
        else:
            self.food = p

    def play_event(self, e):
        m = None
        if e.type == pygame.KEYDOWN:
            m = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
                 pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}.get(e.key)
        elif e.type == pygame.JOYHATMOTION and e.value != (0, 0):
            m = (e.value[0], -e.value[1]) if e.value[0] == 0 or e.value[1] == 0 else None
        if m:
            last = self.queue[-1] if self.queue else self.dir
            if (m[0] != -last[0] or m[1] != -last[1]) and m != last and len(self.queue) < 3:
                self.queue.append(m)

    def play_update(self, dt):
        if self.gold:
            self.gold_t -= dt
            if self.gold_t <= 0:
                self.gold = None
        self.step_t += dt
        if self.step_t < 1 / self.speed:
            return
        self.step_t = 0
        if self.queue:
            self.dir = self.queue.pop(0)
        hx, hy = self.body[0]
        nh = (hx + self.dir[0], hy + self.dir[1])
        if not (0 <= nh[0] < COLS and 0 <= nh[1] < ROWS) or nh in self.body[:-1]:
            px, py = self.cell_center(self.body[0])
            self.parts.emit(px, py, 60, (80, 255, 160), speed=7, life=40, size=5, glow=True)
            self.shake = 12
            self.app.audio.play("boom")
            self.game_over()
            return
        self.body.insert(0, nh)
        if nh == self.food:
            self.score += 1
            self.app.audio.play("eat")
            px, py = self.cell_center(nh)
            self.parts.emit(px, py, 20, (255, 80, 100), speed=4, life=24, size=4, glow=True)
            self.place_food()
            self.speed = min(18, self.speed + 0.25)
            if self.gold is None and random.random() < 0.18:
                self.place_food(gold=True)
        elif self.gold and nh == self.gold:
            self.score += 5
            self.app.audio.play("powerup")
            px, py = self.cell_center(nh)
            self.parts.emit(px, py, 36, GOLD, speed=6, life=30, size=5, glow=True)
            self.gold = None
            self.speed = min(18, self.speed + 0.8)
            self.body.extend([self.body[-1]] * 2)
        else:
            self.body.pop()

    def cell_center(self, c):
        return OX + c[0] * CELL + CELL // 2, OY + c[1] * CELL + CELL // 2

    def play_draw(self, s):
        board = pygame.Rect(OX, OY, COLS * CELL, ROWS * CELL)
        pygame.draw.rect(s, (6, 16, 20), board)
        for x in range(COLS + 1):
            pygame.draw.line(s, (14, 34, 40), (OX + x * CELL, OY), (OX + x * CELL, board.bottom))
        for y in range(ROWS + 1):
            pygame.draw.line(s, (14, 34, 40), (OX, OY + y * CELL), (board.right, OY + y * CELL))
        neon_rect(s, board.inflate(6, 6), (60, 255, 180), 3)
        # yem
        if self.food:
            px, py = self.cell_center(self.food)
            pulse = 1 + 0.15 * __import__("math").sin(self.t * 8)
            blit_glow(s, (px, py), 30, (120, 20, 40))
            pygame.draw.circle(s, (255, 70, 90), (px, py), int(10 * pulse))
            pygame.draw.circle(s, (255, 180, 190), (px - 3, py - 3), 3)
            pygame.draw.line(s, (80, 200, 80), (px, py - 10), (px + 4, py - 15), 3)
        if self.gold:
            px, py = self.cell_center(self.gold)
            blit_glow(s, (px, py), 40, (120, 90, 10))
            pygame.draw.circle(s, GOLD, (px, py), 11)
            pygame.draw.circle(s, (255, 250, 200), (px - 3, py - 3), 4)
            text(s, f"{max(0, self.gold_t):.0f}", 16, (px, py - 22), GOLD)
        # yılan
        n = len(self.body)
        for i in range(n - 1, -1, -1):
            px, py = self.cell_center(self.body[i])
            col = lerp_color((90, 255, 170), (20, 120, 160), i / max(1, n))
            r = CELL // 2 - 1 if i == 0 else int(CELL / 2 - 2 - 4 * i / max(1, n))
            if i < n - 1:
                qx, qy = self.cell_center(self.body[i + 1])
                if abs(qx - px) <= CELL and abs(qy - py) <= CELL:
                    pygame.draw.line(s, col, (px, py), (qx, qy), r * 2)
            pygame.draw.circle(s, col, (px, py), r)
        hx, hy = self.cell_center(self.body[0])
        blit_glow(s, (hx, hy), 34, (20, 90, 60))
        dx, dy = self.dir
        for side in (-1, 1):
            ex = hx + dx * 5 + (-dy) * side * 6
            ey = hy + dy * 5 + dx * side * 6
            pygame.draw.circle(s, (255, 255, 255), (ex, ey), 4)
            pygame.draw.circle(s, (10, 10, 20), (ex + dx * 1.5, ey + dy * 1.5), 2)
