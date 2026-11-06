"""Gölge Seferi: bölüm oynanışı (dalgalar, boss, efektler, arayüz)."""
import math
import random

import pygame

from engine.core import (GOLD, WHITE, W, H, Particles, Scene, blit_glow, is_back, is_confirm, lerp_color, nav_dir,
                         resource_path, shade, text)
from games.hack import data as D
from games.hack.entities import (FLOOR_Y0, ZMAX, Effect, Enemy, Hazard, Hero, Projectile)

KEYS = dict(
    left=(pygame.K_LEFT, pygame.K_a), right=(pygame.K_RIGHT, pygame.K_d), up=(pygame.K_UP, pygame.K_w),
    down=(pygame.K_DOWN, pygame.K_s),
)
PRESS = {
    "attack": (pygame.K_k, pygame.K_j), "heavy": (pygame.K_l,), "jump": (pygame.K_SPACE,),
    "dodge": (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_SEMICOLON), "potion": (pygame.K_h, pygame.K_q),
    "skill0": (pygame.K_1, pygame.K_u), "skill1": (pygame.K_2, pygame.K_i), "skill2": (pygame.K_3, pygame.K_o),
    "skill3": (pygame.K_4, pygame.K_p),
}
SKILL_KEYS = ["1/U", "2/I", "3/O", "4/P"]
RANKS = [(0, "D", (150, 150, 170)), (8, "C", (120, 200, 255)), (16, "B", (120, 255, 140)), (28, "A", (255, 210, 80)),
         (45, "S", (255, 120, 60)), (70, "SS", (255, 70, 160)), (100, "SSS", (255, 255, 255))]


class HackTouch:
    """Telefon için hack and slash oyun kolu."""

    def __init__(self, hero_data):
        from engine.touch import Button, TouchPad
        self.pad = TouchPad()
        sk = hero_data["skills"]
        col = hero_data["color"]
        self.pad.buttons = [
            Button("attack", 1090, 608, 66, "SALDIR", (255, 90, 80)),
            Button("heavy", 1212, 520, 46, "AĞIR", (255, 150, 60)),
            Button("jump", 1218, 650, 42, "ZIPLA", (80, 170, 255)),
            Button("dodge", 965, 660, 40, "KAÇ", (160, 160, 200)),
            Button("skill0", 950, 540, 44, sk[0]["name"], col),
            Button("skill1", 1020, 455, 44, sk[1]["name"], col),
            Button("skill2", 1120, 415, 44, sk[2]["name"], col),
            Button("skill3", 1225, 395, 50, sk[3]["name"], (255, 210, 60)),
            Button("potion", 1225, 150, 32, "İKSİR", (120, 230, 140)),
        ]

    def handle(self, e):
        return self.pad.handle(e)

    def read(self):
        p = self.pad
        out = {k: p.take(k) for k in ("attack", "heavy", "jump", "dodge", "potion", "skill0", "skill1", "skill2",
                                       "skill3")}
        l, r, u, d = p.dirs()
        kx, kz = p.knob
        if math.hypot(kx, kz) > 0.3:
            out["move"] = (max(-1, min(1, kx * 1.4)), max(-1, min(1, kz * 1.4)))
        else:
            out["move"] = (0, 0)
        out["pause"] = p.take("PAUSE")
        return out

    def draw(self, s, hero):
        p = self.pad
        cx, cy = p.STICK
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.circle(ov, (255, 255, 255, 34), (cx, cy), p.STICK_R)
        pygame.draw.circle(ov, (255, 255, 255, 110), (cx, cy), p.STICK_R, 3)
        kx, ky = p.knob
        kp = (int(cx + kx * p.STICK_R * 0.8), int(cy + ky * p.STICK_R * 0.8))
        pygame.draw.circle(ov, (255, 255, 255, 120), kp, 46)
        for b in p.buttons:
            pygame.draw.circle(ov, b.color + (190 if b.down else 100,), (b.x, b.y), b.r)
            pygame.draw.circle(ov, (255, 255, 255, 190), (b.x, b.y), b.r, 3)
        pb = p.pause_btn
        pygame.draw.circle(ov, (0, 0, 0, 110), (pb.x, pb.y), pb.r)
        s.blit(ov, (0, 0))
        pygame.draw.rect(s, WHITE, (pb.x - 8, pb.y - 10, 5, 20))
        pygame.draw.rect(s, WHITE, (pb.x + 3, pb.y - 10, 5, 20))
        for b in p.buttons:
            if b.key.startswith("skill"):
                i = int(b.key[-1])
                draw_cooldown(s, b.x, b.y, b.r, hero, i)
            words = b.label.split()
            size = 15 if b.r < 50 else 18
            if len(words) > 1:
                text(s, words[0], size, (b.x, b.y - 8), WHITE, outline=1)
                text(s, " ".join(words[1:]), size, (b.x, b.y + 9), WHITE, outline=1)
            else:
                text(s, b.label, size, (b.x, b.y), WHITE, outline=1)
            if b.key == "potion":
                text(s, f"x{hero.potions}", 16, (b.x + 30, b.y + 26), GOLD, outline=1)


def draw_cooldown(s, x, y, r, hero, i):
    sk = hero.data["skills"][i]
    if hero.skill_level(i) == 0:
        ov = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ov, (0, 0, 0, 170), (r, r), r)
        s.blit(ov, (x - r, y - r))
        text(s, f"Sv {sk['unlock']}", 14, (x, y + r - 10), (200, 190, 220), outline=1)
        return
    full = sk["cd"] * (1 - 0.06 * (hero.skill_level(i) - 1))
    k = hero.cds[i] / full if full else 0
    if k > 0:
        ov = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pts = [(r, r)]
        for a in range(0, int(360 * k) + 1, 8):
            ang = math.radians(-90 + a)
            pts.append((r + math.cos(ang) * r, r + math.sin(ang) * r))
        if len(pts) > 2:
            pygame.draw.polygon(ov, (0, 0, 0, 160), pts)
        s.blit(ov, (x - r, y - r))
    elif hero.energy < sk["cost"]:
        ov = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(ov, (20, 30, 90, 150), (r, r), r)
        s.blit(ov, (x - r, y - r))


