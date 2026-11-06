"""Gölge Seferi: kahraman, düşmanlar, mermiler, tehlike alanları ve görsel efektler."""
import math
import random

import pygame

from engine.core import W, blit_glow, lerp_color, shade
from games.fighter import sprites

FLOOR_Y0 = 500          # derinlik 0'ın ekrandaki y'si
ZMAX = 190              # derinlik aralığı
GRAV = 0.95
HERO_SCALE = 0.78

_tint_cache = {}


def sprite_img(cid, anim, idx, facing, scale, tint=None, flash=False):
    key = (cid, anim, idx, facing, scale, tint, flash)
    img = _tint_cache.get(key)
    if img is None:
        if len(_tint_cache) > 2500:
            _tint_cache.clear()
        ss = sprites.get(cid)
        img = ss.image(anim, idx, facing, None, scale)
        if tint or flash:
            img = img.copy()
            if tint:
                # gölge düşman: koyulaştır, renk ver, kenarları parlat
                img.fill(tint + (255,), special_flags=pygame.BLEND_RGBA_MULT)
                img.fill((14, 4, 26, 0), special_flags=pygame.BLEND_RGBA_ADD)
            if flash:
                img.fill((190, 190, 190, 0), special_flags=pygame.BLEND_RGBA_ADD)
        _tint_cache[key] = img
    return img


def frame_count(cid, anim):
    return len(sprites.get(cid).anims[anim])


def prog_idx(cid, anim, p):
    n = frame_count(cid, anim)
    return max(0, min(n - 1, int(p * (n - 1) + 0.5)))


def peak_idx(cid, anim):
    return sprites.get(cid).meta["peak"][anim]


def attack_idx(cid, anim, p, wind=0.45):
    """Saldırı ilerlemesi (0..1): ilk 'wind' kısmı vuruş karesine, kalanı bitişe."""
    n = frame_count(cid, anim)
    pk = peak_idx(cid, anim)
    if p < wind:
        return int(pk * p / wind)
    return min(n - 1, pk + int((p - wind) / (1 - wind) * (n - 1 - pk) + 0.5))


# ============================================================================ temel varlık
class Entity:
    def __init__(self, cid, x, z, scale, team):
        self.cid = cid
        self.x, self.z, self.y = x, z, 0.0
        self.vx = self.vz = self.vy = 0.0
        self.facing = 1
        self.scale = scale
        self.team = team
        self.state = "idle"
        self.t = 0.0
        self.flash = 0.0
        self.invuln = 0.0
        self.hitstun = 0.0
        self.dead = False
        self.remove = False
        self.fade = 1.0
        self.tint = None
        self.armor = False
        self.uid = id(self)
        ss = sprites.get(cid)
        self.height = ss.height * scale
        self.width = ss.width * scale

    def set_state(self, s):
        self.state = s
        self.t = 0.0

    @property
    def airborne(self):
        return self.y > 0.5

    def screen_pos(self, camx):
        return self.x - camx, FLOOR_Y0 + self.z - self.y

    def body_rect(self):
        w = self.width * 0.7
        return self.x - w / 2, self.x + w / 2

    def physics(self, dt, xmin, xmax):
        k = dt * 60
        if self.airborne or self.vy > 0:
            self.vy -= GRAV * k
            self.y += self.vy * k
            if self.y <= 0:
                self.y = 0
                landed_v = self.vy
                self.vy = 0
                self.on_land(landed_v)
        self.x += self.vx * k
        self.z += self.vz * k
        self.x = max(xmin, min(xmax, self.x))
        self.z = max(0, min(ZMAX, self.z))

    def on_land(self, v):
        pass

    def hurt(self, dmg, src_x, kind, scene, crit=False):
        """kind: light / heavy / launch / knock"""
        if self.dead or self.invuln > 0:
            return 0
        self.hp -= dmg
        self.flash = 0.12
        d = 1 if self.x >= src_x else -1
        self.facing = -d
        if self.hp <= 0:
            self.hp = 0
            self.die(scene, d)
            return dmg
        if self.armor and kind in ("light", "heavy") and self.state not in ("air", "down"):
            return dmg
        if kind == "launch" or (kind == "knock") or self.airborne:
            self.vy = 13 if kind == "launch" else 8
            self.vx = d * (2.5 if kind == "launch" else 6)
            self.y = max(self.y, 1)
            self.set_state("air")
        else:
            self.vx = d * (2.2 if kind == "light" else 4.5)
            self.hitstun = 0.32 if kind == "light" else 0.5
            self.set_state("hurt")
        return dmg

    def die(self, scene, d):
        self.dead = True
        self.vy = 10
        self.vx = d * 5
        self.y = max(self.y, 1)
        self.set_state("dying")

    def frame(self):
        st, t = self.state, self.t
        c = self.cid
        if st == "walk":
            return "Walk", int(t * 15) % frame_count(c, "Walk")
        if st == "hurt":
            return "Hit", prog_idx(c, "Hit", min(0.7, t / 0.4))
        if st in ("air", "dying") and self.airborne:
            return "Knockout", prog_idx(c, "Knockout", min(0.42, t / 1.2))
        if st in ("down", "dying", "dead"):
            return "Knockout", prog_idx(c, "Knockout", min(1.0, 0.45 + t * 1.6))
        if st == "getup":
            return "Land", prog_idx(c, "Land", 0.3 + 0.7 * min(1, t / 0.4))
        if st == "jump":
            k = max(0.0, min(1.0, 0.5 - self.vy / 30))
            return "JumpLoop", prog_idx(c, "JumpLoop", k)
        return "Idle", int(t * 10) % frame_count(c, "Idle")

    def draw(self, surf, camx):
        anim, idx = self.frame()
        sx, sy = self.screen_pos(camx)
        fr = sprites.get(self.cid).anims[anim][idx]
        img = sprite_img(self.cid, anim, idx, self.facing, self.scale, self.tint, self.flash > 0)
        ox = (fr["ox"] if self.facing > 0 else -fr["ox"] - fr["w"]) * self.scale
        if self.fade < 1:
            img = img.copy()
            img.set_alpha(int(255 * self.fade))
        surf.blit(img, (int(sx + ox), int(sy + fr["oy"] * self.scale)))

    def draw_shadow(self, surf, camx):
        sx = self.x - camx
        sy = FLOOR_Y0 + self.z
        w = max(30, self.width * 0.9 - self.y * 0.25)
        sh = pygame.Surface((int(w), 18), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, max(40, 120 - int(self.y * 0.4))), sh.get_rect())
        surf.blit(sh, (sx - w / 2, sy - 9))


