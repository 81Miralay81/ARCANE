"""Dövüşçü mantığı: hareket, saldırı, özel hareket komutları, hasar."""
import math

from games.fighter.characters import MOTIONS, NORMALS
from games.fighter.skeleton import POSES, blend, hurt_rect, limb_point

GROUND = 640
GRAVITY = 0.85
SUPER_COST = 100
MAX_METER = 200


class InputState:
    __slots__ = ("left", "right", "up", "down", "p", "k", "p_held", "k_held", "special")

    def __init__(self, left=False, right=False, up=False, down=False, p=False, k=False, p_held=False, k_held=False,
                 special=None):
        self.left, self.right, self.up, self.down = left, right, up, down
        self.p, self.k, self.p_held, self.k_held = p, k, p_held, k_held
        self.special = special   # dokunmatik özel hareket tuşu: 0,1,2 ya da "super"


def numpad(inp, facing):
    fwd = inp.right if facing > 0 else inp.left
    back = inp.left if facing > 0 else inp.right
    x = 1 if fwd and not back else (-1 if back and not fwd else 0)
    y = 1 if inp.up and not inp.down else (-1 if inp.down and not inp.up else 0)
    return 5 + x + y * 3


class Action:
    """Devam eden bir saldırı / özel hareket."""

    def __init__(self, kind, data, name):
        self.kind = kind          # normal / special / super
        self.data = data
        self.name = name
        self.t = 0
        self.hits_done = 0
        self.last_hit_t = -99
        self.confirmed = False    # isabet ya da blok oldu mu (iptal/zincir için)
        self.phase = "startup"
        self.timer = 0
        self.spawned = False


