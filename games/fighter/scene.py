"""Dövüş oyunu sahneleri: mod seçimi, karakter seçimi, dövüş, duraklatma."""
import math
import random

import pygame

from engine.core import (BLACK, CYAN, GOLD, RED, WHITE, W, H, Particles, Scene, blit_glow, font, is_back, is_confirm,
                         lerp_color, nav_dir, shade, text, vgradient)
from games.fighter.characters import CHARACTERS, MOTION_TEXT
from games.fighter.controls import KEYMAP_SOLO, KEYMAPS, CPUController, HumanController, NetController, key_names
from games.fighter.fighter import GROUND, MAX_METER, SUPER_COST, Fighter, InputState
from games.fighter.skeleton import POSES, blend, draw_fighter
from games.fighter import sprites
from games.fighter.stages import STAGE_W, STAGES

ROUND_TIME = 99
WIN_ROUNDS = 2


# ============================================================================ seçim ekranı
class FighterSelect(Scene):
    def __init__(self, app, two_player=False):
        super().__init__(app)
        self.two = two_player
        self.cur = [0, 1]
        self.done = [False, not two_player]
        self.stage_i = 0
        self.phase = "char"   # char -> stage
        self.t = 0.0
        self.bg = vgradient(W, H, (20, 10, 40), (60, 10, 30))
        self.preview_t = [0, 0]

    def on_enter(self):
        self.app.audio.play_music("menu")

    def char_rects(self):
        n = len(CHARACTERS)
        cw = 150
        x0 = W // 2 - (n * cw) // 2
        return [pygame.Rect(x0 + i * cw + 10, 560, cw - 20, 130) for i in range(n)]

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            x, y = e.pos
            if x < 160 and y < 90:
                e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
            elif self.phase == "char":
                for i, r in enumerate(self.char_rects()):
                    if r.collidepoint(x, y):
                        p = 0 if not self.done[0] else 1
                        if self.done[p]:
                            return
                        if self.cur[p] == i:
                            self.done[p] = True
                            self.app.audio.play("select")
                            if all(self.done):
                                if not self.two:
                                    self.cur[1] = random.choice([j for j in range(len(CHARACTERS)) if j != self.cur[0]])
                                self.phase = "stage"
                                self.stage_i = random.randrange(len(STAGES))
                        else:
                            self.cur[p] = i
                            self.preview_t[p] = 0
                            self.app.audio.play("menu")
                        return
                return
            else:
                if x < W // 3:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
                elif x > W * 2 // 3:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
                else:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        if is_back(e):
            self.app.audio.play("back")
            if self.phase == "stage":
                self.phase = "char"
                self.done = [False, not self.two]
            else:
                self.app.pop()
            return
        if self.phase == "char":
            player = None
            dx = 0
            confirm = False
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_a,) or (e.key == pygame.K_LEFT and not self.two):
                    player, dx = 0, -1
                elif e.key in (pygame.K_d,) or (e.key == pygame.K_RIGHT and not self.two):
                    player, dx = 0, 1
                elif e.key == pygame.K_LEFT and self.two:
                    player, dx = 1, -1
                elif e.key == pygame.K_RIGHT and self.two:
                    player, dx = 1, 1
                elif e.key in (pygame.K_f, pygame.K_RETURN, pygame.K_SPACE) and not (self.two and e.key == pygame.K_RETURN and self.done[0]):
                    player, confirm = 0, True
                    if self.two and self.done[0] and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        player = 1
                elif e.key in (pygame.K_k, pygame.K_KP1, pygame.K_RETURN) and self.two:
                    player, confirm = 1, True
            elif e.type == pygame.JOYHATMOTION and e.value[0]:
                player, dx = min(e.joy, 1), e.value[0]
            elif e.type == pygame.JOYBUTTONDOWN and e.button in (0, 2, 7):
                player, confirm = min(e.joy, 1), True
            if player is None or (player == 1 and not self.two):
                if player == 1 and not self.two:
                    return
                if player is None:
                    return
            if self.done[player] and dx:
                return
            if dx:
                self.cur[player] = (self.cur[player] + dx) % len(CHARACTERS)
                self.preview_t[player] = 0
                self.app.audio.play("menu")
            if confirm and not self.done[player]:
                self.done[player] = True
                self.app.audio.play("select")
                if all(self.done):
                    if not self.two:
                        # CPU rakibi: farklı bir karakter
                        others = [i for i in range(len(CHARACTERS)) if i != self.cur[0]]
                        self.cur[1] = random.choice(others)
                    self.phase = "stage"
                    self.stage_i = random.randrange(len(STAGES))
        else:
            d = nav_dir(e)
            if d and d[0]:
                self.stage_i = (self.stage_i + d[0]) % len(STAGES)
                self.app.audio.play("menu")
            elif is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_f, pygame.K_k)):
                self.app.audio.play("select")
                self.app.replace(FightScene(self.app, self.cur[0], self.cur[1], self.stage_i, self.two))

    def update(self, dt):
        self.t += dt
        self.preview_t = [p + dt for p in self.preview_t]

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        # hareketli çapraz şeritler
        for i in range(-4, 20):
            x = i * 90 + (self.t * 40) % 90
            pygame.draw.line(s, (40, 18, 60), (x, 0), (x - 300, H), 18)
        text(s, "KARAKTER SEÇ" if self.phase == "char" else "ARENA SEÇ", 52, (W // 2, 50), GOLD, outline=3)
        pygame.draw.rect(s, (40, 24, 60), (20, 20, 120, 46), border_radius=12)
        text(s, "◄ GERİ", 22, (80, 43), WHITE)
        if self.app.touch_mode:
            msg = "Karaktere dokun, onaylamak için tekrar dokun" if self.phase == "char" else "Sağa/sola dokunarak değiştir, ortaya dokunarak başla"
            text(s, msg, 20, (W // 2, 92), (190, 210, 255))
        text(s, "Karakter çizimleri: Sujal V Kanchan — StreetFighter2D-Game (MIT)", 13, (W - 12, 12), (130, 120, 160),
             anchor="topright", shadow=False)
        if self.phase == "char":
            self.draw_chars(s)
        else:
            self.draw_stages(s)

    def draw_chars(self, s):
        n = len(CHARACTERS)
        cw = 150
        x0 = W // 2 - (n * cw) // 2
        for i, ch in enumerate(CHARACTERS):
            r = pygame.Rect(x0 + i * cw + 10, 560, cw - 20, 130)
            pygame.draw.rect(s, (30, 20, 50), r, border_radius=12)
            clip = s.get_clip()
            s.set_clip(r)
            if ch.get("sprite"):
                sprites.draw_static(s, ch["sprite"], "Idle", int(self.t * 10), r.centerx, r.bottom + 70, 1, 0.55)
            else:
                draw_fighter(s, dict(ch, scale=ch["scale"] * 0.72), POSES["idle"], r.centerx, r.bottom + 38, 1, t=self.t)
            s.set_clip(clip)
            text(s, ch["name"], 22, (r.centerx, r.bottom - 14), WHITE)
            for p in (0, 1):
                if (p == 1 and not self.two) or self.cur[p] != i:
                    continue
                col = (255, 80, 80) if p == 0 else (80, 160, 255)
                pygame.draw.rect(s, col, r.inflate(8 + p * 8, 8 + p * 8), 4, border_radius=14)
                text(s, f"{p + 1}P", 20, (r.left + 18 + p * (r.w - 36), r.top + 16), col, outline=2)
        # büyük önizlemeler
        for p in (0, 1):
            if p == 1 and not self.two:
                continue
            ch = CHARACTERS[self.cur[p]]
            cx = 300 if p == 0 else W - 300
            facing = 1 if p == 0 else -1
            blit_glow(s, (cx, 380), 200, shade(ch["fx"], 0.35), 1.0)
            k = min(1, self.preview_t[p] * 3)
            pose = blend(POSES["taunt"], POSES["idle"], k) if not self.done[p] else POSES["win"]
            pal = ch["palette"] if not (self.two and p == 1 and self.cur[0] == self.cur[1]) else ch["alt"]
            big = dict(ch, scale=ch["scale"] * 1.75)
            pygame.draw.ellipse(s, (10, 5, 20), (cx - 110, 518, 220, 30))
            if ch.get("sprite"):
                if self.done[p]:
                    ss_ = sprites.get(ch["sprite"])
                    sprites.draw_static(s, ch["sprite"], "Attack_3", ss_.meta["peak"]["Attack_3"], cx, 540, facing, 1.35)
                else:
                    sprites.draw_static(s, ch["sprite"], "Idle", int(self.t * 10), cx, 540, facing, 1.35)
            else:
                draw_fighter(s, big, pose, cx, 530, facing, t=self.t, palette=pal, ss=1)
            tx = cx + (260 if p == 0 else -260)
            anchor = "midleft" if p == 0 else "midright"
            ax = tx - 60 if p == 0 else tx + 60
            text(s, ch["name"], 54, (ax, 150), WHITE, anchor=anchor, outline=3)
            text(s, ch["title"], 26, (ax, 195), shade(ch["fx"], 1.1), anchor=anchor)
            self._wrap(s, ch["desc"], ax, 235, anchor, 340)
            stats = [("GÜÇ", ch["power"] / 1.25), ("HIZ", ch["speed"] / 5.4), ("CAN", ch["health"] / 1200)]
            for j, (lab, v) in enumerate(stats):
                y = 320 + j * 34
                text(s, lab, 20, (ax, y), (200, 200, 220), anchor=anchor)
                bx = ax + 50 if p == 0 else ax - 50 - 200
                pygame.draw.rect(s, (40, 30, 60), (bx, y - 8, 200, 16), border_radius=8)
                pygame.draw.rect(s, ch["fx"], (bx, y - 8, int(200 * min(1, v)), 16), border_radius=8)
            # özel hareketler
            kn = key_names(self.two, p)
            btn = {"P": kn["P"], "K": kn["K"]}
            rows = [(sp["name"], MOTION_TEXT[sp["motion"]] + " + " + btn[sp["button"]]) for sp in ch["specials"]]
            rows.append(("SÜPER: " + ch["super"]["name"], MOTION_TEXT[ch["super"]["motion"]] + " + " + btn[ch["super"]["button"]]))
            for j, (nm, cmd) in enumerate(rows):
                yy = 428 + j * 27
                if p == 0:
                    text(s, nm, 19, (ax, yy), GOLD if j == 3 else WHITE, anchor="midleft")
                    text(s, cmd if not self.app.touch_mode else "", 19, (ax + 250, yy), CYAN, anchor="midleft")
                else:
                    text(s, nm, 19, (ax, yy), GOLD if j == 3 else WHITE, anchor="midright")
                    text(s, cmd if not self.app.touch_mode else "", 19, (ax - 250, yy), CYAN, anchor="midright")
            if self.done[p]:
                text(s, "HAZIR!", 40, (cx, 600 - 80), GOLD, outline=3)
        if not self.two:
            text(s, "A/D veya ← → ile seç   •   F / ENTER onayla   •   ESC geri", 20, (W // 2, 705), (200, 190, 230))
        else:
            text(s, "1P: A/D + F     2P: ← → + K", 20, (W // 2, 705), (200, 190, 230))

    def _wrap(self, s, msg, x, y, anchor, width):
        words = msg.split()
        line = ""
        f = font(20)
        for w in words:
            test = (line + " " + w).strip()
            if f.size(test)[0] > width:
                text(s, line, 20, (x, y), (220, 220, 235), anchor=anchor)
                y += 26
                line = w
            else:
                line = test
        if line:
            text(s, line, 20, (x, y), (220, 220, 235), anchor=anchor)

    def draw_stages(self, s):
        if not hasattr(self, "thumbs"):
            self.thumbs = {}
        if self.stage_i not in self.thumbs:
            stage = STAGES[self.stage_i]()
            prev = pygame.Surface((W, H))
            stage.draw_back(prev, 300)
            self.thumbs[self.stage_i] = (stage.name, pygame.transform.smoothscale(prev, (800, 450)))
        name, thumb = self.thumbs[self.stage_i]

        class _S:
            pass
        stage = _S()
        stage.name = name
        r = thumb.get_rect(center=(W // 2, 360))
        pygame.draw.rect(s, GOLD, r.inflate(12, 12), 4, border_radius=10)
        s.blit(thumb, r)
        text(s, stage.name, 40, (W // 2, r.bottom + 40), WHITE, outline=3)
        text(s, "◄", 60, (r.left - 50, r.centery), GOLD)
        text(s, "►", 60, (r.right + 50, r.centery), GOLD)
        text(s, "← → arena değiştir   •   ENTER başla", 20, (W // 2, 700), (200, 190, 230))


# ============================================================================ mermiler
class Projectile:
    def __init__(self, owner, data, pos, is_super):
        self.owner = owner
        self.d = data
        self.x, self.y = pos
        self.ground = data.get("ground", False)
        if self.ground:
            self.y = GROUND - 22
        self.vx = data["speed"] * owner.facing
        self.r = data["radius"]
        self.color = data["color"]
        self.hits = data.get("hits", 1)
        self.is_super = is_super
        self.alive = True
        self.t = 0
        self.cool = 0
        dmg = data["dmg"] if is_super else int(data["dmg"] * owner.ch["power"])
        self.hd = dict(dmg=dmg // self.hits, hitstun=22, block=18, push=5.0, height="low" if self.ground else "mid",
                       chip=0.25, snd="hit_h", strength=3 if is_super else 2, knockdown=False, super=is_super)

    def update(self, parts):
        self.t += 1
        self.x += self.vx
        if self.cool:
            self.cool -= 1
        if self.t % 2 == 0:
            if self.ground:
                parts.emit(self.x - self.vx * 2, GROUND - 4, 3, self.color, speed=4, life=24, size=6, gravity=0.35,
                           angle=-math.pi / 2, spread=1.4)
            else:
                parts.emit(self.x - self.vx, self.y, 2, self.color, speed=1.4, life=18, size=self.r * 0.35, gravity=-0.05,
                           glow=self.is_super)
        if self.x < -200 or self.x > STAGE_W + 200:
            self.alive = False

    def rect(self):
        return pygame.Rect(self.x - self.r, self.y - self.r, self.r * 2, self.r * 2)

    def draw(self, s, camx, camy, t):
        x, y = int(self.x - camx), int(self.y - camy)
        c = self.color
        if self.ground:
            for i in range(5):
                h = 30 + 20 * math.sin(self.t * 0.6 + i)
                bx = x - i * 14 * (1 if self.vx > 0 else -1)
                pygame.draw.polygon(s, shade(c, 1 - i * 0.12), [(bx - 12, GROUND - camy), (bx, GROUND - camy - h), (bx + 12, GROUND - camy)])
            blit_glow(s, (x, int(GROUND - camy - 20)), 60, shade(c, 0.5), 1.0)
            return
        blit_glow(s, (x, y), int(self.r * 2.6), shade(c, 0.7), 1.0)
        # alev kuyruğu
        dirx = 1 if self.vx > 0 else -1
        for i in range(6):
            k = i / 6
            rr = self.r * (1 - k * 0.8)
            ox = -dirx * (i * self.r * 0.45) + math.sin(t * 30 + i) * 2
            oy = math.sin(t * 25 + i * 1.7) * self.r * 0.2
            pygame.draw.circle(s, lerp_color(c, (255, 60, 20), k), (int(x + ox), int(y + oy)), max(2, int(rr)))
        pygame.draw.circle(s, lerp_color(c, WHITE, 0.6), (x, y), int(self.r * 0.6))
        pygame.draw.circle(s, WHITE, (x + dirx * 2, y), int(self.r * 0.3))


# ============================================================================ dövüş sahnesi
class FightScene(Scene):
    def __init__(self, app, c1, c2, stage_i, two_player, net=None):
        super().__init__(app)
        self.net = net
        self.local = net.side if net else 0
        self.net_menu = False
        self.acc = 0.0
        self.c = (c1, c2)
        self.two = two_player
        self.stage = STAGES[stage_i]()
        self.parts = Particles()
        self.projectiles = []
        self.sparks = []      # (x, y, life, color, size)
        self.popups = []      # yazı efektleri
        self.shake = 0
        self.hitstop = 0
        self.super_freeze = 0
        self.super_owner = None
        self.slowmo = 0
        self.camx = (STAGE_W - W) / 2
        self.camy = 0
        self.round = 1
        self.paused = False
        self.pause_i = 0
        self.show_moves = False
        self.freeze_input = True
        self.t = 0.0
        self.show_skills = app.save.settings.get("show_skills", True)
        diff = app.save.settings.get("difficulty", 1)
        joys = app.joysticks
        ch1, ch2 = CHARACTERS[c1], CHARACTERS[c2]
        self.touch = None
        if app.touch_mode:
            from engine.touch import TouchPad
            self.touch = TouchPad()
            self.touch.set_skill_labels(CHARACTERS[(c1, c2)[self.local]])
        if net:
            ctrl1, ctrl2 = NetController(), NetController()
            self.local_reader = HumanController(KEYMAP_SOLO, joys[0] if joys else None, self.touch)
        elif two_player:
            ctrl1 = HumanController(KEYMAPS[0], joys[0] if len(joys) > 0 else None, self.touch)
            ctrl2 = HumanController(KEYMAPS[1], joys[1] if len(joys) > 1 else None)
        else:
            ctrl1 = HumanController(KEYMAP_SOLO, joys[0] if joys else None, self.touch)
            ctrl2 = CPUController(diff)
        pal2 = ch2["alt"] if c1 == c2 else ch2["palette"]
        self.f = [Fighter(ch1, ch1["palette"], 0, 1, 0, ctrl1), Fighter(ch2, pal2, 0, -1, 1, ctrl2)]
        for ch in (ch1, ch2):
            if ch.get("sprite"):
                sprites.get(ch["sprite"]).preload()
        self.timer = ROUND_TIME
        self.match_over = False
        self.start_round()

    def on_enter(self):
        self.app.audio.play_music("fight")

    # ------------------------------------------------------------------ tur akışı
    def start_round(self):
        mid = STAGE_W / 2
        for i, f in enumerate(self.f):
            f.x = mid - 230 if i == 0 else mid + 230
            f.y = GROUND
            f.vx = f.vy = 0
            f.facing = 1 if i == 0 else -1
            f.health = f.red_health = f.max_health
            f.action = None
            f.ko_pending = False
            f.combo = 0
            f.juggle = 0
            f.invuln = 0
            f.set_state("intro")
            f.pose = dict(POSES["taunt"])
        self.camx = mid - W / 2
        self.projectiles.clear()
        self.timer = ROUND_TIME
        self.phase = "intro"
        self.phase_t = 0.0
        self.freeze_input = True
        self.ko_winner = None
        self.app.audio.play("round")

    def projectile_threat(self, f):
        return any(p.owner is not f for p in self.projectiles)

    def _tap(self, e):
        """Dokunma / tıklama konumu (menüler için)."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            return e.pos
        return None

    def handle(self, e):
        if self.net:
            self.net_handle(e)
            return
        if self.touch is not None and not self.paused and not self.match_over:
            if self.touch.handle(e):
                if self.touch.take("PAUSE"):
                    self.paused = True
                    self.pause_i = 0
                    self.app.audio.play("back")
                return
        tap = self._tap(e)
        if self.paused:
            if self.show_moves:
                if is_back(e) or is_confirm(e) or tap:
                    self.show_moves = False
                return
            if tap:
                for i in range(4):
                    if pygame.Rect(W // 2 - 200, 260 + i * 74, 400, 58).collidepoint(tap):
                        self.pause_i = i
                        e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                        break
            d = nav_dir(e)
            if d and d[1]:
                self.pause_i = (self.pause_i + d[1]) % 4
                self.app.audio.play("menu")
            elif is_confirm(e):
                self.app.audio.play("select")
                if self.pause_i == 0:
                    self.paused = False
                elif self.pause_i == 1:
                    self.show_moves = True
                elif self.pause_i == 2:
                    for f in self.f:
                        f.wins = 0
                        f.meter = 0
                    self.round = 1
                    self.paused = False
                    self.match_over = False
                    self.start_round()
                else:
                    self.app.audio.stop_music()
                    self.app.pop()
            elif is_back(e):
                self.paused = False
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            self.show_skills = not self.show_skills
            self.app.save.settings["show_skills"] = self.show_skills
            self.app.save.save()
            return
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p, pygame.K_AC_BACK) or \
                (e.type == pygame.JOYBUTTONDOWN and e.button in (7, 9)):
            if self.match_over:
                self.app.audio.stop_music()
                self.app.pop()
                return
            self.paused = True
            self.pause_i = 0
            self.app.audio.play("back")
            return
        if self.match_over and tap:
            for i in range(2):
                if pygame.Rect(W // 2 - 160, 380 + i * 70, 320, 54).collidepoint(tap):
                    self.match_choice = i
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        if self.match_over and (is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_f, pygame.K_k))):
            if self.phase_t > 1.5:
                if self.match_choice == 0:
                    for f in self.f:
                        f.wins = 0
                        f.meter = 0
                    self.round = 1
                    self.match_over = False
                    self.start_round()
                else:
                    self.app.audio.stop_music()
                    self.app.pop()
        if self.match_over:
            d = nav_dir(e)
            if d and d[1]:
                self.match_choice = 1 - self.match_choice
                self.app.audio.play("menu")

    # ------------------------------------------------------------------ ağ oyunu
    def net_handle(self, e):
        if self.touch is not None and not self.match_over and not self.net_menu:
            if self.touch.handle(e):
                if self.touch.take("PAUSE"):
                    self.net_menu = True
                return
        esc = (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_AC_BACK)) or \
            (e.type == pygame.JOYBUTTONDOWN and e.button in (7, 9))
        tap = self._tap(e)
        if self.net.disconnected:
            if esc or is_confirm(e) or tap:
                self.app.audio.stop_music()
                self.app.pop()
            return
        if self.net_menu:
            if esc:
                self.net_menu = False
            elif is_confirm(e) or tap:
                self.net.conn.send({"t": "bye"})
                self.app.audio.stop_music()
                self.app.pop()
            return
        if esc:
            self.net_menu = True
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            self.show_skills = not self.show_skills
            return
        if self.match_over and self.local == 0:
            if tap:
                for i in range(2):
                    if pygame.Rect(W // 2 - 160, 380 + i * 70, 320, 54).collidepoint(tap):
                        self.match_choice = i
                        e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
            d = nav_dir(e)
            if d and d[1]:
                self.match_choice = 1 - self.match_choice
                self.app.audio.play("menu")
            elif (is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_f, pygame.K_k))) and self.phase_t > 1.5:
                choice = "rematch" if self.match_choice == 0 else "leave"
                self.net.conn.send({"t": "menu", "c": choice})
                self.net_choice(choice)

    def net_choice(self, choice):
        if choice == "rematch":
            self.net = self.net.restart()
            self.acc = 0.0
            for f in self.f:
                f.wins = 0
                f.meter = 0
            self.round = 1
            self.match_over = False
            self.start_round()
        else:
            self.app.audio.stop_music()
            self.app.pop()

    def net_update(self, dt):
        from engine.net import INPUT_DELAY
        ls = self.net
        ls.pump()
        msgs, ls.remote_msgs = ls.remote_msgs, []
        for m in msgs:
            if m.get("t") == "bye":
                ls.disconnected = True
            elif m.get("t") == "menu" and self.local == 1:
                self.net_choice(m["c"])
                return
        if ls.disconnected:
            return
        self.acc += min(dt, 1 / 20)
        STEP = 1 / 60
        steps = 0
        while self.acc >= STEP and steps < 4:
            if ls.frame + INPUT_DELAY > ls.sent_upto:
                inp = self.local_reader.poll(self.f[self.local], self.f[1 - self.local], self)
                if self.net_menu:
                    inp = InputState()
                ls.push_local([inp.left, inp.right, inp.up, inp.down, inp.p, inp.k, inp.p_held, inp.k_held, inp.special])
            ls.pump()
            if not ls.ready():
                break
            a, b = ls.take()
            for f, v in zip(self.f, (a, b)):
                f.ctrl.value = InputState(*v) if v else InputState()
            self._update_core(STEP)
            ls.checksum(round(sum(f.x + f.y + f.health for f in self.f), 2))
            self.acc -= STEP
            steps += 1
        if self.acc > STEP * 4:
            self.acc = STEP * 4

    # ------------------------------------------------------------------ güncelleme
    def update(self, dt):
        if self.net:
            self.net_update(dt)
            return
        self._update_core(dt)

    def _update_core(self, dt):
        if self.paused:
            return
        self.t += dt
        self.stage.update(dt)
        self.phase_t += dt
        self.update_popups()
        if self.shake > 0:
            self.shake -= 1

        if self.phase == "intro":
            if self.phase_t > 2.6:
                self.phase = "fight"
                self.phase_t = 0
                self.freeze_input = False
                for f in self.f:
                    f.set_state("idle")
        elif self.phase == "fight":
            self.timer -= dt if not (self.hitstop or self.super_freeze) else 0
            if self.timer <= 0:
                self.timer = 0
                self.end_round(timeout=True)
        elif self.phase == "ko":
            if self.phase_t > 3.4:
                self.next_round()
        elif self.phase == "match":
            pass

        # süper hareket donması
        if self.super_freeze > 0:
            self.super_freeze -= 1
            self.parts.update(0.3)
            return
        # vuruş anı duraksaması
        if self.hitstop > 0:
            self.hitstop -= 1
            return
        if self.slowmo > 0:
            self.slowmo -= 1
            if self.slowmo % 3:
                return

        steps = 1
        for _ in range(steps):
            self.step()

    def step(self):
        f1, f2 = self.f
        for f in self.f:
            f.proj_out = any(p.owner is f for p in self.projectiles)
        for f, o in ((f1, f2), (f2, f1)):
            inp = f.ctrl.poll(f, o, self)
            if self.freeze_input or self.phase != "fight":
                inp = InputState()
            f.read_input(inp)
        for f, o in ((f1, f2), (f2, f1)):
            f.update(o, 60, STAGE_W - 60)
        self.push_apart()
        self.limit_distance()
        for f in self.f:
            self.process_events(f)
        self.check_hits()
        for p in self.projectiles:
            p.update(self.parts)
        self.projectile_clash()
        self.projectiles = [p for p in self.projectiles if p.alive]
        self.parts.update()
        self.sparks = [(x, y, l - 1, c, s) for x, y, l, c, s in self.sparks if l > 1]
        self.update_camera()
        if self.phase == "fight":
            for i, f in enumerate(self.f):
                if f.health <= 0:
                    self.end_round(loser=i)
                    break

    def push_apart(self):
        a, b = self.f
        if abs(a.y - b.y) > 110:
            return
        if a.state in ("down", "ko") or b.state in ("down", "ko"):
            return
        def bw(f):
            if f.ch.get("sprite"):
                return sprites.get(f.ch["sprite"]).width * 0.42
            return 62 * f.ch["scale"]
        mind = (bw(a) + bw(b)) / 2
        dx = b.x - a.x
        if abs(dx) < mind:
            over = (mind - abs(dx)) / 2
            s = 1 if dx >= 0 else -1
            if dx == 0:
                s = 1 if a.facing > 0 else -1
            a.x -= s * over
            b.x += s * over
            for f in (a, b):
                f.x = max(60, min(STAGE_W - 60, f.x))
            if abs(b.x - a.x) < mind:
                # duvara sıkıştı: diğerini it
                if a.x <= 61 or a.x >= STAGE_W - 61:
                    b.x = a.x + s * mind
                else:
                    a.x = b.x - s * mind

    def limit_distance(self):
        a, b = self.f
        maxd = W - 140
        if abs(a.x - b.x) > maxd:
            mid = (a.x + b.x) / 2
            for f in (a, b):
                side = 1 if f.x > mid else -1
                f.x = mid + side * maxd / 2

    def process_events(self, f):
        for ev in f.events:
            kind = ev[0]
            if kind == "sound":
                self.app.audio.play(ev[1])
            elif kind == "dust":
                self.parts.emit(ev[1], ev[2] - 4, 8, (200, 190, 170), speed=2.5, life=22, size=6, gravity=-0.03,
                                angle=-math.pi / 2, spread=2.6)
            elif kind == "land_hard":
                self.parts.emit(ev[1], GROUND - 6, 16, (210, 200, 180), speed=4, life=30, size=8, gravity=-0.02,
                                angle=-math.pi / 2, spread=3.0)
                self.shake = max(self.shake, 8)
                self.app.audio.play("land")
            elif kind == "projectile":
                self.projectiles.append(Projectile(f, ev[1], ev[2], ev[3]))
            elif kind == "trail":
                self.parts.emit(ev[1][0], ev[1][1], 2, ev[2], speed=1.2, life=16, size=7, gravity=0, glow=True)
            elif kind == "charge":
                self.parts.emit(ev[1] + random.uniform(-60, 60), ev[2] + random.uniform(-60, 60), 3, ev[3], speed=2,
                                life=18, size=5, gravity=-0.1, glow=True)
            elif kind == "super_flash":
                self.super_freeze = 32
                self.super_owner = f
                self.shake = 6
            elif kind == "special_name":
                col = GOLD if ev[2] else WHITE
                self.popup(ev[1].upper(), f.x, GROUND - 240, col, 30 if ev[2] else 22, 60)
            elif kind == "shockwave":
                x, d, sup = ev[1], ev[2], ev[3]
                self.shake = 14
                self.app.audio.play("boom")
                self.parts.emit(x, GROUND - 4, 30, (230, 200, 150), speed=7, life=34, size=8, gravity=0.25,
                                angle=-math.pi / 2, spread=2.4)
                self.sparks.append((x, GROUND - 10, 14, (255, 220, 120), 3))
                o = self.f[1 - f.side]
                if o.grounded and abs(o.x - x) < 120 and f.action and f.action.hits_done == 0:
                    hd = dict(dmg=int(d["dmg"] * f.ch["power"] * 0.7), hitstun=26, block=18, push=6, height="mid",
                              knockdown=True, launch=-9.0, chip=0.25, snd="hit_h", strength=3)
                    self.apply_hit(f, o, hd, (o.x, GROUND - 60))
                    f.on_hit_landed("hit")
        f.events.clear()

    def check_hits(self):
        for f, o in ((self.f[0], self.f[1]), (self.f[1], self.f[0])):
            hb = f.hitbox()
            if not hb:
                continue
            (hx, hy), r, hd = hb
            hr = o.hurtbox()
            cx = max(hr.left, min(hx, hr.right))
            cy = max(hr.top, min(hy, hr.bottom))
            if (cx - hx) ** 2 + (cy - hy) ** 2 <= r * r:
                res = self.apply_hit(f, o, hd, (hx, hy))
                if res:
                    f.on_hit_landed(res)
        for p in self.projectiles:
            o = self.f[1 - p.owner.side]
            if p.cool or not p.alive:
                continue
            hr = o.hurtbox()
            if hr.colliderect(p.rect()):
                res = self.apply_hit(p.owner, o, p.hd, (p.x, p.y), proj=True)
                if res:
                    p.hits -= 1
                    p.cool = 6
                    if p.hits <= 0 or res == "block" and not p.is_super:
                        p.alive = False
                        self.parts.emit(p.x, p.y, 20, p.color, speed=6, life=26, size=6, glow=True)

    def projectile_clash(self):
        ps = self.projectiles
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                a, b = ps[i], ps[j]
                if a.owner is b.owner or not (a.alive and b.alive):
                    continue
                if a.rect().colliderect(b.rect()):
                    for p in (a, b):
                        p.hits -= 1 if not (a.is_super and b.is_super) else p.hits
                    if a.is_super and not b.is_super:
                        b.alive = False
                    elif b.is_super and not a.is_super:
                        a.alive = False
                    else:
                        a.alive = b.alive = False
                    self.parts.emit((a.x + b.x) / 2, (a.y + b.y) / 2, 30, WHITE, speed=7, life=26, size=5, glow=True)
                    self.sparks.append(((a.x + b.x) / 2, (a.y + b.y) / 2, 12, WHITE, 3))
                    self.app.audio.play("block")

    def apply_hit(self, att, df, hd, pos, proj=False):
        res = df.receive_hit(hd, att, proj)
        if not res:
            return None
        x, y = pos
        if res == "block":
            self.app.audio.play("block")
            self.sparks.append((x, y, 8, CYAN, 1))
            self.parts.emit(x, y, 8, (150, 220, 255), speed=5, life=14, size=3, gravity=0.1)
            self.hitstop = 5
        else:
            strength = hd.get("strength", 1)
            self.app.audio.play(hd.get("snd", "hit_l"))
            col = att.ch["fx"] if strength >= 2 else (255, 240, 180)
            self.sparks.append((x, y, 10 + strength * 2, col, strength))
            self.parts.emit(x, y, 8 + strength * 6, col, speed=5 + strength * 1.5, life=20, size=4, gravity=0.2, glow=strength >= 2)
            self.hitstop = 5 + strength * 2
            self.stage.excite = min(1.6, self.stage.excite + 0.25 * strength)
            self.shake = max(self.shake, 3 + strength * 3)
            if att.combo >= 2:
                self.popup(f"{att.combo} VURUŞ!", 0, 0, GOLD, 36, 70, hud_side=att.side)
            if res == "ko":
                self.hitstop = 18
                self.app.audio.play("ko")
                self.slowmo = 60
                self.stage.excite = 2.5
        return res

    def update_camera(self):
        mid = (self.f[0].x + self.f[1].x) / 2
        target = max(0, min(STAGE_W - W, mid - W / 2))
        self.camx += (target - self.camx) * 0.15
        top = min(self.f[0].y, self.f[1].y)
        ty = min(0, (top - 330) * 0.3)
        self.camy += (ty - self.camy) * 0.1

    # ------------------------------------------------------------------ tur sonu
    def end_round(self, loser=None, timeout=False):
        if self.phase != "fight":
            return
        if timeout:
            a, b = self.f
            ra, rb = a.health / a.max_health, b.health / b.max_health
            loser = None if abs(ra - rb) < 1e-6 else (0 if ra < rb else 1)
        self.phase = "ko"
        self.phase_t = 0
        self.freeze_input = True
        self.timeout = timeout
        if loser is None:
            self.ko_winner = -1
            for f in self.f:
                f.wins += 1
        else:
            w = self.f[1 - loser]
            w.wins += 1
            self.ko_winner = w.side
            self.perfect = w.health == w.max_health
        if not timeout:
            self.app.audio.play("ko")

    def next_round(self):
        winners = [f for f in self.f if f.wins >= WIN_ROUNDS]
        if winners:
            self.phase = "match"
            self.phase_t = 0
            self.match_over = True
            self.match_choice = 0
            if len(winners) == 2:
                self.match_winner = -1
            else:
                self.match_winner = winners[0].side
            self.app.audio.play("win")
            for f in self.f:
                if f.side == self.match_winner:
                    f.set_state("victory")
            return
        self.round += 1
        self.start_round()

    # ------------------------------------------------------------------ yazı efektleri
    def popup(self, msg, x, y, color, size, life, hud_side=None):
        if hud_side is not None:
            self.popups = [p for p in self.popups if p.get("side") != hud_side]
        self.popups.append(dict(msg=msg, x=x, y=y, color=color, size=size, life=life, max=life, side=hud_side))

    def update_popups(self):
        for p in self.popups:
            p["life"] -= 1
        self.popups = [p for p in self.popups if p["life"] > 0]

    # ------------------------------------------------------------------ çizim
    def draw(self, s):
        sx = sy = 0
        if self.shake:
            sx = random.randint(-self.shake, self.shake)
            sy = random.randint(-self.shake, self.shake) // 2
        camx = self.camx + sx
        camy = self.camy + sy
        self.stage.draw_back(s, camx)
        world = s
        # süper donmasında arka plan kararır
        if self.super_freeze:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))
            s.blit(dim, (0, 0))
            o = self.super_owner
            if o:
                cx, cy = int(o.x - camx), int(o.y - camy - 100)
                k = self.super_freeze / 32
                rays = pygame.Surface((W, H), pygame.SRCALPHA)
                for i in range(18):
                    a = i / 18 * math.tau + self.t * 2
                    a2 = a + 0.06
                    pygame.draw.polygon(rays, o.ch["fx"] + (int(70 * k),),
                                        [(cx, cy), (cx + math.cos(a) * 1400, cy + math.sin(a) * 1400),
                                         (cx + math.cos(a2) * 1400, cy + math.sin(a2) * 1400)])
                s.blit(rays, (0, 0))
                blit_glow(s, (cx, cy), 160, o.ch["fx"], 1.0)
        # gölgeler
        for f in self.f:
            h = max(0, GROUND - f.y)
            w = max(40, 110 * f.ch["scale"] - h * 0.3)
            sh = pygame.Surface((int(w), 22), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, max(30, 110 - int(h * 0.4))), sh.get_rect())
            s.blit(sh, (f.x - camx - w / 2, GROUND - camy - 10))
        # dövüşçüler (saldıran önde)
        order = sorted(self.f, key=lambda f: 1 if f.action else 0)
        for f in order:
            flash = f.flash > 0
            tint = None
            if f.invuln > 0 and f.state == "getup" and (f.frame // 3) % 2:
                tint = (255, 255, 255)
            if self.super_freeze and self.super_owner is f:
                blit_glow(s, (int(f.x - camx), int(f.y - camy - 90)), 140, shade(f.ch["fx"], 0.6), 1.0)
            if f.action is not None and f.action.kind != "normal":
                blit_glow(s, (int(f.x - camx), int(f.y - camy - 150)), 150, shade(f.ch["fx"], 0.45), 1.0)
            if f.ch.get("sprite"):
                sprites.draw(world, f, f.x - camx, f.y - camy, flash)
                continue
            draw_fighter(world, f.ch, f.pose, f.x - camx, f.y - camy, f.facing, f.draw_grounded(), flash, tint,
                         t=f.anim_t, palette=f.palette)
        for p in self.projectiles:
            p.draw(s, camx, camy, self.t)
        self.parts.draw(s, camx, camy)
        self.draw_sparks(s, camx, camy)
        self.stage.draw_front(s, camx)
        self.draw_hud(s)
        for p in self.popups:
            k = p["life"] / p["max"]
            a = int(255 * min(1, k * 3))
            if p["side"] is not None:
                x = 40 if p["side"] == 0 else W - 40
                anchor = "midleft" if p["side"] == 0 else "midright"
                sc = 1 + max(0, (k - 0.85)) * 3
                text(s, p["msg"], int(p["size"] * sc), (x, 200), p["color"], anchor=anchor, outline=3, alpha=a)
            else:
                text(s, p["msg"], p["size"], (p["x"] - camx, p["y"] - camy - (1 - k) * 30), p["color"], outline=3, alpha=a)
        if self.touch is not None and not self.paused and not self.match_over:
            self.touch.draw(s, self.f[self.local], self.t)
        self.draw_announcer(s)
        if self.net:
            self.draw_net_overlay(s)
        if self.paused:
            self.draw_pause(s)

    def draw_net_overlay(self, s):
        ls = self.net
        text(s, "AĞ OYUNU  •  " + ("KURUCU (1P)" if self.local == 0 else "KATILAN (2P)"), 15, (W // 2, 104), (190, 210, 255))
        if ls.disconnected:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((5, 0, 15, 200))
            s.blit(ov, (0, 0))
            text(s, "BAĞLANTI KOPTU", 60, (W // 2, 300), (255, 90, 90), outline=4)
            text(s, "Diğer oyuncu çıktı ya da ağ bağlantısı kesildi. ENTER: Menüye dön", 22, (W // 2, 370), WHITE)
        elif self.net_menu:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((5, 0, 15, 180))
            s.blit(ov, (0, 0))
            text(s, "Oyundan çıkılsın mı?", 50, (W // 2, 300), GOLD, outline=3)
            text(s, "ENTER: Çık   •   ESC: Devam (oyun durmaz)", 22, (W // 2, 360), WHITE)
        elif self.match_over and self.local == 1:
            text(s, "Kurucunun seçimi bekleniyor...", 22, (W // 2, 530), (200, 190, 230), outline=2)
        if ls.desynced() or getattr(self, "_desync", False):
            self._desync = True
            text(s, "Uyarı: iki ekran farklılaştı (senkron hatası)", 16, (W // 2, 124), (255, 120, 120))

    def draw_sparks(self, s, camx, camy):
        for x, y, life, col, strength in self.sparks:
            cx, cy = int(x - camx), int(y - camy)
            k = life / (10 + strength * 2)
            r = int((20 + strength * 14) * (1.3 - k))
            blit_glow(s, (cx, cy), r * 2, shade(col, 0.8 * k), 1.0)
            n = 8
            for i in range(n):
                a = i / n * math.tau + strength
                l1 = r * 0.3
                l2 = r * (1.0 if i % 2 else 0.6)
                p1 = (cx + math.cos(a) * l1, cy + math.sin(a) * l1)
                p2 = (cx + math.cos(a) * l2, cy + math.sin(a) * l2)
                pygame.draw.line(s, lerp_color(col, WHITE, 0.6), p1, p2, max(2, int(5 * k)))
            pygame.draw.circle(s, WHITE, (cx, cy), max(2, int(r * 0.25 * k)))

    def draw_hud(self, s):
        bw, bh = 500, 30
        for i, f in enumerate(self.f):
            x = 40 if i == 0 else W - 40 - bw
            y = 34
            # çerçeve
            frame = pygame.Rect(x - 6, y - 6, bw + 12, bh + 12)
            pygame.draw.rect(s, (20, 14, 30), frame, border_radius=8)
            pygame.draw.rect(s, (210, 190, 140), frame, 3, border_radius=8)
            pygame.draw.rect(s, (60, 10, 20), (x, y, bw, bh))
            red = int(bw * f.red_health / f.max_health)
            hp = int(bw * max(0, f.health) / f.max_health)
            if i == 0:
                pygame.draw.rect(s, (230, 40, 40), (x + bw - red, y, red, bh))
                hr = pygame.Rect(x + bw - hp, y, hp, bh)
            else:
                pygame.draw.rect(s, (230, 40, 40), (x, y, red, bh))
                hr = pygame.Rect(x, y, hp, bh)
            ratio = f.health / f.max_health
            col = lerp_color((255, 220, 40), (90, 230, 90), ratio * 1.6 - 0.3) if ratio > 0.25 else (255, 160, 30)
            if hr.w > 0:
                pygame.draw.rect(s, col, hr)
                pygame.draw.rect(s, shade(col, 1.3), (hr.x, hr.y + 3, hr.w, 7))
                pygame.draw.rect(s, shade(col, 0.7), (hr.x, hr.bottom - 7, hr.w, 7))
            # isim
            text(s, f.ch["name"], 26, (x if i == 0 else x + bw, y + bh + 22), WHITE,
                 anchor="midleft" if i == 0 else "midright", outline=2)
            # tur kazanma işaretleri
            for w in range(WIN_ROUNDS):
                cx = (x + bw - 20 - w * 30) if i == 0 else (x + 20 + w * 30)
                cy = y + bh + 22
                pygame.draw.circle(s, (20, 14, 30), (cx, cy), 11)
                pygame.draw.circle(s, GOLD if f.wins > w else (70, 60, 80), (cx, cy), 8)
            # süper göstergesi
            mx = 40 if i == 0 else W - 40 - 300
            my = H - 46
            pygame.draw.rect(s, (20, 14, 30), (mx - 4, my - 4, 308, 24), border_radius=6)
            segs = MAX_METER // SUPER_COST
            for k in range(segs):
                seg_w = 300 // segs
                sxp = mx + k * seg_w
                fill = max(0.0, min(1.0, (f.meter - k * SUPER_COST) / SUPER_COST))
                pygame.draw.rect(s, (40, 30, 60), (sxp + 2, my, seg_w - 4, 16), border_radius=4)
                if fill > 0:
                    c = f.ch["fx"] if fill >= 1 else shade(f.ch["fx"], 0.55)
                    fw = int((seg_w - 4) * fill)
                    rx = sxp + 2 if i == 0 else sxp + 2 + (seg_w - 4 - fw)
                    pygame.draw.rect(s, c, (rx, my, fw, 16), border_radius=4)
                    if fill >= 1 and int(self.t * 6) % 2:
                        pygame.draw.rect(s, WHITE, (sxp + 2, my, seg_w - 4, 16), 2, border_radius=4)
            lbl = "SÜPER HAZIR!" if f.meter >= SUPER_COST else "SÜPER"
            text(s, lbl, 18, (mx + (0 if i == 0 else 300), my - 16), GOLD if f.meter >= SUPER_COST else (200, 190, 220),
                 anchor="midleft" if i == 0 else "midright")
        if self.show_skills and not getattr(self.app, "touch_mode", False):
            for i, f in enumerate(self.f):
                if self.two or i == self.local:
                    self.draw_skill_panel(s, f, i)
        # zaman
        tr = pygame.Rect(W // 2 - 48, 20, 96, 70)
        pygame.draw.rect(s, (20, 14, 30), tr, border_radius=12)
        pygame.draw.rect(s, (210, 190, 140), tr, 3, border_radius=12)
        tv = max(0, int(math.ceil(self.timer)))
        text(s, f"{tv:02d}", 46, tr.center, RED if tv <= 10 else WHITE, outline=2)
        if self.two or self.touch is not None:
            ctrl = ""
        else:
            ctrl = "Yön: ← ↑ → ↓ (veya W A S D)   •   Yumruk: K (veya F)   •   Tekme: L (veya G)   •   ESC: Menü   •   TAB: Hareketler"
        text(s, ctrl, 16, (W // 2, H - 18), (220, 210, 240))

    MIRROR = str.maketrans("→←↘↙↗↖", "←→↙↘↖↗")

    def draw_skill_panel(self, s, f, i):
        """Ekranda özel hareketler ve komutları (karakterin baktığı yöne göre)."""
        btn = key_names(self.two, i)
        rows = [(sp["name"], MOTION_TEXT[sp["motion"]], btn[sp["button"]], False) for sp in f.ch["specials"]]
        sup = f.ch["super"]
        rows.append((sup["name"], MOTION_TEXT[sup["motion"]], btn[sup["button"]], True))
        pw, ph = 330, 22 * len(rows) + 14
        x = 36 if i == 0 else W - 36 - pw
        y = H - 74 - ph
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((8, 4, 18, 150))
        s.blit(panel, (x, y))
        for j, (name, cmd, b, is_sup) in enumerate(rows):
            if f.facing < 0:
                cmd = cmd.translate(self.MIRROR)
            cy = y + 18 + j * 22
            ready = (not is_sup) or f.meter >= SUPER_COST
            col = (GOLD if is_sup else (235, 235, 245)) if ready else (120, 110, 140)
            text(s, cmd.replace(" ", "") + " +" + b, 17, (x + 10, cy), CYAN if ready else (90, 100, 130),
                 anchor="midleft", shadow=False)
            text(s, name, 17, (x + pw - 10, cy), col, anchor="midright", shadow=False)
        text(s, f"{btn['P']} = Yumruk   {btn['K']} = Tekme   (TAB: gizle)", 14, (x + pw // 2, y - 9), (190, 180, 220), shadow=False)

    def draw_announcer(self, s):
        t = self.phase_t
        if self.phase == "intro":
            if t < 1.6:
                k = min(1, t * 3)
                text(s, f"TUR {self.round}" if self.round < 3 or True else "SON TUR", int(80 * (2 - k)), (W // 2, H // 2 - 60),
                     GOLD, outline=4, alpha=int(255 * k))
            else:
                if t < 1.65:
                    pass
                k = min(1, (t - 1.6) * 4)
                text(s, "DÖVÜŞ!", int(110 * (1.6 - k * 0.6)), (W // 2, H // 2 - 60), (255, 80, 60), outline=5)
            if 1.55 < t < 1.62 and not getattr(self, "_fight_snd", False):
                self._fight_snd = True
                self.app.audio.play("fight")
            if t < 0.1:
                self._fight_snd = False
        elif self.phase == "ko":
            if self.timeout:
                msg = "SÜRE DOLDU"
            else:
                msg = "NAKAVT!"
            k = min(1, t * 2.5)
            size = int(130 * (1.8 - k * 0.8))
            text(s, msg, size, (W // 2, H // 2 - 70), (255, 60, 50), outline=6)
            if t > 1.4:
                if self.ko_winner == -1:
                    sub = "BERABERE"
                else:
                    w = self.f[self.ko_winner]
                    sub = f"{w.ch['name']} KAZANDI"
                    if getattr(self, "perfect", False):
                        sub += "  •  KUSURSUZ!"
                text(s, sub, 44, (W // 2, H // 2 + 30), GOLD, outline=3)
        elif self.phase == "match":
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, int(min(150, t * 200))))
            s.blit(dim, (0, 0))
            if self.match_winner == -1:
                msg = "BERABERE!"
            else:
                w = self.f[self.match_winner]
                if not self.two:
                    msg = "KAZANDIN!" if self.match_winner == self.local else "KAYBETTİN"
                else:
                    msg = f"{self.match_winner + 1}. OYUNCU KAZANDI!"
                text(s, f"{w.ch['name']}", 40, (W // 2, 190), shade(w.ch["fx"], 1.2), outline=3)
            text(s, msg, 96, (W // 2, 270), GOLD, outline=5)
            for i, opt in enumerate(["Rövanş", "Ana Menü"]):
                sel = i == self.match_choice
                r = pygame.Rect(W // 2 - 160, 380 + i * 70, 320, 54)
                pygame.draw.rect(s, (60, 30, 90) if sel else (25, 18, 40), r, border_radius=12)
                if sel:
                    pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
                text(s, opt, 30, r.center, WHITE if sel else (170, 160, 190))

    def draw_pause(self, s):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((5, 0, 15, 200))
        s.blit(dim, (0, 0))
        if self.show_moves:
            self.draw_move_list(s)
            return
        text(s, "DURAKLATILDI", 64, (W // 2, 170), GOLD, outline=4)
        for i, opt in enumerate(["Devam Et", "Hareket Listesi", "Maçı Yeniden Başlat", "Ana Menü"]):
            sel = i == self.pause_i
            r = pygame.Rect(W // 2 - 200, 260 + i * 74, 400, 58)
            pygame.draw.rect(s, (60, 30, 90) if sel else (25, 18, 40), r, border_radius=12)
            if sel:
                pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
            text(s, opt, 30, r.center, WHITE if sel else (170, 160, 190))

    def draw_move_list(self, s):
        text(s, "HAREKET LİSTESİ", 50, (W // 2, 50), GOLD, outline=3)
        text(s, "Tuşlar: yön ← ↑ → ↓ (veya WASD) • Yumruk K (veya F) • Tekme L (veya G) • Komutlar sağa bakarken yazılmıştır", 17, (W // 2, 92),
             (200, 190, 230))
        kn = key_names(self.two, 0)
        btn = {"P": f"{kn['P']} (Yumruk)", "K": f"{kn['K']} (Tekme)"}
        Y, T = kn["P"], kn["K"]
        for i, f in enumerate(self.f):
            if i == 1 and self.f[0].ch is self.f[1].ch:
                continue
            ch = f.ch
            x = 90 if i == 0 else W // 2 + 30
            y = 140
            text(s, f"{ch['name']} — {ch['title']}", 30, (x, y), shade(ch["fx"], 1.2), anchor="midleft", outline=2)
            y += 46
            rows = [(sp["name"], f"{MOTION_TEXT[sp['motion']]} + {btn[sp['button']]}") for sp in ch["specials"]]
            sup = ch["super"]
            rows.append((f"SÜPER: {sup['name']}", f"{MOTION_TEXT[sup['motion']]} + {btn[sup['button']]}"))
            for name, cmd in rows:
                text(s, name, 22, (x, y), GOLD if name.startswith("SÜPER") else WHITE, anchor="midleft")
                text(s, cmd, 22, (x + 260, y), CYAN, anchor="midleft")
                y += 36
        y = 380
        text(s, "KOMBOLAR", 30, (90, y), GOLD, anchor="midleft", outline=2)
        combos = [
            ("Ustalık Kombosu", f"{Y} → {Y} → {T} → {T} → özel hareket → SÜPER"),
            ("Zincir Kombo", f"{Y} → {Y} → {T}  (3 vuruş, yere serer)"),
            ("Alçak Zincir", f"↓+{Y} → ↓+{Y} → ↓+{T}  (süpürme, yere serer)"),
            ("İptal Kombo", f"{Y} → {Y} → hemen özel hareket komutu"),
            ("Süper Bitirici", "Özel hareket isabet edince → SÜPER komutu (süper bar dolu)"),
            ("Hava Kombosu", f"Zıpla + {T} → yere inince {Y} → {Y} → özel hareket"),
        ]
        y += 42
        for name, cmd in combos:
            text(s, name, 22, (90, y), WHITE, anchor="midleft")
            text(s, cmd, 22, (330, y), CYAN, anchor="midleft")
            y += 31
        text(s, "Geri adım = blok  •  ↓ + geri = alçak blok  •  Hava saldırıları ayakta bloklanır", 20, (W // 2, H - 60),
             (220, 210, 240))
        text(s, "Kapatmak için ENTER / ESC", 18, (W // 2, H - 28), (160, 150, 190))