# ============================================================================ kahraman
class Hero(Entity):
    def __init__(self, hid, data, profile, x, z):
        super().__init__(hid, x, z, HERO_SCALE, "hero")
        self.data = data
        self.p = profile
        up = profile["up"]
        lvl = profile["level"]
        self.maxhp = int(data["hp"] * (1 + 0.09 * (lvl - 1)) * (1 + 0.10 * up["hp"]))
        self.hp = self.maxhp
        self.atk = data["atk"] * (1 + 0.07 * (lvl - 1)) * (1 + 0.08 * up["atk"])
        self.crit = 0.08 + 0.04 * up["crit"]
        self.max_energy = 100 + 15 * up["energy"]
        self.energy = self.max_energy * 0.6
        self.regen = 5 + 1.2 * up["energy"]
        self.speed = data["spd"]
        self.color = data["color"]
        self.cds = [0.0] * 4
        self.combo_step = 0
        self.buffer = None
        self.hit_ids = set()
        self.cast = None
        self.dodge_dir = (1, 0)
        self.afterimages = []
        self.potions = profile["potions"]

    # --- yardımcılar
    def skill_level(self, i):
        return self.p["skills"][i]

    def skill_ready(self, i):
        sk = self.data["skills"][i]
        return self.skill_level(i) > 0 and self.cds[i] <= 0 and self.energy >= sk["cost"]

    def skill_mult(self, i):
        return 1 + 0.22 * (self.skill_level(i) - 1)

    def roll_dmg(self, mult):
        crit = random.random() < self.crit
        d = self.atk * mult * random.uniform(0.9, 1.1) * (1.8 if crit else 1.0)
        return int(d), crit

    def busy(self):
        return self.state in ("attack", "heavy", "skill", "dodge", "hurt", "air", "down", "getup", "dying", "dead", "airatk")

    # --- giriş
    def control(self, inp, scene, dt):
        st = self.state
        if self.dead:
            return
        if inp.get("potion") and self.potions > 0 and self.hp < self.maxhp:
            self.potions -= 1
            self.hp = min(self.maxhp, self.hp + self.maxhp * 0.45)
            scene.fx_ring(self.x, self.z, (120, 255, 140), 120)
            scene.popup_text(self.x, self.z, 180, "+CAN", (120, 255, 140), 26)
            scene.app.audio.play("powerup")
        if inp.get("attack"):
            self.buffer = ("attack", scene.time)
        if inp.get("heavy"):
            self.buffer = ("heavy", scene.time)
        for i in range(4):
            if inp.get("skill%d" % i):
                self.buffer = ("skill%d" % i, scene.time)
        if inp.get("dodge") and st not in ("hurt", "air", "down", "dying", "skill", "dodge"):
            mx, mz = inp.get("move", (0, 0))
            if mx == 0 and mz == 0:
                mx = self.facing
            n = math.hypot(mx, mz) or 1
            self.dodge_dir = (mx / n, mz / n)
            self.set_state("dodge")
            self.invuln = 0.3
            scene.app.audio.play("whoosh")
            return
        if inp.get("jump") and st in ("idle", "walk"):
            self.vy = 15.5
            self.y = 1
            self.set_state("jump")
            scene.app.audio.play("jump")
        # tampon girişi işle
        if self.buffer and scene.time - self.buffer[1] < 0.35:
            b = self.buffer[0]
            if b.startswith("skill"):
                i = int(b[-1])
                if self.skill_ready(i) and st in ("idle", "walk", "jump", "attack", "heavy") and \
                        (st not in ("attack", "heavy") or self.t > 0.12):
                    self.buffer = None
                    self.start_skill(i, scene)
                    return
                if not self.skill_ready(i) and self.skill_level(i) > 0:
                    self.buffer = None
            elif b == "attack":
                if st in ("idle", "walk"):
                    self.buffer = None
                    self.start_attack(0, scene)
                elif st == "jump":
                    self.buffer = None
                    self.set_state("airatk")
                    self.hit_ids = set()
                    scene.app.audio.play("whoosh")
                elif st == "attack" and self.t > self.attack_dur() * 0.45 and self.combo_step < 2:
                    self.buffer = None
                    self.start_attack(self.combo_step + 1, scene)
            elif b == "heavy" and (st in ("idle", "walk") or (st == "attack" and self.t > self.attack_dur() * 0.4)):
                self.buffer = None
                self.set_state("heavy")
                self.hit_ids = set()
                scene.app.audio.play("whoosh")
        # hareket
        mx, mz = inp.get("move", (0, 0))
        if st in ("idle", "walk"):
            self.vx = mx * self.speed
            self.vz = mz * self.speed * 0.7
            if mx:
                self.facing = 1 if mx > 0 else -1
            if mx or mz:
                if st != "walk":
                    self.set_state("walk")
            elif st != "idle":
                self.set_state("idle")
        elif st == "jump":
            self.vx = mx * self.speed * 0.9
            self.vz = mz * self.speed * 0.5
            if mx:
                self.facing = 1 if mx > 0 else -1

    def attack_dur(self):
        return (0.3, 0.3, 0.42)[self.combo_step]

    def start_attack(self, step, scene):
        self.combo_step = step
        self.set_state("attack")
        self.hit_ids = set()
        self.vx = self.facing * 2.5
        self.vz = 0
        scene.app.audio.play("whoosh")

    def start_skill(self, i, scene):
        sk = self.data["skills"][i]
        self.energy -= sk["cost"]
        self.cds[i] = sk["cd"] * (1 - 0.06 * (self.skill_level(i) - 1))
        self.cast = dict(i=i, sk=sk, fired=False, hits=0, hit_ids=set(), timer=0.0)
        self.set_state("skill")
        self.vx = self.vz = 0
        if sk.get("ult"):
            scene.start_cinematic(self, sk)
            scene.app.audio.play("super")
        else:
            scene.app.audio.play("special")
        scene.popup_text(self.x, self.z, self.height + 40, sk["name"].upper(), shade(self.color, 1.3), 24)
        if sk["type"] == "teleport":
            target = scene.nearest_enemy(self, 700)
            if target:
                self.x = target.x - target.facing * 0 + (70 if target.x < self.x else -70) * -1
                self.x = target.x + (-1 if self.x < target.x else 1) * -80
                self.z = target.z
                self.facing = 1 if target.x > self.x else -1
                scene.fx_burst(self.x, self.z, 80, (200, 200, 255))
                self.cast["target"] = target

    # --- güncelleme
    def update(self, dt, scene, xmin, xmax):
        self.t += dt
        self.flash = max(0, self.flash - dt)
        self.invuln = max(0, self.invuln - dt)
        for i in range(4):
            self.cds[i] = max(0, self.cds[i] - dt)
        self.energy = min(self.max_energy, self.energy + self.regen * dt)
        st = self.state
        k = dt * 60
        if st == "attack":
            dur = self.attack_dur()
            p = self.t / dur
            self.vx *= 0.8
            if 0.3 < p < 0.62:
                mult = (1.0, 1.1, 1.6)[self.combo_step]
                kind = "light" if self.combo_step < 2 else "knock"
                reach = 120 if self.combo_step < 2 else 140
                scene.melee(self, self.x, self.x + self.facing * reach, 50, mult, kind, self.hit_ids)
                if self.combo_step >= 0 and not getattr(self, "_arc", False):
                    self._arc = True
                    scene.fx_slash(self, (0.35, -0.35, 0.0)[self.combo_step], 120 + self.combo_step * 20)
            if p >= 1:
                self._arc = False
                self.set_state("idle")
                self.combo_step = 0
        elif st == "heavy":
            p = self.t / 0.5
            self.vx *= 0.8
            if 0.35 < p < 0.6:
                scene.melee(self, self.x, self.x + self.facing * 130, 55, 1.5, "launch", self.hit_ids)
                if not getattr(self, "_arc", False):
                    self._arc = True
                    scene.fx_slash(self, -0.9, 150)
            if p >= 1:
                self._arc = False
                self.set_state("idle")
        elif st == "airatk":
            scene.melee(self, self.x - self.facing * 20, self.x + self.facing * 120, 55, 1.2, "knock", self.hit_ids,
                        ymin=-40)
            if not getattr(self, "_arc", False):
                self._arc = True
                scene.fx_slash(self, 0.6, 130)
        elif st == "dodge":
            sp = 15 * max(0.2, 1 - self.t / 0.28)
            self.vx = self.dodge_dir[0] * sp
            self.vz = self.dodge_dir[1] * sp * 0.6
            if int(self.t * 60) % 2 == 0:
                self.afterimages.append([self.x, self.z, self.y, self.frame(), self.facing, 0.25])
            if self.t > 0.28:
                self.set_state("idle")
                self.vx = self.vz = 0
        elif st == "skill":
            self.update_skill(dt, scene)
        elif st == "hurt":
            self.hitstun -= dt
            self.vx *= 0.85
            if self.hitstun <= 0:
                self.set_state("idle")
        elif st == "air" and not self.airborne and self.vy == 0:
            self.set_state("down")
        elif st == "down":
            self.vx *= 0.8
            if self.t > 0.5:
                self.set_state("getup")
                self.invuln = 0.6
        elif st == "getup":
            if self.t > 0.4:
                self.set_state("idle")
        elif st == "dying":
            self.vx *= 0.9
        if st not in ("walk", "jump", "dodge", "skill", "air"):
            self.vz *= 0.7
        for a in self.afterimages:
            a[5] -= dt
        self.afterimages = [a for a in self.afterimages if a[5] > 0]
        del k
        self.physics(dt, xmin, xmax)

    def on_land(self, v):
        if self.state in ("jump", "airatk"):
            self._arc = False
            self.set_state("idle")
        elif self.state == "skill" and self.cast and self.cast["sk"]["type"] == "slam":
            self.cast["landed"] = True
        elif self.state in ("air", "dying"):
            self.set_state("down" if self.state == "air" else "dying")

    def update_skill(self, dt, scene):
        c = self.cast
        sk = c["sk"]
        typ = sk["type"]
        c["timer"] += dt
        t = c["timer"]
        mult = sk["dmg"] * self.skill_mult(c["i"])
        if typ == "projectile":
            if t > 0.18 and not c["fired"]:
                c["fired"] = True
                scene.spawn_hero_projectiles(self, sk, mult)
            if t > 0.42:
                self.set_state("idle")
        elif typ == "uppercut":
            if t > 0.12 and not c["fired"]:
                c["fired"] = True
                scene.melee(self, self.x - self.facing * 20, self.x + self.facing * sk["range"], 70, mult, "launch",
                            c["hit_ids"])
                scene.fx_pillar(self.x + self.facing * 70, self.z, self.color, 260, sk["style"])
                self.vy = 11
                self.y = 1
            if t > 0.6 and not self.airborne:
                self.set_state("idle")
        elif typ == "dash":
            dur = sk["dist"] / (14 * 60)
            if t < dur:
                self.vx = self.facing * 14
                self.invuln = max(self.invuln, 0.05)
                hits = sk.get("hits", 1)
                if hits > 1 and int(t / (dur / hits)) != c.get("tick", -1):
                    c["tick"] = int(t / (dur / hits))
                    c["hit_ids"] = set()
                scene.melee(self, self.x - self.facing * 40, self.x + self.facing * 90, 60, mult,
                            "knock" if t > dur * 0.8 or sk.get("armor") else "light", c["hit_ids"])
                if int(t * 60) % 2 == 0:
                    self.afterimages.append([self.x, self.z, self.y, self.frame(), self.facing, 0.3])
                    scene.fx_trail(self.x, self.z, 60, self.color, sk["style"])
            else:
                self.vx *= 0.7
                if t > dur + 0.18:
                    self.set_state("idle")
        elif typ == "slam":
            if not c["fired"]:
                c["fired"] = True
                self.vy = 16
                self.y = 1
                self.vx = self.facing * 5
            if c.get("landed") and not c.get("boom"):
                c["boom"] = True
                self.vx = 0
                scene.aoe(self, self.x + self.facing * 30, self.z, sk["radius"], mult, "launch")
                scene.fx_shockwave(self.x + self.facing * 30, self.z, sk["radius"], self.color, sk["style"])
                scene.shake = 16
                scene.app.audio.play("boom")
            if c.get("boom") and t > 0.2 + c.get("boom_t", t):
                c.setdefault("boom_t", t)
            if c.get("boom") and t > 1.0:
                self.set_state("idle")
            if t > 2.0:
                self.set_state("idle")
        elif typ == "teleport":
            if t > 0.12 and not c["fired"]:
                c["fired"] = True
                scene.melee(self, self.x - 30 * self.facing, self.x + self.facing * 150, 70, mult, "knock", c["hit_ids"])
                scene.fx_slash(self, 0.0, 190)
                scene.fx_slash(self, 0.8, 160)
                for k in range(3):
                    self.afterimages.append([self.x - self.facing * (40 + k * 40), self.z, self.y, self.frame(),
                                             self.facing, 0.5])
            if t > 0.5:
                self.set_state("idle")
        elif sk.get("ult"):
            if scene.cinematic:
                return
            self.invuln = max(self.invuln, 0.1)
            if not c["fired"]:
                c["fired"] = True
                scene.start_ultimate(self, sk, mult)
            if c.get("done") or t > 3.5:
                self.set_state("idle")

    def frame(self):
        st = self.state
        c = self.cid
        if st == "attack":
            anim = ("Attack_1", "Attack_3", "Attack_2")[self.combo_step]
            return anim, attack_idx(c, anim, self.t / self.attack_dur(), 0.4)
        if st == "heavy":
            return "Attack_2", attack_idx(c, "Attack_2", self.t / 0.5, 0.42)
        if st == "airatk":
            return "Attack_2", peak_idx(c, "Attack_2")
        if st == "dodge":
            return "Walk", int(self.t * 30) % frame_count(c, "Walk")
        if st == "skill" and self.cast:
            sk = self.cast["sk"]
            anim = sk.get("anim", "Attack_3")
            if sk["type"] == "slam":
                if self.airborne:
                    return "JumpLoop", prog_idx(c, "JumpLoop", 0.4 if self.vy > 0 else 0.85)
                return "Land", prog_idx(c, "Land", 0.4)
            if sk["type"] == "uppercut" and self.airborne:
                return anim, peak_idx(c, anim)
            if sk["type"] == "dash":
                return anim, peak_idx(c, anim)
            return anim, attack_idx(c, anim, min(1.0, self.cast["timer"] / 0.45), 0.4)
        return super().frame()

    def draw(self, surf, camx):
        for x, z, y, (anim, idx), facing, life in self.afterimages:
            img = sprite_img(self.cid, anim, idx, facing, self.scale, self.color)
            img = img.copy()
            img.set_alpha(int(150 * life / 0.3))
            fr = sprites.get(self.cid).anims[anim][idx]
            ox = (fr["ox"] if facing > 0 else -fr["ox"] - fr["w"]) * self.scale
            surf.blit(img, (int(x - camx + ox), int(FLOOR_Y0 + z - y + fr["oy"] * self.scale)))
        if self.state == "skill" or self.invuln > 0.25:
            sx, sy = self.screen_pos(camx)
            blit_glow(surf, (int(sx), int(sy - self.height * 0.5)), int(self.height * 0.6), shade(self.color, 0.4))
        if self.invuln > 0 and self.state == "getup" and int(self.t * 20) % 2:
            return
        super().draw(surf, camx)


