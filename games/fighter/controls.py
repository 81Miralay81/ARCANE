"""Klavye, gamepad ve bilgisayar (CPU) kontrolleri."""
import random

import pygame

from games.fighter.fighter import GROUND, InputState

KEYMAPS = {
    0: dict(left=[pygame.K_a], right=[pygame.K_d], up=[pygame.K_w], down=[pygame.K_s], p=[pygame.K_f], k=[pygame.K_g]),
    1: dict(left=[pygame.K_LEFT], right=[pygame.K_RIGHT], up=[pygame.K_UP], down=[pygame.K_DOWN],
            p=[pygame.K_k, pygame.K_KP1], k=[pygame.K_l, pygame.K_KP2]),
}
# Tek oyunculu modda iki tuş takımı da 1. oyuncuyu kontrol eder
KEYMAP_SOLO = {key: KEYMAPS[0][key] + KEYMAPS[1][key] for key in KEYMAPS[0]}


class HumanController:
    def __init__(self, keymap, joystick=None, touch=None):
        self.map = keymap
        self.joy = joystick
        self.touch = touch
        self.prev_p = False
        self.prev_k = False

    def poll(self, fighter, opp, scene):
        keys = pygame.key.get_pressed()

        def held(name):
            return any(keys[k] for k in self.map[name])

        left, right, up, down = held("left"), held("right"), held("up"), held("down")
        p, k = held("p"), held("k")
        if self.joy is not None:
            try:
                if self.joy.get_numhats():
                    hx, hy = self.joy.get_hat(0)
                    left |= hx < 0
                    right |= hx > 0
                    up |= hy > 0
                    down |= hy < 0
                ax = self.joy.get_axis(0) if self.joy.get_numaxes() > 0 else 0
                ay = self.joy.get_axis(1) if self.joy.get_numaxes() > 1 else 0
                left |= ax < -0.5
                right |= ax > 0.5
                up |= ay < -0.6
                down |= ay > 0.5
                nb = self.joy.get_numbuttons()
                p |= any(self.joy.get_button(b) for b in (0, 2) if b < nb)
                k |= any(self.joy.get_button(b) for b in (1, 3) if b < nb)
            except Exception:
                pass
        special = None
        tp = tk = False
        if self.touch is not None:
            l2, r2, u2, d2 = self.touch.dirs()
            left |= l2
            right |= r2
            up |= u2
            down |= d2
            tp = self.touch.take("P")
            tk = self.touch.take("K")
            for i in range(3):
                if self.touch.take("S%d" % i):
                    special = i
            if self.touch.take("SUP"):
                special = "super"
        inp = InputState(left, right, up, down, (p and not self.prev_p) or tp, (k and not self.prev_k) or tk, p, k, special)
        self.prev_p, self.prev_k = p, k
        return inp


