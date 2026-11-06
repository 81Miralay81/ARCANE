"""Kanatix Arcade ana menüsü ve ayarlar."""
import math
import random

import pygame

from engine.core import (GOLD, WHITE, W, H, VERSION, Scene, blit_glow, draw_kanatix_logo, is_back, is_confirm, nav_dir,
                         text, vgradient)


class MainMenu(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.i = 0
        self.bg = vgradient(W, H, (10, 6, 30), (60, 12, 50))
        self.stars = [(random.uniform(0, W), random.uniform(0, H * 0.6), random.random()) for _ in range(120)]
        self.items = [
            ("DÖVÜŞ ARENASI", "1 Oyuncu — bilgisayara karşı", self.fight_1p),
            ("DÖVÜŞ ARENASI  2P", "2 Oyuncu — aynı klavyede", self.fight_2p),
            ("NEON YILAN", "Klasik yılan oyunu", lambda: self.open("snake")),
            ("TUĞLA KIRICI", "Raketle tuğlaları kır", lambda: self.open("breakout")),
            ("UZAY İSTİLASI", "Uzaylılara karşı savun", lambda: self.open("invaders")),
            ("NEON PONG", "Bilgisayara ya da arkadaşına karşı", lambda: self.open("pong")),
            ("AYARLAR", "Ses, zorluk, tam ekran", lambda: self.app.push(Settings(self.app))),
            ("ÇIKIŞ", "", self.quit),
        ]

    def on_enter(self):
        self.app.audio.play_music("menu")

    def fight_1p(self):
        from games.fighter.scene import FighterSelect
        self.app.push(FighterSelect(self.app, False))

    def fight_2p(self):
        from games.fighter.scene import FighterSelect
        self.app.push(FighterSelect(self.app, True))

    def open(self, name):
        if name == "snake":
            from games.snake import SnakeGame as G
        elif name == "breakout":
            from games.breakout import BreakoutGame as G
        elif name == "invaders":
            from games.invaders import InvadersGame as G
        else:
            from games.pong import PongGame as G
        self.app.push(G(self.app))

    def quit(self):
        self.app.running = False

    def handle(self, e):
        fu = getattr(self.app, "forced_update", None)
        if fu:
            if is_confirm(e) or e.type == pygame.MOUSEBUTTONDOWN:
                from engine.updater import open_url
                open_url(fu[1])
            return
        d = nav_dir(e)
        if d and d[1]:
            self.i = (self.i + d[1]) % len(self.items)
            self.app.audio.play("menu")
        elif is_confirm(e):
            self.app.audio.play("select")
            self.items[self.i][2]()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.i = len(self.items) - 1
            self.app.audio.play("back")
        elif e.type == pygame.MOUSEMOTION or e.type == pygame.MOUSEBUTTONDOWN:
            for idx in range(len(self.items)):
                if self.item_rect(idx).collidepoint(e.pos):
                    if idx != self.i and e.type == pygame.MOUSEMOTION:
                        self.i = idx
                        self.app.audio.play("menu")
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        self.i = idx
                        self.app.audio.play("select")
                        self.items[idx][2]()
                    break

    def update(self, dt):
        self.t += dt

    def item_rect(self, idx):
        return pygame.Rect(W // 2 + 40, 150 + idx * 62, 520, 52)

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        for x, y, k in self.stars:
            b = int(110 + 100 * math.sin(self.t * 2 + k * 40))
            s.set_at((int(x), int(y)), (b, b, min(255, b + 40)))
        # retro güneş
        cx, cy = 330, 430
        blit_glow(s, (cx, cy), 330, (90, 30, 60), 1.0)
        for i in range(18):
            y = cy - 170 + i * 19
            if y > cy + 10:
                break
            w = int(2 * math.sqrt(max(0, 170 ** 2 - (y - cy) ** 2)))
            col = (255, int(200 - i * 8), int(80 + i * 6))
            gap = max(0, (i - 8)) // 2 + 1 if i > 8 else 0
            pygame.draw.rect(s, col, (cx - w // 2, y, w, 19 - gap))
        # ızgara zemin
        hor = 440
        pygame.draw.rect(s, (16, 6, 30), (0, hor, W, H - hor))
        for i in range(16):
            yy = hor + (i ** 2) * 1.3 + (self.t * 40 % 30) * (i / 16)
            if yy < H:
                pygame.draw.line(s, (200, 50, 160), (0, yy), (W, yy), 2)
        for i in range(-20, 21):
            pygame.draw.line(s, (200, 50, 160), (W / 2 + i * 30, hor), (W / 2 + i * 180, H), 2)
        pygame.draw.line(s, (255, 120, 220), (0, hor), (W, hor), 3)
        # logo
        draw_kanatix_logo(s, (150, 110), 0.9, self.t)
        text(s, "KANATIX", 70, (225, 90), (255, 190, 70), anchor="midleft", outline=4)
        text(s, "A R C A D E", 34, (230, 145), (120, 220, 255), anchor="midleft", outline=2)
        # menü öğeleri
        for idx, (title, sub, _) in enumerate(self.items):
            r = self.item_rect(idx)
            sel = idx == self.i
            if sel:
                pulse = 0.5 + 0.5 * math.sin(self.t * 6)
                blit_glow(s, r.center, 200, (50, 20, 60), 1.0)
                pygame.draw.rect(s, (60, 26, 96), r, border_radius=14)
                pygame.draw.rect(s, (255, int(180 + 60 * pulse), 80), r, 3, border_radius=14)
                text(s, "►", 28, (r.left - 26, r.centery), GOLD)
            else:
                pygame.draw.rect(s, (24, 14, 40), r, border_radius=14)
            text(s, title, 28, (r.left + 22, r.centery - (8 if sel and sub else 0)), WHITE if sel else (180, 170, 200),
                 anchor="midleft")
            if sel and sub:
                text(s, sub, 17, (r.left + 24, r.centery + 15), (190, 210, 255), anchor="midleft", shadow=False)
        text(s, f"v{VERSION}   •   ↑↓ seç   ENTER başlat   F11 tam ekran", 18, (W // 2, H - 20), (190, 170, 220))
        fu = getattr(self.app, "forced_update", None)
        if fu:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((5, 0, 15, 225))
            s.blit(ov, (0, 0))
            text(s, "YENİ SÜRÜM VAR", 60, (W // 2, 230), GOLD, outline=4)
            text(s, f"Kanatix Arcade {fu[0]} yayınlandı. Devam etmek için güncellemen gerekiyor.", 24, (W // 2, 310), WHITE)
            r = pygame.Rect(W // 2 - 190, 380, 380, 76)
            pygame.draw.rect(s, (60, 26, 96), r, border_radius=16)
            pygame.draw.rect(s, GOLD, r, 3, border_radius=16)
            text(s, "GÜNCELLE", 36, r.center, WHITE)
            text(s, "Dokununca yeni APK indirilir; indirdikten sonra dosyayı açıp kur.", 18, (W // 2, 490), (190, 180, 220))
        status = getattr(self.app, "update_status", None)
        if status:
            pygame.draw.rect(s, (20, 10, 40), (0, 0, W, 34))
            text(s, status, 20, (W // 2, 17), GOLD)


class Settings(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.i = 0
        self.bg = vgradient(W, H, (10, 6, 30), (40, 12, 50))

    def rows(self):
        st = self.app.save.settings
        diff = ["KOLAY", "NORMAL", "ZOR"][st.get("difficulty", 1)]
        return [
            ("Efekt Sesi", f"{int(st.get('volume', 0.7) * 100)}%"),
            ("Müzik", f"{int(st.get('music', 0.5) * 100)}%"),
            ("Bilgisayar Zorluğu", diff),
            ("Tam Ekran", "AÇIK" if st.get("fullscreen") else "KAPALI"),
            ("Dokunmatik Kontroller", {"auto": "OTOMATİK", "on": "AÇIK", "off": "KAPALI"}[st.get("touch", "auto")]),
            ("Geri", ""),
        ]

    def handle(self, e):
        st = self.app.save.settings
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for idx in range(len(self.rows())):
                if pygame.Rect(W // 2 - 300, 190 + idx * 70, 600, 58).collidepoint(e.pos):
                    self.i = idx
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                    break
            else:
                return
        if is_back(e):
            self.app.save.save()
            self.app.pop()
            return
        d = nav_dir(e)
        if d and d[1]:
            self.i = (self.i + d[1]) % 6
            self.app.audio.play("menu")
        elif (d and d[0]) or is_confirm(e):
            dx = d[0] if d and d[0] else 1
            if self.i == 0:
                st["volume"] = round(max(0, min(1, st.get("volume", 0.7) + dx * 0.1)), 1)
                self.app.audio.play("coin")
            elif self.i == 1:
                st["music"] = round(max(0, min(1, st.get("music", 0.5) + dx * 0.1)), 1)
                self.app.audio.refresh_volume()
            elif self.i == 2:
                st["difficulty"] = (st.get("difficulty", 1) + dx) % 3
                self.app.audio.play("menu")
            elif self.i == 3:
                self.app.toggle_fullscreen()
            elif self.i == 4:
                order = ["auto", "on", "off"]
                st["touch"] = order[(order.index(st.get("touch", "auto")) + dx) % 3]
                from engine.touch import is_android
                self.app.touch_mode = st["touch"] == "on" or (st["touch"] == "auto" and is_android())
                self.app.audio.play("menu")
            elif self.i == 5 and is_confirm(e):
                self.app.save.save()
                self.app.pop()
            self.app.save.save()

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        text(s, "AYARLAR", 64, (W // 2, 110), GOLD, outline=4)
        for idx, (k, v) in enumerate(self.rows()):
            r = pygame.Rect(W // 2 - 300, 190 + idx * 70, 600, 58)
            sel = idx == self.i
            pygame.draw.rect(s, (60, 26, 96) if sel else (24, 14, 40), r, border_radius=14)
            if sel:
                pygame.draw.rect(s, GOLD, r, 3, border_radius=14)
            text(s, k, 28, (r.left + 26, r.centery), WHITE, anchor="midleft")
            if v:
                text(s, f"◄  {v}  ►" if sel else v, 28, (r.right - 26, r.centery), (120, 220, 255), anchor="midright")
        text(s, "← → değiştir   •   ESC geri", 20, (W // 2, H - 40), (190, 170, 220))