# ============================================================================ düşman
class Enemy(Entity):
    def __init__(self, kind, data, x, z, mult, elite=False, boss=False):
        super().__init__(data["sprite"], x, z, data["scale"] * (1.12 if elite else 1.0), "enemy")
        self.kind = kind
        self.data = data
        self.name = data["name"]
        self.maxhp = int(data["hp"] * mult * (2.2 if elite else 1.0))
        self.hp = self.maxhp
        self.atk = data["atk"] * (0.75 + mult * 0.25) * (1.4 if elite else 1.0)
        self.speed = data["spd"] * (1.1 if elite else 1.0)
        self.tint = data["tint"]
        self.elite = elite
        self.boss = boss
        self.armor = data.get("armor", False) and not (kind == "dev" and False)
        self.xp = int(data["xp"] * mult * (2.5 if elite else 1))
        self.gold = int(data["gold"] * mult * (2.5 if elite else 1))
        self.cd = random.uniform(0.5, 1.5)
        self.token = False
        self.move = None
        self.hit_ids = set()
        self.phase2 = False
        self.slot = random.choice((-1, 1))
        self.zoff = random.uniform(-25, 25)
        self.aura = data.get("aura", (255, 200, 60) if elite else None)

    def update(self, dt, scene, xmin, xmax):
        self.t += dt
        self.flash = max(0, self.flash - dt)
        self.invuln = max(0, self.invuln - dt)
        hero = scene.hero
        st = self.state
        d = self.data
        if self.boss and not self.phase2 and self.hp < self.maxhp * 0.5:
            self.phase2 = True
            scene.popup_text(self.x, self.z, self.height + 60, "ÖFKELENDİ!", (255, 80, 60), 34)
            scene.shake = 12
            self.speed *= 1.25
        if st in ("idle", "walk"):
            self.cd -= dt
            dx = hero.x - self.x
            self.facing = 1 if dx > 0 else -1
            ai = d["ai"]
            if ai == "ranged":
                want_x = hero.x - self.facing * 420
                if abs(dx) < 260:
                    want_x = hero.x - self.facing * 450
            else:
                want_x = hero.x - self.slot * (d["reach"] * 0.75) if (self.token or self.boss) else \
                    hero.x - self.slot * (d["reach"] + 140)
                if not self.token and not self.boss and abs(dx) < d["reach"] + 120:
                    want_x = hero.x - self.slot * (d["reach"] + 170)
            want_z = hero.z + (0 if (self.token or self.boss or ai == "ranged") else self.zoff)
            mx = want_x - self.x
            mz = want_z - self.z
            if abs(mx) > 12 or abs(mz) > 8:
                n = math.hypot(mx, mz)
                self.vx = mx / n * self.speed
                self.vz = mz / n * self.speed * 0.7
                if st != "walk":
                    self.set_state("walk")
            else:
                self.vx = self.vz = 0
                if st != "idle":
                    self.set_state("idle")
            in_range = abs(dx) < d["reach"] + 10 and abs(hero.z - self.z) < 30
            if ai == "ranged":
                in_range = abs(dx) < d["reach"] and abs(hero.z - self.z) < 60
            if self.cd <= 0 and not hero.dead:
                if not (self.token or self.boss or ai == "ranged") and scene.take_token(self):
                    self.token = True
                if self.boss:
                    self.choose_boss_move(scene, in_range)
                elif in_range and (self.token or ai == "ranged"):
                    self.set_state("windup")
                    self.vx = self.vz = 0
                    self.hit_ids = set()
        elif st == "windup":
            self.vx *= 0.7
            self.vz *= 0.7
            wind = d["windup"] * (0.7 if self.phase2 else 1.0)
            if self.t >= wind:
                self.set_state("strike")
                self.hit_ids = set()
                if d["ai"] == "ranged" or self.move in ("wave", "blades"):
                    scene.spawn_enemy_projectile(self, self.move)
                elif d["ai"] == "brute" or self.move == "slam":
                    scene.enemy_slam(self)
                elif self.move == "dash":
                    self.vx = self.facing * 16
                elif self.move == "meteors":
                    scene.boss_meteors(self)
                elif self.move == "summon":
                    scene.boss_summon(self)
                scene.app.audio.play("whoosh")
        elif st == "strike":
            if d["ai"] in ("melee",) or (self.boss and self.move == "melee"):
                scene.enemy_melee(self, self.x, self.x + self.facing * d["reach"], 45, self.atk, self.hit_ids)
            if self.move == "dash":
                scene.enemy_melee(self, self.x - self.facing * 30, self.x + self.facing * 90, 60, self.atk * 1.3,
                                  self.hit_ids)
                if int(self.t * 60) % 3 == 0:
                    scene.fx_trail(self.x, self.z, 70, self.aura or (200, 80, 255), "wind")
                if self.t > 0.5:
                    self.vx *= 0.8
            else:
                self.vx *= 0.8
            if self.t > (0.7 if self.move == "dash" else 0.4):
                self.set_state("idle")
                self.cd = d["cd"] * random.uniform(0.8, 1.3) * (0.65 if self.phase2 else 1.0)
                self.move = None
                if not self.boss:
                    scene.release_token(self)
                    self.token = False
        elif st == "hurt":
            self.hitstun -= dt
            self.vx *= 0.85
            if self.hitstun <= 0:
                self.set_state("idle")
                self.cd = max(self.cd, 0.4)
        elif st == "air":
            if not self.airborne and self.vy == 0:
                self.set_state("down")
        elif st == "down":
            self.vx *= 0.8
            if self.t > (0.4 if self.boss else 0.75):
                self.set_state("getup")
                self.invuln = 0.35
        elif st == "getup":
            if self.t > 0.4:
                self.set_state("idle")
        elif st == "dying":
            self.vx *= 0.92
            if not self.airborne and self.t > 0.6:
                self.fade -= dt * 2
                if self.fade <= 0:
                    self.remove = True
        if st not in ("walk",):
            self.vz *= 0.8
        self.physics(dt, xmin, xmax)

    def choose_boss_move(self, scene, in_range):
        moves = list(self.data["moves"])
        if in_range:
            self.move = random.choice(["melee", "melee"] + [m for m in moves if m in ("slam", "dash")])
        else:
            self.move = random.choice(moves)
        if self.move == "summon" and len(scene.enemies) > 4:
            self.move = "dash"
        self.set_state("windup")
        self.vx = self.vz = 0

    def on_land(self, v):
        if self.state == "air":
            self.set_state("down")

    def die(self, scene, d):
        super().die(scene, d)
        if self.token:
            scene.release_token(self)
            self.token = False
        scene.on_enemy_killed(self)

    def frame(self):
        st = self.state
        c = self.cid
        if st == "windup":
            anim = self.attack_anim()
            pk = peak_idx(c, anim)
            wind = self.data["windup"]
            return anim, int(pk * 0.75 * min(1, self.t / wind))
        if st == "strike":
            anim = self.attack_anim()
            if self.move == "dash":
                return anim, peak_idx(c, anim)
            return anim, attack_idx(c, anim, min(1, 0.4 + self.t / 0.4 * 0.6), 0.4)
        return super().frame()

    def attack_anim(self):
        if self.data["ai"] == "ranged" or self.move in ("wave", "blades", "meteors", "summon"):
            return "Attack_3"
        if self.data["ai"] == "brute" or self.move == "slam":
            return "Attack_2"
        if self.move == "dash":
            return "Attack_3"
        return "Attack_1" if self.kind == "haydut" else "Attack_3"

    def draw(self, surf, camx):
        sx, sy = self.screen_pos(camx)
        if self.aura and not self.dead:
            k = 1.3 if self.phase2 else 1.0
            blit_glow(surf, (int(sx), int(sy - self.height * 0.45)), int(self.height * 0.62 * k),
                      shade(self.aura, 0.35 + 0.1 * math.sin(self.t * 6)))
        if self.state == "windup":
            # saldırı uyarısı
            blit_glow(surf, (int(sx), int(sy - self.height * 0.55)), int(self.height * 0.5), (110, 20, 20))
        super().draw(surf, camx)
        if self.state == "windup" and int(self.t * 12) % 2 == 0:
            pygame.draw.polygon(surf, (255, 60, 60), [(sx - 9, sy - self.height - 34), (sx + 9, sy - self.height - 34),
                                                     (sx, sy - self.height - 14)])
        if not self.boss and not self.dead and self.hp < self.maxhp:
            w = 70
            x0, y0 = sx - w / 2, sy - self.height - 14
            pygame.draw.rect(surf, (20, 10, 20), (x0 - 1, y0 - 1, w + 2, 8))
            pygame.draw.rect(surf, (230, 60, 70) if not self.elite else (255, 190, 60), (x0, y0, w * self.hp / self.maxhp, 6))