class CPUController:
    """Basit ama oynanabilir yapay zekâ. Gerçek tuş komutlarını taklit eder."""

    PROFILES = [
        dict(react=16, aggr=0.55, block=0.30, special=0.18, anti_air=0.30, combo=0.45, approach=0.75),  # Kolay
        dict(react=9, aggr=0.75, block=0.55, special=0.28, anti_air=0.60, combo=0.80, approach=0.92),   # Normal
        dict(react=5, aggr=0.90, block=0.80, special=0.35, anti_air=0.90, combo=1.00, approach=1.00),   # Zor
    ]

    def __init__(self, difficulty=1):
        self.prof = self.PROFILES[max(0, min(2, difficulty))]
        self.queue = []
        self.cool = 30
        self.hold_block = 0
        self.rnd = random.Random()
        self.mode = "neutral"
        self.mode_t = 0

    def _seq(self, steps):
        """steps: [(dirs, button, frames)] dirs: 'f','b','d','u','df','db' gibi"""
        for dirs, btn, n in steps:
            for i in range(n):
                self.queue.append((dirs, btn if i == 0 else None))

    def _dirs_to_input(self, dirs, btn, facing):
        fwd, back = ("right", "left") if facing > 0 else ("left", "right")
        d = dict(left=False, right=False, up=False, down=False)
        if "f" in dirs:
            d[fwd] = True
        if "b" in dirs:
            d[back] = True
        if "u" in dirs:
            d["up"] = True
        if "d" in dirs:
            d["down"] = True
        return InputState(d["left"], d["right"], d["up"], d["down"], btn == "P", btn == "K", btn == "P", btn == "K")

    def poll(self, me, opp, scene):
        pr = self.prof
        r = self.rnd.random
        dist = abs(opp.x - me.x)
        facing = me.facing
        if me.state in ("hitstun", "air_hit", "down", "ko", "victory", "intro") or scene.freeze_input:
            self.queue.clear()
            return InputState()

        # kombo devamı: vuruş tuttuysa zincir / özel hareket iptali
        a = me.action
        if a and a.kind == "normal" and a.confirmed and not self.queue and r() < pr["combo"]:
            if a.name == "jab":
                self._seq([("", "P", 1)])
            elif a.name == "cross":
                if r() < 0.5:
                    self._special(me)
                else:
                    self._seq([("", "K", 1)])
            elif a.name == "cjab":
                self._seq([("d", "K", 1)])

        if self.queue:
            dirs, btn = self.queue.pop(0)
            return self._dirs_to_input(dirs, btn, facing)

        # savunma: rakip saldırıyorsa veya mermi geliyorsa
        threat = opp.action is not None or scene.projectile_threat(me)
        if threat and dist < 330 and r() < pr["block"] * 0.25 and me.state in ("idle", "walk", "crouch"):
            low = opp.action is not None and opp.action.data.get("height") == "low"
            self.hold_block = int(6 + 8 * r())
            self._seq([("db" if low or r() < 0.3 else "b", None, self.hold_block)])
            dirs, btn = self.queue.pop(0)
            return self._dirs_to_input(dirs, btn, facing)

        # hava saldırısına karşı kartal yumruğu
        if not opp.grounded and opp.vy > -6 and dist < 190 and r() < pr["anti_air"] * 0.2 and me.can_act():
            dp = next((s for s in me.ch["specials"] if s["motion"] == "dp"), None)
            if dp:
                self._seq([("f", None, 1), ("d", None, 1), ("df", dp["button"], 1)])
                dirs, btn = self.queue.pop(0)
                return self._dirs_to_input(dirs, btn, facing)

        self.cool -= 1
        if self.cool > 0:
            # bekleme sırasında rakibin üstüne yürü (pasif kalma)
            if dist > 120 and r() < pr["approach"]:
                return self._dirs_to_input("f", None, facing)
            return InputState()
        self.cool = int(pr["react"] * (0.6 + r()))

        if me.meter >= 100 and r() < pr["special"] * 0.6 and dist < 520:
            sup = me.ch["super"]
            self._seq([("d", None, 1), ("df", None, 1), ("f", None, 1), ("d", None, 1), ("df", None, 1), ("f", sup["button"], 1)])
        elif dist > 380:
            x = r()
            if x < pr["special"] * 1.3:
                self._special(me, ranged=True)
            elif x < 0.45:
                self._seq([("uf", None, 2), ("", None, 14), ("", "K", 1)])
            else:
                self._seq([("f", None, int(16 + 16 * r()))])
        elif dist > 180:
            x = r()
            if x < pr["special"]:
                self._special(me)
            elif x < pr["special"] + pr["aggr"] * 0.35:
                self._seq([("uf", None, 2), ("", None, 16), ("", "K", 1)])
            elif x < 0.9:
                self._seq([("f", None, int(8 + 12 * r()))])
            else:
                self._seq([("b", None, int(6 + 8 * r()))])
        else:
            x = r()
            if x < pr["aggr"]:
                choice = self.rnd.choice(["jab", "jab", "kick", "cjab", "sweep", "throwcombo"])
                if choice == "jab":
                    self._seq([("", "P", 1), ("", None, 6), ("", "P", 1)])
                elif choice == "kick":
                    self._seq([("", "K", 1)])
                elif choice == "cjab":
                    self._seq([("d", "P", 1), ("d", None, 8), ("d", "K", 1)])
                elif choice == "sweep":
                    self._seq([("d", "K", 1)])
                else:
                    self._seq([("", "P", 1), ("", None, 7), ("", "P", 1), ("", None, 9), ("", "K", 1)])
            elif x < pr["aggr"] + pr["special"]:
                self._special(me)
            elif x < 0.93:
                self._seq([("", "P", 1), ("", None, 6), ("", "P", 1), ("", None, 8), ("", "K", 1)])
            else:
                self._seq([("b", None, int(6 + 8 * r()))])
        if self.queue:
            dirs, btn = self.queue.pop(0)
            return self._dirs_to_input(dirs, btn, facing)
        return InputState()

    def _special(self, me, ranged=False):
        specs = me.ch["specials"]
        if ranged:
            specs = [s for s in specs if s["type"] == "projectile"] or specs
        sp = self.rnd.choice(specs)
        m = sp["motion"]
        if m == "qcf":
            self._seq([("d", None, 1), ("df", None, 1), ("f", sp["button"], 1)])
        elif m == "qcb":
            self._seq([("d", None, 1), ("db", None, 1), ("b", sp["button"], 1)])
        elif m == "dp":
            self._seq([("f", None, 1), ("d", None, 1), ("df", sp["button"], 1)])