class Fighter:
    def __init__(self, ch, palette, x, facing, side, controller):
        self.ch = ch
        self.palette = palette
        self.x = x
        self.y = GROUND
        self.vx = 0.0
        self.vy = 0.0
        self.facing = facing
        self.side = side
        self.ctrl = controller
        self.max_health = ch["health"]
        self.health = self.max_health
        self.red_health = self.health
        self.meter = 0.0
        self.state = "idle"
        self.st = 0               # durum içindeki kare sayacı
        self.action = None
        self.pose = dict(POSES["idle"])
        self.prev_pose = dict(POSES["idle"])
        self.pose_from = dict(POSES["idle"])
        self.blend_t = 1.0
        self.input = InputState()
        self.buffer = []          # (frame, numpad) yön geçmişi
        self.press_buf = None     # (button, frame)
        self.frame = 0
        self.hitstop = 0
        self.stun = 0
        self.flash = 0
        self.invuln = 0
        self.juggle = 0
        self.combo = 0
        self.combo_timer = 0
        self.combo_dmg = 0
        self.wins = 0
        self.anim_t = 0.0
        self.walk_phase = 0.0
        self.events = []          # sahneye bildirilen olaylar (ses, efekt, mermi...)
        self.crouching = False
        self.landed_hit = None
        self.jump_dir = 0
        self.ko_pending = False
        self.low_hit = False
        self.proj_out = False
        self.back_block_pose = False
        self.stun0 = 1

    # ------------------------------------------------------------------ yardımcılar
    @property
    def grounded(self):
        return self.y >= GROUND - 0.01

    def emit(self, *ev):
        self.events.append(ev)

    def set_state(self, s):
        if s != self.state:
            self.pose_from = dict(self.pose)
            self.blend_t = 0.0
        self.state = s
        self.st = 0

    def target_pose(self):
        return self.pose

    def back_held(self, opp):
        toward = 1 if opp.x > self.x else -1
        return (self.input.left and toward > 0) or (self.input.right and toward < 0)

    def can_act(self):
        return self.state in ("idle", "walk", "crouch", "jump", "land") and self.action is None

    # ------------------------------------------------------------------ giriş
    def read_input(self, inp):
        self.input = inp
        n = numpad(inp, self.facing)
        if not self.buffer or self.buffer[-1][1] != n:
            self.buffer.append((self.frame, n))
            if len(self.buffer) > 32:
                self.buffer.pop(0)
        if inp.special is not None:
            sp = self.ch["super"] if inp.special == "super" else self.ch["specials"][inp.special]
            # tek tuşla özel hareket: komutu girdi geçmişine ekle
            for d in MOTIONS[sp["motion"]]:
                self.buffer.append((self.frame, d))
            self.buffer = self.buffer[-32:]
            self.press_buf = (sp["button"], self.frame)
        elif inp.p:
            self.press_buf = ("P", self.frame)
        elif inp.k:
            self.press_buf = ("K", self.frame)

    def motion_done(self, motion, window):
        seq = MOTIONS[motion]
        recent = [d for f, d in self.buffer if self.frame - f <= window]
        i = 0
        for d in recent:
            if d == seq[i] or (seq[i] in (3, 1) and d == seq[i]):
                i += 1
                if i == len(seq):
                    return True
            elif seq[i] in (3, 1) and d in (6, 4) and i + 1 < len(seq) and d == seq[i + 1]:
                # klavyede çapraz kaçırılırsa da kabul et (↓ → gibi)
                i += 2
                if i == len(seq):
                    return True
        return False

    def find_special(self, button):
        ch = self.ch
        sup = ch["super"]
        if self.meter >= SUPER_COST and sup["button"] == button and self.motion_done(sup["motion"], 34):
            return "super", sup
        order = sorted(ch["specials"], key=lambda sp: {"dp": 0, "qcf": 1, "qcb": 2}.get(sp["motion"], 3))
        for sp in order:
            if sp["button"] == button and self.motion_done(sp["motion"], 16):
                if sp["motion"] == "qcf" and self.motion_done("dp", 16) and any(
                        o["motion"] == "dp" and o["button"] == button for o in ch["specials"]):
                    continue
                return "special", sp
        return None

    # ------------------------------------------------------------------ eylem başlatma
    def start_normal(self, name):
        data = NORMALS[name]
        self.action = Action("normal", data, name)
        self.set_state("attack")
        self.emit("sound", "whoosh")
        if not data.get("air"):
            self.vx = 0

    def start_special(self, kind, sp):
        self.action = Action(kind, sp, sp["name"])
        self.set_state("attack")
        self.emit("special_name", sp["name"], kind == "super")
        if kind == "super":
            self.meter -= SUPER_COST
            self.emit("super_flash")
            self.emit("sound", "super")
        else:
            self.emit("sound", "special")
        if sp["type"] in ("rising",):
            self.invuln = sp.get("invuln", 0) + sp["startup"]
        if kind == "super":
            self.invuln = max(self.invuln, sp["startup"] + 4)
        self.vx = 0 if self.grounded else self.vx

    def try_attack(self, opp):
        if not self.press_buf or self.frame - self.press_buf[1] > 6:
            return False
        button = self.press_buf[0]
        a = self.action
        # özel hareket iptali / zincir
        if a is not None:
            if a.kind == "normal" and a.confirmed and not a.data.get("air"):
                sp = self.find_special(button)
                if sp:
                    self.press_buf = None
                    self.start_special(*sp)
                    return True
                nxt = self.chain_target(button)
                if nxt and a.t >= a.data["s"] + 1:
                    self.press_buf = None
                    self.start_normal(nxt)
                    return True
            elif a.kind == "special" and a.confirmed and self.meter >= SUPER_COST:
                sup = self.ch["super"]
                if sup["button"] == button and self.motion_done(sup["motion"], 34):
                    self.press_buf = None
                    self.start_special("super", sup)
                    return True
            return False
        if not self.can_act():
            return False
        if self.grounded:
            sp = self.find_special(button)
            if sp:
                self.press_buf = None
                self.start_special(*sp)
                return True
            self.press_buf = None
            if self.input.down:
                self.start_normal("cjab" if button == "P" else "sweep")
            else:
                self.start_normal("jab" if button == "P" else "kick")
            return True
        else:
            sp = self.find_special(button)
            if sp and sp[1]["type"] == "dash" and sp[1].get("air"):
                self.press_buf = None
                self.start_special(*sp)
                return True
            self.press_buf = None
            self.start_normal("air_p" if button == "P" else "air_k")
            return True

    def chain_target(self, button):
        a = self.action
        for c in a.data.get("chain", ()):
            if button == "P" and c in ("cross", "cjab"):
                return c
            if button == "K" and c in ("kick", "round", "sweep"):
                return c
        return None

    # ------------------------------------------------------------------ hasar alma
    def receive_hit(self, hd, attacker, from_proj=False):
        """hd: dmg, hitstun, block, push, height, knockdown, chip, launch"""
        if self.invuln > 0 or self.state in ("down", "getup", "ko"):
            return None
        # blok kontrolü
        can_block = self.grounded and (self.action is None) and self.state in ("idle", "walk", "crouch", "blockstun", "land")
        holding_back = self.back_held(attacker)
        if can_block and holding_back:
            crouch = self.input.down
            ok = (hd["height"] == "mid") or (hd["height"] == "low" and crouch) or (hd["height"] == "high" and not crouch)
            if ok:
                chip = int(hd["dmg"] * hd.get("chip", 0.0))
                self.health = max(0 if hd.get("super") else 1, self.health - chip) if chip else self.health
                self.stun = hd["block"]
                self.crouching = crouch
                self.set_state("blockstun")
                d = 1 if self.x > attacker.x else -1
                self.vx = d * hd["push"] * 0.9
                self.meter = min(MAX_METER, self.meter + hd["dmg"] * 0.05)
                return "block"
        # isabet
        combo = attacker.combo + 1 if self.state in ("hitstun", "air_hit") else 1
        attacker.combo = combo
        attacker.combo_timer = 70
        scale = 1.0 if combo <= 2 else max(0.4, 1.0 - 0.1 * (combo - 2))
        dmg = int(hd["dmg"] * scale)
        attacker.combo_dmg = dmg if combo == 1 else attacker.combo_dmg + dmg
        self.health = max(0, self.health - dmg)
        self.meter = min(MAX_METER, self.meter + hd["dmg"] * 0.07)
        attacker.meter = min(MAX_METER, attacker.meter + hd["dmg"] * 0.11)
        self.action = None
        self.flash = 3
        d = 1 if self.x > attacker.x else -1
        if self.x == attacker.x:
            d = -attacker.facing * -1
        if self.health <= 0:
            self.set_state("air_hit")
            self.vy = -10.5
            self.vx = d * 5.5
            self.y = min(self.y, GROUND - 1)
            self.ko_pending = True
            return "ko"
        if hd.get("knockdown") or hd.get("launch") or not self.grounded or self.state == "air_hit":
            self.juggle += 1
            self.set_state("air_hit")
            self.vy = hd.get("launch", -8.0) if self.juggle < 4 else 2
            self.vx = d * (hd["push"] * 0.6 + 1.5)
            self.y = min(self.y, GROUND - 1)
        else:
            self.stun = hd["hitstun"]
            self.stun0 = self.stun
            self.low_hit = hd["height"] == "low" or self.input.down
            self.set_state("hitstun")
            self.vx = d * hd["push"]
        return "hit"

    # ------------------------------------------------------------------ hitbox
    def hitbox(self):
        a = self.action
        if a is None:
            return None
        d = a.data
        if a.kind == "normal":
            s, act = d["s"], d["a"]
            if s <= a.t < s + act and a.hits_done == 0:
                p = self.limb_pos(d["limb"])
                hd = dict(dmg=int(d["dmg"] * self.ch["power"]), hitstun=d["hitstun"], block=d["block"], push=d["push"],
                          height=d["height"], knockdown=d.get("knockdown"), chip=0.0, snd=d["snd"],
                          strength=1 if d["dmg"] < 70 else 2)
                return p, 20 * self.ch["scale"], hd
            return None
        typ = d["type"]
        hits = d.get("hits", 1)
        per = int(d["dmg"] * self.ch["power"] / hits) if a.kind == "special" else int(d["dmg"] / hits)
        base = dict(dmg=per, hitstun=20, block=16, push=3.0, height="mid", chip=0.25, snd="hit_h", strength=2,
                    super=a.kind == "super")
        if a.hits_done >= hits:
            return None
        if typ == "rising" and a.phase == "active":
            if a.t - a.last_hit_t < 6:
                return None
            hd = dict(base, launch=-11.0, knockdown=a.hits_done == hits - 1)
            p = self.limb_pos(d["limb"])
            return p, 30 * self.ch["scale"], hd
        if typ == "dash" and a.phase == "active":
            gap = max(4, d["dur"] // hits)
            if a.t - a.last_hit_t < gap:
                return None
            last = a.hits_done == hits - 1
            hd = dict(base, push=2.0 if not last else 7.0, knockdown=last and (a.kind == "super" or d.get("armor")),
                      hitstun=24)
            p = self.limb_pos(d["limb"])
            return p, 34 * self.ch["scale"], hd
        if typ == "stomp" and a.phase == "active" and self.vy > 0:
            hd = dict(base, height="high", knockdown=True, launch=-9.0)
            p = self.limb_pos(d["limb"])
            return p, 34 * self.ch["scale"], hd
        return None

    def on_hit_landed(self, result):
        a = self.action
        if a:
            a.hits_done += 1
            a.last_hit_t = a.t
            a.confirmed = True

    def draw_grounded(self):
        return self.grounded and self.state not in ("air_hit",)

    def limb_pos(self, limb, pose=None, grounded=None):
        if self.ch.get("sprite"):
            from games.fighter import sprites
            return sprites.attack_point(self)
        return limb_point(self.ch, pose or self.pose, self.x, self.y, self.facing, limb,
                          self.draw_grounded() if grounded is None else grounded)

    def hurtbox(self):
        if self.ch.get("sprite"):
            from games.fighter import sprites
            return sprites.hurt_rect(self)
        return hurt_rect(self.ch, self.pose, self.x, self.y, self.facing, self.draw_grounded())

    # ------------------------------------------------------------------ güncelleme
    def update(self, opp, stage_l, stage_r):
        self.frame += 1
        self.anim_t += 1 / 60
        if self.flash > 0:
            self.flash -= 1
        if self.invuln > 0:
            self.invuln -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        elif opp.state not in ("hitstun", "air_hit"):
            self.combo = 0
        if self.red_health > self.health:
            self.red_health -= max(1.5, (self.red_health - self.health) * 0.03) if self.state not in ("hitstun", "air_hit") else 0
            self.red_health = max(self.red_health, self.health)

        inp = self.input
        self.st += 1
        target = None
        st = self.state

        if st in ("idle", "walk", "crouch"):
            if self.grounded:
                self.facing = 1 if opp.x > self.x else -1
        if st in ("idle", "walk", "crouch", "land"):
            if self.try_attack(opp):
                st = self.state
        if st == "attack" and self.action is not None:
            self.try_attack(opp)
            st = self.state
        if st in ("jump",) and self.action is None:
            if self.try_attack(opp):
                st = self.state

        if st in ("idle", "walk", "crouch"):
            if inp.up:
                self.set_state("jump")
                dirx = (1 if inp.right else 0) - (1 if inp.left else 0)
                self.vy = -self.ch["jump"]
                self.vx = dirx * self.ch["speed"] * 1.05
                self.jump_dir = dirx * self.facing
                self.emit("sound", "jump")
                self.emit("dust", self.x, GROUND)
            elif inp.down:
                if st != "crouch":
                    self.set_state("crouch")
                self.vx = 0
                target = POSES["crouch"]
            elif inp.left or inp.right:
                dirx = 1 if inp.right else -1
                back = dirx != self.facing
                self.vx = dirx * self.ch["speed"] * (0.78 if back else 1.0)
                if st != "walk":
                    self.state = "walk"
                self.walk_phase += abs(self.vx) * 0.045 * (-1 if back else 1)
                target = self.walk_pose()
            else:
                if st != "idle":
                    self.state = "idle"
                self.vx = 0
                target = self.idle_pose()
            if target is None:
                target = self.idle_pose()
            self.back_block_pose = self.back_held(opp) and opp.is_threatening() and self.state != "jump"
            if self.back_block_pose:
                target = POSES["cblock"] if inp.down else POSES["block"]

        elif st == "jump":
            target = POSES["jump_up"] if self.vy < -6 else POSES["jump"]
            if self.jump_dir < 0 and self.vy > -4:
                target = blend(POSES["jump"], POSES["jump_up"], 0.3)

        elif st == "land":
            target = POSES["crouch"]
            self.vx *= 0.5
            if self.st > 4:
                self.set_state("idle")

        elif st == "attack":
            target = self.update_action(opp)

        elif st == "hitstun":
            self.stun -= 1
            self.vx *= 0.88
            target = POSES["hit_low"] if getattr(self, "low_hit", False) else POSES["hit"]
            if self.stun <= 0:
                self.set_state("crouch" if inp.down else "idle")
                self.juggle = 0

        elif st == "blockstun":
            self.stun -= 1
            self.vx *= 0.85
            target = POSES["cblock"] if self.crouching else POSES["block"]
            if self.stun <= 0:
                self.set_state("idle")

        elif st == "air_hit":
            target = POSES["air_hit"]
            if self.grounded and self.vy >= 0 and self.st > 2:
                if getattr(self, "ko_pending", False):
                    self.set_state("ko")
                    self.emit("land_hard", self.x)
                else:
                    self.set_state("down")
                    self.emit("land_hard", self.x)
                self.vx *= 0.3
                self.juggle = 0

        elif st == "down":
            target = POSES["down"]
            self.vx *= 0.85
            if self.st > 38:
                self.set_state("getup")
                self.invuln = 20

        elif st == "getup":
            target = blend(POSES["getup"], POSES["idle"], min(1, self.st / 16))
            if self.st > 16:
                self.set_state("idle")
                self.facing = 1 if opp.x > self.x else -1

        elif st == "ko":
            target = POSES["down"]
            self.vx *= 0.85

        elif st == "victory":
            k = min(1.0, self.st / 20)
            target = blend(self.idle_pose(), POSES["win"], k)
            if self.st > 50:
                target = dict(target)
                target["ua_f"] += math.sin(self.st * 0.15) * 6
            self.vx = 0

        elif st == "intro":
            k = min(1.0, self.st / 30)
            target = blend(POSES["taunt"], self.idle_pose(), k)
            self.vx = 0

        # fizik
        if not self.grounded or self.vy < 0:
            if not (self.state == "attack" and self.action and self.action.data.get("type") == "dash"
                    and self.action.phase == "active"):
                self.vy += GRAVITY
            self.y += self.vy
            if self.y >= GROUND:
                self.y = GROUND
                if self.state == "jump" or (self.state == "attack" and self.action and self.action.data.get("air")
                                            and self.action.kind == "normal"):
                    self.action = None
                    self.set_state("land")
                    self.vx = 0
                    self.emit("sound", "land")
                    self.emit("dust", self.x, GROUND)
                elif self.state == "attack" and self.action:
                    self.on_land_action()
                self.vy = 0
        self.x += self.vx
        self.x = max(stage_l, min(stage_r, self.x))

        if target is not None:
            if self.blend_t < 1.0:
                self.blend_t = min(1.0, self.blend_t + 0.34)
                self.pose = blend(self.pose_from, target, self.blend_t)
            else:
                self.pose = dict(target)

    def is_threatening(self):
        return self.action is not None or self.proj_out

    def idle_pose(self):
        b = math.sin(self.anim_t * 4.2)
        p = dict(POSES["idle"])
        p["hy"] = 2 + b * 2.0
        p["torso"] += b * 1.5
        p["ua_f"] += b * 3
        p["ua_b"] -= b * 3
        p["th_f"] += b * 1.5
        p["th_b"] -= b * 1.5
        return p

    def walk_pose(self):
        ph = self.walk_phase
        p = dict(POSES["idle"])
        p["th_f"] = 14 + math.sin(ph) * 22
        p["sh_f"] = -14 - max(0, math.sin(ph + 1.4)) * 30
        p["th_b"] = -12 - math.sin(ph) * 22
        p["sh_b"] = -10 - max(0, -math.sin(ph + 1.4)) * 30
        p["hy"] = abs(math.cos(ph)) * -3
        p["ua_f"] += math.sin(ph) * 6
        p["ua_b"] -= math.sin(ph) * 6
        return p

    # ------------------------------------------------------------------ eylem güncelleme
    def update_action(self, opp):
        a = self.action
        if a is None:
            self.set_state("idle")
            return self.idle_pose()
        d = a.data
        a.t += 1
        if a.kind == "normal":
            s, act, r = d["s"], d["a"], d["r"]
            p0, p1 = POSES[d["pose"][0]], POSES[d["pose"][1]]
            rest = POSES["crouch"] if d.get("crouch") else (POSES["jump"] if d.get("air") else self.idle_pose())
            if a.t < s:
                k = a.t / s
                pose = blend(p0, p1, k * k)
            elif a.t < s + act:
                pose = dict(p1)
            else:
                k = (a.t - s - act) / max(1, r)
                pose = blend(p1, rest, min(1, k * 1.2))
            if a.t >= s + act + r and not d.get("air"):
                self.action = None
                self.set_state("crouch" if d.get("crouch") and self.input.down else "idle")
                self.blend_t = 1.0
                return pose
            if d.get("air") and a.t >= s + act + r:
                pose = POSES["jump"]
            self.blend_t = 1.0
            return pose

        typ = d["type"]
        p0, p1 = POSES[d["pose"][0]], POSES[d["pose"][1]]
        s = d["startup"]
        self.blend_t = 1.0
        if a.phase == "startup":
            k = min(1.0, a.t / s)
            pose = blend(self.pose_from if a.t < 2 else p0, p0, k) if typ != "projectile" else blend(p0, p0, 1)
            if typ == "projectile":
                pose = blend(POSES["idle"], p0, min(1, a.t / (s * 0.6)))
                if a.t > s * 0.6:
                    pose = blend(p0, p1, (a.t - s * 0.6) / (s * 0.4))
            if self.action.kind == "super" and a.t % 4 == 0:
                self.emit("charge", self.x, self.y - 90, self.ch["fx"])
            if a.t >= s:
                a.phase = "active"
                a.t_active = 0
                if typ == "projectile":
                    hand = self.limb_pos("hand_f", p1, True)
                    self.emit("projectile", d, hand, a.kind == "super")
                    self.emit("sound", "fireball")
                    a.phase = "recovery"
                    a.timer = d["recovery"]
                elif typ == "rising":
                    self.vy = d["vy"]
                    self.vx = d["vx"] * self.facing
                    self.y -= 1
                    self.emit("sound", "whoosh")
                elif typ == "dash":
                    a.timer = d["dur"]
                    self.vx = d["vx"] * self.facing
                    if d.get("air"):
                        self.y = GROUND - 34
                        self.vy = 0
                    self.emit("sound", "whoosh")
                elif typ == "stomp":
                    self.vy = d["vy"]
                    self.vx = d["vx"] * self.facing
                    self.y -= 1
            return pose
        if a.phase == "active":
            if typ == "rising":
                pose = dict(p1)
                if self.vy > 0:
                    pose = blend(p1, POSES["jump"], min(1, self.vy / 8))
                if a.t % 2 == 0:
                    self.emit("trail", self.limb_pos(d["limb"], pose, False), self.ch["fx"])
                return pose
            if typ == "dash":
                a.timer -= 1
                spin = d["pose"][0] != d["pose"][1]
                if spin:
                    pose = dict(p0 if (a.t // 5) % 2 == 0 else p1)
                else:
                    pose = dict(p1)
                if a.t % 2 == 0:
                    self.emit("trail", self.limb_pos(d["limb"], pose),
                              self.ch["fx"])
                if d.get("armor"):
                    self.invuln = max(self.invuln, 1) if a.kind == "super" else self.invuln
                if a.timer <= 0 or (a.hits_done >= d.get("hits", 1) and d.get("hits", 1) == 1):
                    a.phase = "recovery"
                    a.timer = d["recovery"]
                    self.vx = self.facing * 1.5
                    if d.get("air"):
                        self.vy = 1
                return pose
            if typ == "stomp":
                pose = dict(p0)
                return pose
        if a.phase == "recovery":
            a.timer -= 1
            self.vx *= 0.8 if self.grounded else 1.0
            rest = self.idle_pose()
            pose = blend(p1 if typ != "dash" else POSES["idle"], rest, 1 - max(0, a.timer) / max(1, d["recovery"]))
            if typ in ("rising",) and not self.grounded:
                pose = POSES["jump"]
            if a.timer <= 0 and self.grounded:
                self.action = None
                self.set_state("idle")
                self.blend_t = 1.0
            return pose
        return self.idle_pose()

    def on_land_action(self):
        a = self.action
        d = a.data
        typ = d.get("type")
        if typ == "stomp":
            self.emit("shockwave", self.x + self.facing * 40, d, a.kind == "super")
            a.phase = "recovery"
            a.timer = d["recovery"]
            self.vx = 0
            self.pose_from = POSES["stomp"]
            a.data = dict(d, pose=(d["pose"][1], d["pose"][1]))
        elif typ == "rising":
            a.phase = "recovery"
            a.timer = d["recovery"]
            self.vx = 0
            self.emit("dust", self.x, GROUND)
        elif typ == "dash":
            a.phase = "recovery"
            a.timer = d["recovery"]
        else:
            self.action = None
            self.set_state("land")