# ============================================================================ mermiler
class Projectile:
    def __init__(self, team, x, z, y, vx, vz, radius, dmg, style, color, pierce=False, explode=0, life=2.5,
                 kind="heavy", ground=False, owner=None):
        self.team, self.x, self.z, self.y = team, x, z, y
        self.vx, self.vz = vx, vz
        self.radius, self.dmg, self.style, self.color = radius, dmg, style, color
        self.pierce, self.explode, self.life, self.kind, self.ground = pierce, explode, life, kind, ground
        self.hit_ids = set()
        self.t = 0.0
        self.dead = False
        self.owner = owner

    def update(self, dt, scene):
        k = dt * 60
        self.t += dt
        self.x += self.vx * k
        self.z += self.vz * k
        self.life -= dt
        if self.life <= 0:
            self.dead = True
        if int(self.t * 60) % 2 == 0:
            scene.parts.emit(self.x, FLOOR_Y0 + self.z - self.y, 2, self.color, speed=1.5, life=16,
                             size=max(3, self.radius * 0.25), gravity=-0.03 if not self.ground else 0.3, glow=True)

    def draw(self, s, camx, t):
        x, y = int(self.x - camx), int(FLOOR_Y0 + self.z - self.y)
        c = self.color
        d = 1 if self.vx >= 0 else -1
        st = self.style
        if st == "quake" or self.ground:
            for i in range(5):
                h = 34 + 22 * math.sin(self.t * 25 + i)
                bx = x - i * 16 * d
                gy = FLOOR_Y0 + self.z
                pygame.draw.polygon(s, shade(c, 1 - i * 0.12), [(bx - 13, gy), (bx, gy - h), (bx + 13, gy)])
            blit_glow(s, (x, int(FLOOR_Y0 + self.z - 20)), 70, shade(c, 0.5))
            return
        if st == "crescent":
            blit_glow(s, (x, y), int(self.radius * 2.2), shade(c, 0.6))
            pts = []
            for i in range(13):
                a = -1.2 + i * 0.2
                pts.append((x + math.cos(a) * self.radius * d, y + math.sin(a) * self.radius * 1.3))
            for i in range(12, -1, -1):
                a = -1.0 + i * 0.1667
                pts.append((x - 12 * d + math.cos(a) * self.radius * 0.75 * d, y + math.sin(a) * self.radius * 1.0))
            pygame.draw.polygon(s, lerp_color(c, (255, 255, 255), 0.5), pts)
            return
        if st == "blade":
            blit_glow(s, (x, y), 34, shade(c, 0.6))
            ang = self.t * 30
            for k in range(2):
                a = ang + k * math.pi / 2
                pygame.draw.line(s, (255, 255, 255), (x - math.cos(a) * 14, y - math.sin(a) * 14),
                                 (x + math.cos(a) * 14, y + math.sin(a) * 14), 4)
            pygame.draw.circle(s, c, (x, y), 6)
            return
        # orb / fire / enemy_fire
        blit_glow(s, (x, y), int(self.radius * 2.6), shade(c, 0.7))
        for i in range(6):
            kk = i / 6
            rr = self.radius * (1 - kk * 0.8)
            ox = -d * (i * self.radius * 0.45) + math.sin(t * 30 + i) * 2
            oy = math.sin(t * 25 + i * 1.7) * self.radius * 0.2
            pygame.draw.circle(s, lerp_color(c, (255, 60, 20) if st != "orb" else (40, 80, 255), kk),
                               (int(x + ox), int(y + oy)), max(2, int(rr)))
        pygame.draw.circle(s, lerp_color(c, (255, 255, 255), 0.6), (x, y), int(self.radius * 0.6))
        pygame.draw.circle(s, (255, 255, 255), (x + d * 2, y), int(self.radius * 0.3))