class HackLevel(Scene):
    def __init__(self, app, hid, profile, chapter_i):
        super().__init__(app)
        self.hid = hid
        self.profile = profile
        self.ch = D.CHAPTERS[chapter_i]
        self.chapter_i = chapter_i
        nm = 1.9 if profile.get("nightmare") else 1.0
        self.mult = (1 + 0.55 * chapter_i) * nm
        self.hero = Hero(hid, D.HEROES[hid], profile, 220, ZMAX * 0.6)
        self.enemies = []
        self.projectiles = []
        self.hazards = []
        self.effects = []
        self.pickups = []
        self.parts = Particles()
        self.camx = 0.0
        self.time = 0.0
        self.shake = 0
        self.hitstop = 0.0
        self.tokens = set()
        self.sections = len(self.ch["waves"]) + 1
        self.world_w = W * (self.sections + 0.3)
        self.section = -1
        self.locked = None
        self.wave_spawned = False
        self.state = "play"       # play / pause / dead / victory
        self.menu_i = 0
        self.combo = 0
        self.combo_t = 0.0
        self.max_combo = 0
        self.kills = 0
        self.gold_gain = 0
        self.xp_gain = 0
        self.cinematic = None
        self.ult = None
        self.boss = None
        self.banner = (self.ch["name"], 2.5)
        self.go_t = 0.0
        self.end_t = 0.0
        self.level_ups = 0
        self.held_prev = set()
        self.touch = HackTouch(D.HEROES[hid]) if app.touch_mode else None
        img = pygame.image.load(resource_path("assets", "stages", self.ch["stage"])).convert()
        h = H + 40
        w = int(img.get_width() * h / img.get_height())
        self.bg = pygame.transform.smoothscale(img, (w, h))
        self.bg_flip = pygame.transform.flip(self.bg, True, False)
        self.weather = [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 1)] for _ in range(80)]
        self.vignette = self._vignette()
        from games.fighter import sprites
        for cid in {hid, "jax", "daiki", "kaito", "titus"}:
            sprites.get(cid).preload()

    def on_enter(self):
        self.app.audio.play_music("fight")

    def _vignette(self):
        v = pygame.Surface((W // 8, H // 8), pygame.SRCALPHA)
        for i in range(20):
            k = i / 20
            a = int(170 * (1 - k) ** 2.2)
            pygame.draw.rect(v, (0, 0, 0, a), (int(k * 32), int(k * 18), W // 8 - int(k * 64), H // 8 - int(k * 36)), 2)
        return pygame.transform.smoothscale(v, (W, H))

    # ------------------------------------------------------------------ giriş
    def read_input(self):
        keys = pygame.key.get_pressed()

        def held(names):
            return any(keys[k] for k in names)
        mx = (1 if held(KEYS["right"]) else 0) - (1 if held(KEYS["left"]) else 0)
        mz = (1 if held(KEYS["down"]) else 0) - (1 if held(KEYS["up"]) else 0)
        inp = {"move": (mx, mz)}
        now = set()
        for name, ks in PRESS.items():
            if held(ks):
                now.add(name)
                if name not in self.held_prev:
                    inp[name] = True
        self.held_prev = now
        for j in self.app.joysticks[:1]:
            try:
                ax, ay = j.get_axis(0), j.get_axis(1)
                if abs(ax) > 0.35 or abs(ay) > 0.35:
                    inp["move"] = (ax if abs(ax) > 0.35 else 0, ay if abs(ay) > 0.35 else 0)
                if j.get_numhats():
                    hx, hy = j.get_hat(0)
                    if hx or hy:
                        inp["move"] = (hx, -hy)
            except Exception:
                pass
        if self.touch:
            t = self.touch.read()
            for k, v in t.items():
                if k == "move":
                    if v != (0, 0):
                        inp["move"] = v
                elif v:
                    inp[k] = True
        return inp

    def handle(self, e):
        if e.type == pygame.JOYBUTTONDOWN:
            m = {0: "attack", 2: "attack", 1: "heavy", 3: "jump", 4: "skill0", 5: "skill1", 6: "skill2", 7: "skill3"}
            if e.button in m:
                self._joy = m[e.button]
        if self.state == "play":
            if self.touch and self.touch.handle(e):
                return
            if (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_AC_BACK)) or \
                    (e.type == pygame.JOYBUTTONDOWN and e.button in (9,)):
                self.state = "pause"
                self.menu_i = 0
                self.app.audio.play("back")
            return
        tap = e.pos if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) else None
        opts = self.menu_options()
        if tap:
            for i in range(len(opts)):
                if pygame.Rect(W // 2 - 190, 360 + i * 70, 380, 56).collidepoint(tap):
                    self.menu_i = i
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                    break
            else:
                return
        d = nav_dir(e)
        if d and d[1]:
            self.menu_i = (self.menu_i + d[1]) % len(opts)
            self.app.audio.play("menu")
        elif is_confirm(e) and (self.state == "pause" or self.end_t > 1.2):
            self.app.audio.play("select")
            choice = opts[self.menu_i]
            if choice == "Devam Et":
                self.state = "play"
            elif choice == "Tekrar Dene":
                self.finish(False)
                self.app.replace(HackLevel(self.app, self.hid, self.profile, self.chapter_i))
            elif choice == "Sonraki Bölüm":
                self.finish(True)
                self.app.replace(HackLevel(self.app, self.hid, self.profile, min(self.chapter_i + 1, len(D.CHAPTERS) - 1)))
            else:
                if self.state != "pause":
                    self.finish(self.state == "victory")
                self.app.pop()
        elif is_back(e) and self.state == "pause":
            self.state = "play"

    def menu_options(self):
        if self.state == "pause":
            return ["Devam Et", "Kampa Dön"]
        if self.state == "dead":
            return ["Tekrar Dene", "Kampa Dön"]
        if self.chapter_i < len(D.CHAPTERS) - 1:
            return ["Sonraki Bölüm", "Kampa Dön"]
        return ["Kampa Dön"]

    def finish(self, won):
        """Kazanılan XP / altın zaten profile işlendi; burada sadece kaydet."""
        if getattr(self, "_saved", False):
            return
        self._saved = True
        p = self.profile
        if won:
            if self.chapter_i not in p["cleared"]:
                p["cleared"].append(self.chapter_i)
            p["chapter"] = max(p["chapter"], min(len(D.CHAPTERS), self.chapter_i + 2))
        p["potions"] = max(p["potions"], 2) if not won else max(self.hero.potions, 2)
        p["best_combo"] = max(p.get("best_combo", 0), self.max_combo)
        p["kills"] = p.get("kills", 0) + self.kills
        self.app.save.save()

    # ------------------------------------------------------------------ dalgalar
    def section_left(self, i):
        return i * W

    def update_sections(self):
        h = self.hero
        if self.locked is None:
            nxt = self.section + 1
            if nxt < self.sections and h.x > self.section_left(nxt) + W * 0.42:
                self.section = nxt
                self.locked = self.section_left(nxt)
                self.spawn_section(nxt)
        else:
            alive = [e for e in self.enemies if not e.dead]
            if not alive:
                if self.section == self.sections - 1:
                    if self.state == "play":
                        self.victory()
                else:
                    self.locked = None
                    self.go_t = 3.0
                    self.app.audio.play("round")

    def spawn_section(self, i):
        waves = self.ch["waves"]
        if i < len(waves):
            kinds = list(waves[i])
            if self.profile.get("nightmare"):
                kinds += random.sample(kinds, min(2, len(kinds)))
            for n, k in enumerate(kinds):
                side = 1 if n % 2 == 0 else -1
                x = self.locked + (W + 60 + n * 50 if side > 0 else -60 - n * 50)
                elite = random.random() < 0.12 + 0.05 * self.chapter_i
                e = Enemy(k, D.ENEMIES[k], x, random.uniform(10, ZMAX - 10), self.mult, elite=elite)
                e.cd = 0.8 + n * 0.35
                self.enemies.append(e)
        else:
            bk = self.ch["boss"]
            b = Enemy(bk, D.BOSSES[bk], self.locked + W - 160, ZMAX * 0.5, self.mult, boss=True)
            b.cd = 2.0
            self.boss = b
            self.enemies.append(b)
            self.banner = (b.name, 2.6)
            self.app.audio.play("fight")
            self.shake = 10

    def take_token(self, e):
        self.tokens = {t for t in self.tokens if not t.dead and t.token}
        limit = 2 + self.chapter_i // 2
        if len(self.tokens) < limit:
            self.tokens.add(e)
            return True
        return False

    def release_token(self, e):
        self.tokens.discard(e)

    def nearest_enemy(self, hero, maxd):
        best, bd = None, maxd
        for e in self.enemies:
            if e.dead:
                continue
            d = math.hypot(e.x - hero.x, (e.z - hero.z) * 2)
            if d < bd:
                best, bd = e, d
        return best

    # ------------------------------------------------------------------ savaş
    def damage_enemy(self, e, mult, kind, src_x, heavy_fx=False):
        dmg, crit = self.hero.roll_dmg(mult)
        got = e.hurt(dmg, src_x, kind, self, crit)
        if not got:
            return False
        self.hero.energy = min(self.hero.max_energy, self.hero.energy + 2.2)
        self.combo += 1
        self.combo_t = 2.6
        self.max_combo = max(self.max_combo, self.combo)
        col = (255, 230, 90) if crit else WHITE
        self.popup_text(e.x + random.uniform(-20, 20), e.z, e.height * 0.9, ("KRİTİK " if crit else "") + str(dmg), col,
                        30 if crit else 22)
        hx = e.x
        hy = FLOOR_Y0 + e.z - e.y - e.height * 0.55
        self.parts.emit(hx, hy, 10 if crit else 6, self.hero.color, speed=6, life=18, size=4, glow=True)
        self.effects.append(Effect("ring", 0.18, x=e.x, z=e.z, radius=40, color=self.hero.color))
        self.hitstop = max(self.hitstop, 0.06 if crit or kind != "light" else 0.035)
        self.shake = max(self.shake, 5 if crit else 3)
        self.app.audio.play("hit_h" if kind != "light" or crit else "hit_l", 0.8)
        return True

    def melee(self, hero, x1, x2, zr, mult, kind, hit_ids, ymin=None):
        lo, hi = min(x1, x2), max(x1, x2)
        for e in self.enemies:
            if e.dead or e.uid in hit_ids:
                continue
            l, r = e.body_rect()
            if r < lo or l > hi or abs(e.z - hero.z) > zr:
                continue
            if abs(e.y - hero.y) > 160:
                continue
            if self.damage_enemy(e, mult, kind, hero.x):
                hit_ids.add(e.uid)

    def aoe(self, hero, x, z, radius, mult, kind):
        for e in self.enemies:
            if e.dead:
                continue
            if math.hypot(e.x - x, (e.z - z) * 2.2) < radius:
                self.damage_enemy(e, mult, kind, x)

    def hurt_hero(self, dmg, src_x, kind="light"):
        h = self.hero
        if h.dead or h.invuln > 0 or h.state == "dodge":
            return False
        if h.state == "skill" and h.cast and h.cast["sk"].get("armor"):
            dmg *= 0.4
            kind = "none"
        dmg = int(dmg * random.uniform(0.9, 1.1))
        if kind == "none":
            h.hp -= dmg
            h.flash = 0.1
        else:
            h.hurt(dmg, src_x, kind, self)
            if h.state != "dying":
                h.invuln = 0.45 if kind == "light" else 0.9
        self.popup_text(h.x, h.z, h.height * 0.9, str(dmg), (255, 80, 80), 24)
        self.combo = 0
        self.shake = max(self.shake, 7)
        self.app.audio.play("hit_h")
        if h.hp <= 0 and not h.dead:
            h.dead = True
            h.hp = 0
            h.set_state("dying")
        if h.dead and self.state == "play":
            self.state = "dead"
            self.end_t = 0
            self.menu_i = 0
            self.app.audio.play("ko")
        return True

    def enemy_melee(self, e, x1, x2, zr, atk, hit_ids):
        h = self.hero
        if h.uid in hit_ids:
            return
        lo, hi = min(x1, x2), max(x1, x2)
        l, r = h.body_rect()
        if r < lo or l > hi or abs(e.z - h.z) > zr or h.y > 120:
            return
        hit_ids.add(h.uid)
        self.hurt_hero(atk, e.x, "knock" if e.data["ai"] == "brute" or e.boss and random.random() < 0.3 else "light")

    def enemy_slam(self, e):
        r = 150 if not e.boss else 210
        self.hazards.append(Hazard("enemy", e.x + e.facing * 80, e.z, r, 0.05, e.atk * 1.4, "knock", "slam",
                                   e.aura or (220, 180, 120), owner=e))

    def spawn_enemy_projectile(self, e, move):
        h = self.hero
        y = e.height * 0.55
        if move == "blades":
            for a in (-0.3, -0.15, 0, 0.15, 0.3):
                self.projectiles.append(Projectile("enemy", e.x + e.facing * 40, e.z, y, e.facing * 11, a * 6, 16,
                                                   e.atk * 0.8, "blade", e.aura or (255, 80, 200), life=2.0))
            return
        if move == "wave":
            self.projectiles.append(Projectile("enemy", e.x + e.facing * 50, e.z, 0, e.facing * 9, 0, 34, e.atk * 1.2,
                                               "quake", e.aura or (150, 100, 255), ground=True, life=2.4))
            return
        dz = (h.z - e.z) / max(1, abs(h.x - e.x) / 8)
        self.projectiles.append(Projectile("enemy", e.x + e.facing * 40, e.z, y, e.facing * 8, dz, 20, e.atk,
                                           "fire", (255, 110, 50), life=3.0))
        self.app.audio.play("fireball", 0.6)

    def boss_meteors(self, e):
        h = self.hero
        for i in range(6 + (3 if e.phase2 else 0)):
            x = h.x + random.uniform(-260, 260)
            z = max(0, min(ZMAX, h.z + random.uniform(-70, 70)))
            self.hazards.append(Hazard("enemy", x, z, 95, 0.9 + i * 0.18, e.atk * 1.3, "knock", "meteor",
                                       (255, 90, 40), owner=e))

    def boss_summon(self, e):
        for k in range(2):
            m = Enemy("haydut", D.ENEMIES["haydut"], e.x + random.choice((-1, 1)) * 260, random.uniform(10, ZMAX - 10),
                      self.mult)
            self.enemies.append(m)
            self.fx_burst(m.x, m.z, 90, (160, 80, 255))
        self.popup_text(e.x, e.z, e.height + 40, "ÇAĞRI!", (200, 120, 255), 26)

    def hazard_hit(self, hz):
        if hz.team == "enemy":
            h = self.hero
            if math.hypot(h.x - hz.x, (h.z - hz.z) * 2.2) < hz.radius and h.y < 120:
                self.hurt_hero(hz.dmg, hz.x, hz.kind)
            self.shake = max(self.shake, 8)
            self.app.audio.play("boom", 0.7)
            self.parts.emit(hz.x, FLOOR_Y0 + hz.z, 18, hz.color, speed=7, life=26, size=6, gravity=0.3,
                            angle=-math.pi / 2, spread=2.4)
        else:
            self.aoe(self.hero, hz.x, hz.z, hz.radius, hz.dmg, hz.kind)
            self.shake = max(self.shake, 9)
            self.app.audio.play("boom", 0.6)
            self.parts.emit(hz.x, FLOOR_Y0 + hz.z, 16, hz.color, speed=7, life=26, size=6, gravity=0.3,
                            angle=-math.pi / 2, spread=2.4, glow=True)

    def spawn_hero_projectiles(self, hero, sk, mult):
        count = sk.get("count", 1)
        spread = sk.get("spread", 0)
        for n in range(count):
            a = (n - (count - 1) / 2) * spread
            p = Projectile("hero", hero.x + hero.facing * 60, hero.z, hero.height * 0.55 if not sk.get("ground") else 0,
                           hero.facing * sk["speed"], a * 10, sk["radius"], mult, sk["style"], hero.color,
                           pierce=sk.get("pierce", False), explode=sk.get("explode", 0), life=1.8,
                           kind="knock" if sk.get("ground") else "heavy", ground=sk.get("ground", False))
            self.projectiles.append(p)
        self.app.audio.play("fireball")

    # ------------------------------------------------------------------ ultimate
    def start_cinematic(self, hero, sk):
        self.cinematic = dict(t=0.0, dur=1.0, hero=hero, sk=sk)

    def start_ultimate(self, hero, sk, mult):
        self.ult = dict(type=sk["type"], t=0.0, mult=mult, hits=sk.get("hits", 8), done_hits=0, hero=hero, sk=sk,
                        next=0.0)
        typ = sk["type"]
        if typ == "storm":
            for i in range(3):
                self.effects.append(Effect("dragon", 1.8, y=300 + i * 110, color=hero.color, phase=i * 2.1))
            self.effects.append(Effect("flash", 0.4, color=(200, 230, 255), alpha=150))
        elif typ == "meteors":
            targets = [e for e in self.enemies if not e.dead] or [hero]
            for i in range(sk["hits"]):
                tg = random.choice(targets)
                x = tg.x + random.uniform(-90, 90)
                z = max(0, min(ZMAX, tg.z + random.uniform(-40, 40)))
                self.hazards.append(Hazard("hero", x, z, 110, 0.4 + i * 0.1, mult, "knock", "meteor", (255, 100, 40)))
            self.effects.append(Effect("flash", 0.5, color=(255, 60, 30), alpha=110))
            self.ult["done"] = True
        elif typ == "pillars":
            for i in range(sk["hits"]):
                x = hero.x + hero.facing * (90 + i * 85)
                for dz in (-60, 0, 60):
                    z = max(0, min(ZMAX, hero.z + dz))
                    self.hazards.append(Hazard("hero", x, z, 80, 0.15 + i * 0.09, mult * 0.5, "launch", "rock",
                                               (220, 180, 90)))
            self.ult["done"] = True

    def update_ultimate(self, dt):
        u = self.ult
        if not u:
            return
        u["t"] += dt
        hero = u["hero"]
        if u["type"] == "storm":
            if u["t"] >= u["next"] and u["done_hits"] < u["hits"]:
                u["next"] = u["t"] + 0.17
                u["done_hits"] += 1
                for e in self.enemies:
                    if not e.dead and abs(e.x - self.camx - W / 2) < W / 2 + 40:
                        self.damage_enemy(e, u["mult"], "launch" if u["done_hits"] == u["hits"] else "light", hero.x)
            if u["done_hits"] >= u["hits"]:
                self.finish_ult()
        elif u["type"] == "flurry":
            if u["t"] >= u["next"]:
                u["next"] = u["t"] + 0.07
                targets = [e for e in self.enemies if not e.dead and abs(e.x - self.camx - W / 2) < W / 2 + 40]
                if not targets or u["done_hits"] >= u["hits"]:
                    self.finish_ult()
                    return
                tg = random.choice(targets)
                side = random.choice((-1, 1))
                hero.afterimages.append([hero.x, hero.z, hero.y, hero.frame(), hero.facing, 0.35])
                hero.x = tg.x + side * 70
                hero.z = tg.z
                hero.facing = -side
                self.damage_enemy(tg, u["mult"], "launch" if u["done_hits"] >= u["hits"] - 2 else "light", hero.x)
                self.effects.append(Effect("slash", 0.15, owner=hero, radius=140, tilt=random.uniform(-1, 1),
                                           color=hero.color))
                u["done_hits"] += 1
        elif u.get("done"):
            if u["t"] > 0.8:
                self.finish_ult()

    def finish_ult(self):
        if self.ult:
            h = self.ult["hero"]
            if h.cast:
                h.cast["done"] = True
        self.ult = None

    # ------------------------------------------------------------------ ödüller
    def on_enemy_killed(self, e):
        self.kills += 1
        self.parts.emit(e.x, FLOOR_Y0 + e.z - e.height * 0.5, 30, shade(e.tint, 1.2), speed=5, life=40, size=6,
                        gravity=-0.06, glow=True)
        n = max(1, e.gold // 6)
        for i in range(min(n, 12)):
            self.pickups.append(dict(kind="gold", x=e.x, z=e.z, y=40, vx=random.uniform(-4, 4), vy=random.uniform(6, 11),
                                     val=max(1, e.gold // n), t=0.0))
        for i in range(min(6, max(2, e.xp // 10))):
            self.pickups.append(dict(kind="xp", x=e.x, z=e.z, y=60, vx=random.uniform(-3, 3), vy=random.uniform(5, 9),
                                     val=max(1, e.xp // max(2, min(6, e.xp // 10))), t=0.0))
        if random.random() < (0.12 if not e.elite else 0.6) or e.boss:
            self.pickups.append(dict(kind="heal", x=e.x, z=e.z, y=50, vx=0, vy=8, val=0.15, t=0.0))
        if e.boss:
            self.effects.append(Effect("flash", 0.8, color=(255, 255, 255), alpha=200))
            self.shake = 20
            self.app.audio.play("ko")

    def gain_xp(self, v):
        p = self.profile
        p["xp"] += v
        self.xp_gain += v
        while p["xp"] >= D.xp_needed(p["level"]):
            p["xp"] -= D.xp_needed(p["level"])
            p["level"] += 1
            p["skill_pts"] += 1
            self.level_ups += 1
            h = self.hero
            # yeni seviyede açılan yetenekler
            for i, sk in enumerate(h.data["skills"]):
                if p["skills"][i] == 0 and p["level"] >= sk["unlock"]:
                    p["skills"][i] = 1
                    self.popup_text(h.x, h.z, h.height + 90, f"YENİ YETENEK: {sk['name'].upper()}", GOLD, 26)
            old_hp_ratio = h.hp / h.maxhp
            nh = Hero(self.hid, h.data, p, h.x, h.z)
            h.maxhp, h.atk = nh.maxhp, nh.atk
            h.hp = min(h.maxhp, h.maxhp * old_hp_ratio + h.maxhp * 0.3)
            self.popup_text(h.x, h.z, h.height + 50, f"SEVİYE {p['level']}!", GOLD, 36)
            self.effects.append(Effect("pillar", 0.9, x=h.x, z=h.z, height=420, color=(255, 210, 90)))
            self.app.audio.play("powerup")

    def update_pickups(self, dt):
        h = self.hero
        k = dt * 60
        for p in self.pickups:
            p["t"] += dt
            if p["t"] < 0.5:
                p["vy"] -= 0.9 * k
                p["y"] = max(0, p["y"] + p["vy"] * k)
                p["x"] += p["vx"] * k
                if p["y"] == 0:
                    p["vx"] *= 0.7
                    p["vy"] = abs(p["vy"]) * 0.4
            else:
                dx, dz = h.x - p["x"], h.z - p["z"]
                d = math.hypot(dx, dz)
                sp = min(d, (8 + p["t"] * 14) * k)
                if d > 0:
                    p["x"] += dx / d * sp
                    p["z"] += dz / d * sp
                p["y"] += (40 - p["y"]) * 0.2
                if d < 30:
                    p["done"] = True
                    if p["kind"] == "gold":
                        self.profile["gold"] += p["val"]
                        self.gold_gain += p["val"]
                        self.app.audio.play("coin", 0.35)
                    elif p["kind"] == "xp":
                        self.gain_xp(p["val"])
                    else:
                        h.hp = min(h.maxhp, h.hp + h.maxhp * p["val"])
                        self.popup_text(h.x, h.z, h.height, "+CAN", (120, 255, 140), 22)
        self.pickups = [p for p in self.pickups if not p.get("done")]

    def victory(self):
        self.state = "victory"
        self.end_t = 0
        self.menu_i = 0
        bonus = int(self.max_combo * 3 + 60 * (self.chapter_i + 1))
        self.profile["gold"] += bonus
        self.gold_gain += bonus
        self.app.audio.play("win")
        self.finish(True)

    # ------------------------------------------------------------------ efekt yardımcıları
    def popup_text(self, x, z, h, msg, color, size):
        self.effects.append(Effect("text", 0.9, x=x, z=z, h=h, msg=msg, color=color, size=size))

    def fx_slash(self, hero, tilt, radius):
        self.effects.append(Effect("slash", 0.16, owner=hero, radius=radius, tilt=tilt, color=hero.color))

    def fx_ring(self, x, z, color, r):
        self.effects.append(Effect("ring", 0.5, x=x, z=z, radius=r, color=color))

    def fx_burst(self, x, z, r, color):
        self.effects.append(Effect("ring", 0.4, x=x, z=z, radius=r, color=color))
        self.parts.emit(x, FLOOR_Y0 + z - 100, 24, color, speed=6, life=24, size=5, glow=True)

    def fx_pillar(self, x, z, color, height, style):
        self.effects.append(Effect("pillar", 0.55, x=x, z=z, height=height, color=color))

    def fx_shockwave(self, x, z, r, color, style):
        for k in range(3):
            self.effects.append(Effect("ring", 0.35 + k * 0.15, x=x, z=z, radius=r * (0.6 + k * 0.3), color=color))
        self.parts.emit(x, FLOOR_Y0 + z, 40, color, speed=9, life=30, size=7, gravity=0.35, angle=-math.pi / 2,
                        spread=2.8, glow=True)

    def fx_trail(self, x, z, h, color, style):
        self.parts.emit(x, FLOOR_Y0 + z - h, 3, color, speed=2, life=18, size=7, gravity=-0.02, glow=True)

    # ------------------------------------------------------------------ güncelleme
    def update(self, dt):
        dt = min(dt, 1 / 30)
        if self.state != "play":
            self.end_t += dt
            if self.state in ("dead", "victory"):
                self.parts.update()
                for ef in self.effects:
                    ef.update(dt)
            if self.state == "dead":
                self.hero.update(dt, self, 40, self.world_w - 40)
            return
        if self.touch is not None and self.touch.pad.take("PAUSE"):
            self.state = "pause"
            self.menu_i = 0
            return
        self.time += dt
        if self.banner and self.banner[1] > 0:
            self.banner = (self.banner[0], self.banner[1] - dt)
        if self.cinematic:
            self.cinematic["t"] += dt
            if self.cinematic["t"] >= self.cinematic["dur"]:
                self.cinematic = None
            return
        if self.hitstop > 0:
            self.hitstop -= dt
            return
        if self.shake > 0:
            self.shake -= 1
        if self.combo_t > 0:
            self.combo_t -= dt
            if self.combo_t <= 0:
                self.combo = 0
        self.go_t = max(0, self.go_t - dt)
        inp = self.read_input()
        if getattr(self, "_joy", None):
            inp[self._joy] = True
            self._joy = None
        h = self.hero
        if not self.ult or self.ult["type"] != "flurry":
            h.control(inp, self, dt)
        if self.locked is not None:
            xmin, xmax = self.locked + 40, self.locked + W - 40
        else:
            xmin, xmax = max(40, self.camx + 40), self.world_w - 60
        h.update(dt, self, xmin, xmax)
        for e in self.enemies:
            if self.locked is not None:
                exmin, exmax = self.locked - 300, self.locked + W + 300
                if e.x < self.locked + 30 or e.x > self.locked + W - 30:
                    if e.state in ("idle", "walk"):
                        pass
            else:
                exmin, exmax = -1000, self.world_w + 1000
            e.update(dt, self, exmin, exmax)
        self.enemies = [e for e in self.enemies if not e.remove]
        if self.boss and self.boss.remove:
            self.boss = None
        for p in self.projectiles:
            p.update(dt, self)
            self.projectile_hits(p)
        self.projectiles = [p for p in self.projectiles if not p.dead]
        for hz in self.hazards:
            hz.update(dt, self)
        self.hazards = [hz for hz in self.hazards if not hz.dead]
        self.update_ultimate(dt)
        self.effects = [ef for ef in self.effects if ef.update(dt)]
        self.update_pickups(dt)
        self.parts.update()
        self.update_sections()
        # kamera
        target = h.x - W * 0.42
        if self.locked is not None:
            target = self.locked
        target = max(0, min(self.world_w - W, target))
        if self.locked is None and target < self.camx:
            target = self.camx      # geri dönülmez
        self.camx += (target - self.camx) * 0.12

    def projectile_hits(self, p):
        if p.team == "hero":
            for e in self.enemies:
                if e.dead or e.uid in p.hit_ids:
                    continue
                l, r = e.body_rect()
                if p.x + p.radius < l or p.x - p.radius > r or abs(e.z - p.z) > 40 + p.radius * 0.5:
                    continue
                p.hit_ids.add(e.uid)
                if p.explode:
                    self.aoe(self.hero, p.x, p.z, p.explode, p.dmg, "knock")
                    self.fx_shockwave(p.x, p.z, p.explode, p.color, "fire")
                    self.app.audio.play("boom", 0.6)
                    p.dead = True
                    return
                self.damage_enemy(e, p.dmg, p.kind, p.x - p.vx)
                if not p.pierce:
                    p.dead = True
                    return
        else:
            h = self.hero
            l, r = h.body_rect()
            if p.x + p.radius < l or p.x - p.radius > r or abs(h.z - p.z) > 30 + p.radius * 0.4 or h.y > 140:
                return
            if self.hurt_hero(p.dmg, p.x - p.vx, "knock" if p.ground else "light"):
                p.dead = True

    # ------------------------------------------------------------------ çizim
    def draw_bg(self, s, camx):
        bw = self.bg.get_width()
        i0 = int(camx // bw)
        for i in range(i0, i0 + 3):
            img = self.bg if i % 2 == 0 else self.bg_flip
            s.blit(img, (int(i * bw - camx), -40))
        # hava efekti
        if self.ch["effect"] == "embers":
            for p in self.weather:
                p[1] -= 0.8 * p[2]
                p[0] += math.sin(self.time * 2 + p[2] * 9) * 0.5
                if p[1] < -10:
                    p[1] = H + 10
                    p[0] = random.uniform(0, W)
                blit_glow(s, (int(p[0]), int(p[1])), 8 + int(p[2] * 6), (int(120 * p[2]), int(50 * p[2]), 10))
                pygame.draw.circle(s, (255, 190, 90), (int(p[0]), int(p[1])), 2)
        else:
            for p in self.weather:
                p[1] += 16 * p[2] + 6
                p[0] -= 3 * p[2]
                if p[1] > H:
                    p[1] = random.uniform(-80, 0)
                    p[0] = random.uniform(0, W + 100)
                c = (int(120 + 80 * p[2]), int(140 + 80 * p[2]), 200)
                pygame.draw.line(s, c, (p[0], p[1]), (p[0] - 4 * p[2], p[1] - 22 * p[2]), 1)

    def draw(self, s):
        sx = random.randint(-self.shake, self.shake) if self.shake else 0
        sy = random.randint(-self.shake, self.shake) // 2 if self.shake else 0
        camx = self.camx + sx
        self.draw_bg(s, camx)
        world = pygame.Surface((W, H), pygame.SRCALPHA) if sy else s
        if self.cinematic:
            dim = pygame.Surface((W, H), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))
            s.blit(dim, (0, 0))
        for hz in self.hazards:
            if not hz.done:
                hz.draw(s, camx, self.time)
        ents = [self.hero] + self.enemies
        for e in ents:
            e.draw_shadow(s, camx)
        for p in self.pickups:
            x, y = p["x"] - camx, FLOOR_Y0 + p["z"] - p["y"]
            if p["kind"] == "gold":
                blit_glow(s, (int(x), int(y)), 14, (90, 70, 10))
                pygame.draw.circle(s, (255, 200, 60), (int(x), int(y)), 6)
                pygame.draw.circle(s, (255, 240, 170), (int(x - 2), int(y - 2)), 2)
            elif p["kind"] == "xp":
                blit_glow(s, (int(x), int(y)), 16, (30, 80, 120))
                pygame.draw.circle(s, (120, 230, 255), (int(x), int(y)), 5)
            else:
                blit_glow(s, (int(x), int(y)), 22, (30, 110, 40))
                pygame.draw.circle(s, (120, 255, 140), (int(x), int(y)), 9)
                pygame.draw.rect(s, WHITE, (x - 2, y - 6, 4, 12))
                pygame.draw.rect(s, WHITE, (x - 6, y - 2, 12, 4))
        for e in sorted(ents, key=lambda q: q.z):
            e.draw(s, camx)
        for hz in self.hazards:
            if hz.done:
                hz.draw(s, camx, self.time)
        for p in self.projectiles:
            p.draw(s, camx, self.time)
        self.parts.draw(s, camx, 0)
        for ef in self.effects:
            if ef.kind != "text":
                ef.draw(s, camx, self.time)
        del world
        s.blit(self.vignette, (0, 0))
        for ef in self.effects:
            if ef.kind == "text":
                ef.draw(s, camx, self.time)
        self.draw_hud(s)
        if self.touch and self.state == "play":
            self.touch.draw(s, self.hero)
        if self.cinematic:
            self.draw_cinematic(s)
        self.draw_overlays(s)

    def draw_cinematic(self, s):
        c = self.cinematic
        k = c["t"] / c["dur"]
        h = c["hero"]
        band = pygame.Surface((W, 220), pygame.SRCALPHA)
        band.fill(h.color + (int(150 * min(1, k * 4) * (1 - max(0, k - 0.8) * 5)),))
        s.blit(band, (0, 250))
        from games.fighter import sprites
        port = sprites.get(h.cid).portrait
        if port:
            ph = 360
            img = pygame.transform.smoothscale(port, (int(port.get_width() * ph / port.get_height()), ph))
            x = -400 + min(1, k * 3) * 500
            s.blit(img, (x, 180))
        tx = W + 200 - min(1, k * 3) * 700
        text(s, c["sk"]["name"].upper(), 64, (tx, 360), WHITE, anchor="midleft", outline=4)
        text(s, "ULTİMATE", 26, (tx + 4, 310), GOLD, anchor="midleft", outline=2)

    def draw_hud(self, s):
        h = self.hero
        p = self.profile
        # portre + barlar
        from games.fighter import sprites
        pygame.draw.circle(s, (20, 12, 30), (64, 64), 50)
        port = sprites.get(h.cid).portrait
        if port:
            if not hasattr(self, "_port"):
                ph = 120
                img = pygame.transform.smoothscale(port, (int(port.get_width() * ph / port.get_height()), ph))
                mask = pygame.Surface((92, 92), pygame.SRCALPHA)
                pygame.draw.circle(mask, (255, 255, 255, 255), (46, 46), 46)
                cut = pygame.Surface((92, 92), pygame.SRCALPHA)
                cut.blit(img, (46 - img.get_width() // 2, 4))
                cut.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                self._port = cut
            s.blit(self._port, (18, 18))
        pygame.draw.circle(s, h.color, (64, 64), 48, 3)
        pygame.draw.circle(s, (20, 12, 30), (100, 102), 18)
        text(s, str(p["level"]), 18, (100, 102), GOLD)
        bars = [(h.hp / h.maxhp, (230, 50, 70), 22, f"{int(h.hp)}/{h.maxhp}"),
                (h.energy / h.max_energy, (70, 150, 255), 14, f"{int(h.energy)}"),
                (p["xp"] / D.xp_needed(p["level"]), (255, 200, 70), 6, "")]
        y = 30
        for ratio, col, bh, lab in bars:
            pygame.draw.rect(s, (20, 12, 30), (120, y - 2, 344, bh + 4), border_radius=6)
            pygame.draw.rect(s, col, (122, y, int(340 * max(0, min(1, ratio))), bh), border_radius=5)
            pygame.draw.rect(s, shade(col, 1.3), (122, y + 2, int(340 * max(0, min(1, ratio))), max(2, bh // 4)),
                             border_radius=3)
            if lab:
                text(s, lab, max(12, bh - 4), (126, y + bh // 2 + 1), WHITE, anchor="midleft", shadow=False)
            y += bh + 8
        text(s, f"{h.data['name']}  •  {self.ch['name']}", 16, (122, y + 6), (210, 200, 230), anchor="midleft")
        # altın, iksir
        text(s, f"{p['gold']}", 26, (W - 60, 34), GOLD, anchor="midright", outline=2)
        pygame.draw.circle(s, (255, 200, 60), (W - 40, 34), 11)
        if not self.touch:
            text(s, f"İksir x{h.potions}  (H)", 18, (W - 30, 66), (140, 240, 160), anchor="midright", outline=1)
        # kombo ve rütbe
        if self.combo >= 3:
            rank = RANKS[0]
            for r in RANKS:
                if self.combo >= r[0]:
                    rank = r
            text(s, rank[1], 72, (W - 70, 170), rank[2], outline=4)
            text(s, f"{self.combo} KOMBO", 26, (W - 70, 222), WHITE, outline=2)
            pygame.draw.rect(s, (40, 30, 60), (W - 140, 240, 140, 6))
            pygame.draw.rect(s, rank[2], (W - 140, 240, int(140 * self.combo_t / 2.6), 6))
        # boss barı
        b = self.boss
        if b and not b.dead:
            bw = 640
            x0 = W // 2 - bw // 2
            text(s, b.name, 24, (W // 2, 92), (255, 120, 120) if b.phase2 else WHITE, outline=2)
            pygame.draw.rect(s, (20, 10, 20), (x0 - 4, 106, bw + 8, 22), border_radius=6)
            pygame.draw.rect(s, (200, 30, 50), (x0, 110, int(bw * b.hp / b.maxhp), 14), border_radius=4)
        # yetenek çubuğu
        if not self.touch:
            for i in range(4):
                x = W // 2 - 165 + i * 110
                y = H - 52
                r = 34
                sk = h.data["skills"][i]
                col = h.color if not sk.get("ult") else (255, 200, 60)
                pygame.draw.circle(s, (20, 12, 30), (x, y), r + 4)
                pygame.draw.circle(s, shade(col, 0.55), (x, y), r)
                ready = h.skill_ready(i)
                if ready:
                    blit_glow(s, (x, y), r + 16, shade(col, 0.35))
                pygame.draw.circle(s, col, (x, y), r, 3)
                words = sk["name"].split()
                text(s, words[0], 13, (x, y - 6), WHITE, outline=1)
                if len(words) > 1:
                    text(s, words[1], 13, (x, y + 9), WHITE, outline=1)
                draw_cooldown(s, x, y, r, h, i)
                pygame.draw.rect(s, (20, 12, 30), (x - 22, y - r - 18, 44, 18), border_radius=5)
                text(s, SKILL_KEYS[i], 13, (x, y - r - 9), GOLD, shadow=False)
                text(s, f"{sk['cost']}", 12, (x + r - 2, y + r - 4), (120, 180, 255), outline=1)
            text(s, "Yön: WASD/Oklar  •  Saldırı: K/J  •  Ağır: L  •  Zıpla: Boşluk  •  Kaç: Shift  •  ESC: Menü", 15,
                 (W // 2, H - 8), (200, 190, 230), shadow=False, anchor="midbottom")
        # ilerle oku
        if self.go_t > 0 and int(self.go_t * 3) % 2 == 0:
            text(s, "İLERLE ►", 44, (W - 160, H // 2 - 40), GOLD, outline=3)
        if self.banner and self.banner[1] > 0:
            k = min(1, self.banner[1])
            text(s, self.banner[0], 52, (W // 2, 200), WHITE, outline=4, alpha=int(255 * k))

    def draw_overlays(self, s):
        if self.state == "play":
            return
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((5, 0, 15, min(200, int(self.end_t * 300)) if self.state != "pause" else 190))
        s.blit(ov, (0, 0))
        if self.state == "pause":
            text(s, "DURAKLATILDI", 60, (W // 2, 180), GOLD, outline=4)
            self.draw_skill_info(s)
        elif self.state == "dead":
            text(s, "YENİLDİN", 84, (W // 2, 170), (255, 70, 70), outline=5)
            text(s, f"Kazanılan: {self.gold_gain} altın, {self.xp_gain} XP (korundu)", 24, (W // 2, 250), WHITE)
            text(s, "İpucu: Kampta yeteneklerini ve canını geliştir, Shift ile kaçmayı unutma.", 18, (W // 2, 290),
                 (190, 180, 220))
        else:
            text(s, "BÖLÜM TAMAMLANDI!", 70, (W // 2, 150), GOLD, outline=5)
            rank = RANKS[0]
            for r in RANKS:
                if self.max_combo >= r[0]:
                    rank = r
            rows = [f"Öldürülen düşman: {self.kills}", f"En yüksek kombo: {self.max_combo}  (Rütbe {rank[1]})",
                    f"Altın: +{self.gold_gain}    XP: +{self.xp_gain}    Yeni seviye: {self.level_ups}"]
            for i, r in enumerate(rows):
                text(s, r, 24, (W // 2, 225 + i * 36), WHITE)
        for i, opt in enumerate(self.menu_options()):
            sel = i == self.menu_i
            r = pygame.Rect(W // 2 - 190, 360 + i * 70, 380, 56)
            pygame.draw.rect(s, (60, 26, 96) if sel else (25, 18, 40), r, border_radius=12)
            if sel:
                pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
            text(s, opt, 28, r.center, WHITE if sel else (170, 160, 190))

    def draw_skill_info(self, s):
        h = self.hero
        y = 540
        for i, sk in enumerate(h.data["skills"]):
            lv = h.skill_level(i)
            msg = f"{SKILL_KEYS[i]}  {sk['name']}  " + (f"Sv {lv}  •  {sk['cost']} enerji  •  {sk['cd']:.0f} sn"
                                                         if lv else f"(Seviye {sk['unlock']}'de açılır)")
            text(s, msg, 18, (W // 2, y + i * 26), WHITE if lv else (140, 130, 160))