# ============================================================================ tehlike alanı (gecikmeli alan hasarı)
class Hazard:
    def __init__(self, team, x, z, radius, delay, dmg, kind, style, color, owner=None, hero_side=True):
        self.team, self.x, self.z, self.radius = team, x, z, radius
        self.delay, self.dmg, self.kind, self.style, self.color = delay, dmg, kind, style, color
        self.t = 0.0
        self.done = False
        self.dead = False
        self.owner = owner
        self.after = 0.0

    def update(self, dt, scene):
        self.t += dt
        if not self.done and self.t >= self.delay:
            self.done = True
            scene.hazard_hit(self)
        if self.done:
            self.after += dt
            if self.after > 0.5:
                self.dead = True

    def draw(self, s, camx, t):
        x, gy = self.x - camx, FLOOR_Y0 + self.z
        r = self.radius
        if not self.done:
            k = self.t / max(0.01, self.delay)
            ell = pygame.Rect(0, 0, int(r * 2), int(r * 0.6))
            ell.center = (int(x), int(gy))
            ov = pygame.Surface(ell.size, pygame.SRCALPHA)
            pygame.draw.ellipse(ov, self.color + (int(50 + 70 * k),), ov.get_rect())
            pygame.draw.ellipse(ov, (255, 255, 255, 160), ov.get_rect(), 2)
            s.blit(ov, ell.topleft)
            if self.style == "meteor":
                my = gy - 600 * (1 - k)
                mx = x + 200 * (1 - k)
                blit_glow(s, (int(mx), int(my)), 60, (160, 60, 20))
                pygame.draw.circle(s, (255, 170, 80), (int(mx), int(my)), 18)
                pygame.draw.line(s, (255, 120, 40), (mx, my), (mx + 60, my - 160), 8)
        else:
            k = self.after / 0.5
            if self.style == "rock":
                h = 220 * (1 - abs(k - 0.3) / 0.7) if k < 1 else 0
                pts = [(x - r * 0.35, gy), (x - r * 0.15, gy - h), (x + r * 0.05, gy - h * 0.8), (x + r * 0.3, gy)]
                pygame.draw.polygon(s, (150, 120, 90), pts)
                pygame.draw.polygon(s, (200, 170, 120), pts, 3)
                blit_glow(s, (int(x), int(gy - 30)), int(r), shade(self.color, 0.5 * (1 - k)))
            else:
                blit_glow(s, (int(x), int(gy - r * 0.3)), int(r * 1.3), shade(self.color, 0.9 * (1 - k)))
                ell = pygame.Rect(0, 0, int(r * 2 * (0.6 + k)), int(r * 0.6 * (0.6 + k)))
                ell.center = (int(x), int(gy))
                pygame.draw.ellipse(s, lerp_color(self.color, (255, 255, 255), 0.5), ell, max(1, int(8 * (1 - k))))


# ============================================================================ görsel efektler
class Effect:
    def __init__(self, kind, life, **kw):
        self.kind = kind
        self.life = self.max = life
        self.__dict__.update(kw)

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, s, camx, t):
        k = max(0.0, self.life / self.max)
        if self.kind == "slash":
            o = self.owner
            cx = o.x - camx + o.facing * 40
            cy = FLOOR_Y0 + o.z - o.y - o.height * 0.5
            r = self.radius
            tilt = self.tilt
            pts_o, pts_i = [], []
            sweep = (1 - k) * 2.6
            for i in range(16):
                a = -1.3 + (i / 15) * min(2.6, sweep + 0.6)
                ca, sa = math.cos(a), math.sin(a)
                rx = ca * r * o.facing
                ry = sa * r * 0.55 + tilt * ca * r * 0.4
                pts_o.append((cx + rx, cy + ry))
                pts_i.append((cx + rx * 0.72, cy + ry * 0.72))
            poly = pts_o + pts_i[::-1]
            surf = pygame.Surface((W, 720), pygame.SRCALPHA)
            pygame.draw.polygon(surf, self.color + (int(200 * k),), poly)
            pygame.draw.lines(surf, (255, 255, 255, int(255 * k)), False, pts_o, 3)
            s.blit(surf, (0, 0))
        elif self.kind == "ring":
            x, y = self.x - camx, FLOOR_Y0 + self.z
            r = self.radius * (1.2 - k)
            ell = pygame.Rect(0, 0, int(r * 2), int(r * 0.6))
            ell.center = (int(x), int(y))
            pygame.draw.ellipse(s, lerp_color(self.color, (255, 255, 255), k * 0.5), ell, max(1, int(10 * k)))
        elif self.kind == "pillar":
            x, gy = self.x - camx, FLOOR_Y0 + self.z
            h = self.height * min(1.0, (1 - k) * 4)
            w = 70 * k + 20
            surf = pygame.Surface((int(w * 2 + 40), int(h + 40)), pygame.SRCALPHA)
            pygame.draw.rect(surf, self.color + (int(150 * k),), (20, 20, int(w * 2), int(h)), border_radius=int(w))
            pygame.draw.rect(surf, (255, 255, 255, int(200 * k)), (20 + w * 0.6, 20, int(w * 0.8), int(h)),
                             border_radius=int(w * 0.4))
            s.blit(surf, (x - w - 20, gy - h - 20))
            blit_glow(s, (int(x), int(gy - h * 0.5)), int(h * 0.5 + 20), shade(self.color, 0.6 * k))
        elif self.kind == "dragon":
            # ekranı boydan boya geçen ışık ejderhası
            p = 1 - k
            head_x = -200 + p * (W + 600)
            base_y = self.y
            pts = []
            for i in range(28):
                xx = head_x - i * 26
                yy = base_y + math.sin(t * 5 + i * 0.35 + self.phase) * 50
                pts.append((xx, yy))
            for i, (xx, yy) in enumerate(pts):
                r = max(4, 34 - i)
                blit_glow(s, (int(xx), int(yy)), int(r * 2.2), shade(self.color, 0.5))
                pygame.draw.circle(s, lerp_color((255, 255, 255), self.color, i / 28), (int(xx), int(yy)), r)
            hx, hy = pts[0]
            pygame.draw.polygon(s, (255, 255, 255), [(hx + 50, hy), (hx + 5, hy - 26), (hx + 5, hy + 26)])
            pygame.draw.circle(s, (255, 60, 60), (int(hx + 14), int(hy - 8)), 5)
        elif self.kind == "text":
            from engine.core import text
            y = FLOOR_Y0 + self.z - self.h - (1 - k) * 60
            a = int(255 * min(1, k * 3))
            sc = 1 + max(0, k - 0.8) * 2
            text(s, self.msg, int(self.size * sc), (self.x - camx, y), self.color, outline=2, alpha=a)
        elif self.kind == "flash":
            ov = pygame.Surface((W, 720), pygame.SRCALPHA)
            ov.fill(self.color + (int(self.alpha * k),))
            s.blit(ov, (0, 0))
