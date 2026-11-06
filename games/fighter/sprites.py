"""Çizimli (sprite) karakterler: kare seçimi, çizim, gövde ve vuruş kutuları.

Çizimler: https://github.com/sujalvk888/StreetFighter2D-Game (MIT lisansı, Sujal V Kanchan)
"""
import json
import math
import os

import pygame

from engine.core import resource_path

ATTACK_ANIM = {"jab": "Attack_1", "cross": "Attack_3", "kick": "Attack_2", "round": "Attack_2", "cjab": "Attack_1",
               "sweep": "Attack_2", "air_p": "Attack_1", "air_k": "Attack_2"}

_sets = {}


class SpriteSet:
    def __init__(self, cid):
        self.cid = cid
        base = resource_path("assets", "sprites", cid)
        with open(os.path.join(base, "meta.json"), encoding="utf-8") as f:
            self.meta = json.load(f)
        self.base = base
        self.anims = {}
        self.cache = {}
        for anim, frames in self.meta["anims"].items():
            self.anims[anim] = frames
            # vuruş anı: en öne uzanan kare
            peak = max(range(len(frames)), key=lambda i: frames[i]["reach"][0]) if frames else 0
            self.meta.setdefault("peak", {})[anim] = peak
        self.height = self.meta["height"]
        self.width = self.meta["width"]
        try:
            self.portrait = pygame.image.load(os.path.join(base, "portrait.png")).convert_alpha()
        except Exception:
            self.portrait = None

    def image(self, anim, idx, facing, variant=None, scale=1.0):
        key = (anim, idx, facing, variant, scale)
        img = self.cache.get(key)
        if img is None:
            fr = self.anims[anim][idx]
            if (anim, idx, 1, None, 1.0) not in self.cache:
                self.cache[(anim, idx, 1, None, 1.0)] = pygame.image.load(os.path.join(self.base, fr["f"])).convert_alpha()
            img = self.cache[(anim, idx, 1, None, 1.0)]
            if scale != 1.0:
                img = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * scale)), max(1, int(img.get_height() * scale))))
            if variant == "flash":
                img = img.copy()
                img.fill((170, 170, 170, 0), special_flags=pygame.BLEND_RGBA_ADD)
            elif variant == "dark":
                img = img.copy()
                img.fill((90, 90, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
            if facing < 0:
                img = pygame.transform.flip(img, True, False)
            self.cache[key] = img
        return img

    def preload(self):
        for anim, frames in self.anims.items():
            for i in range(len(frames)):
                for fc in (1, -1):
                    self.image(anim, i, fc)


def get(cid):
    s = _sets.get(cid)
    if s is None:
        s = SpriteSet(cid)
        _sets[cid] = s
    return s


def _prog(n, k):
    return max(0, min(n - 1, int(k * (n - 1) + 0.5)))


def select(f):
    """Dövüşçünün durumuna göre (animasyon, kare) seçer."""
    ss = get(f.ch["sprite"])
    A = ss.anims
    st = f.state
    a = f.action
    if st == "attack" and a is not None:
        d = a.data
        if a.kind == "normal":
            anim = ATTACK_ANIM.get(a.name, "Attack_1")
            n = len(A[anim])
            p = ss.meta["peak"][anim]
            s_, act, r = d["s"], d["a"], d["r"]
            if a.t < s_:
                return anim, _prog(p + 1, a.t / s_)
            if a.t < s_ + act:
                return anim, p
            k = min(1.0, (a.t - s_ - act) / max(1, r))
            return anim, min(n - 1, p + int(k * (n - 1 - p) + 0.5))
        anim = d.get("anim", "Attack_3")
        n = len(A[anim])
        p = ss.meta["peak"][anim]
        typ = d["type"]
        if a.phase == "startup":
            return anim, _prog(p + 1, a.t / max(1, d["startup"]))
        if a.phase == "active":
            if typ == "dash" and d.get("spin"):
                # dönerek tekme: ileri-geri kareler arasında salınım
                return anim, max(0, p - 2 + (a.t // 3) % 3)
            if typ == "rising" and f.vy > 2:
                return "JumpLoop", _prog(len(A["JumpLoop"]), 0.75)
            if typ == "stomp":
                k = 0.3 if f.vy < 0 else 0.8
                return "JumpLoop", _prog(len(A["JumpLoop"]), k)
            return anim, p
        # toparlanma
        if not f.grounded:
            return "JumpLoop", _prog(len(A["JumpLoop"]), 0.85)
        if typ == "stomp":
            return "Land", _prog(len(A["Land"]), 0.5)
        k = 1 - max(0, a.timer) / max(1, d["recovery"])
        return anim, min(n - 1, p + int(k * (n - 1 - p) + 0.5))
    if st in ("idle", "intro"):
        if f.back_block_pose:
            return "Block", len(A["Block"]) // 2
        return "Idle", int(f.anim_t * 11) % len(A["Idle"])
    if st == "victory":
        n = len(A["Attack_3"])
        if f.st < 25:
            return "Attack_3", _prog(n, f.st / 25)
        return "Idle", int(f.anim_t * 9) % len(A["Idle"])
    if st == "walk":
        if f.back_block_pose:
            return "Block", len(A["Block"]) // 2
        n = len(A["Walk"])
        return "Walk", int((f.walk_phase / math.tau) * n * 1.0) % n
    if st == "crouch":
        n = len(A["Land"])
        return "Land", _prog(n, 0.35)
    if st == "jump":
        if f.st < 5 and f.vy < 0:
            return "JumpStart", _prog(len(A["JumpStart"]), 0.5 + f.st / 10)
        k = (f.vy + f.ch["jump"]) / (2 * f.ch["jump"])
        return "JumpLoop", _prog(len(A["JumpLoop"]), max(0.0, min(1.0, k)))
    if st == "land":
        return "Land", _prog(len(A["Land"]), 0.35 + f.st / 10)
    if st == "hitstun":
        k = 1 - f.stun / max(1, getattr(f, "stun0", 1))
        return "Hit", _prog(len(A["Hit"]), min(1.0, k * 1.2) * 0.75)
    if st == "blockstun":
        return "Block", len(A["Block"]) // 2
    if st == "air_hit":
        return "Knockout", _prog(len(A["Knockout"]), min(0.45, f.st / 60))
    if st in ("down", "ko"):
        n = len(A["Knockout"])
        return "Knockout", _prog(n, min(1.0, 0.45 + f.st / 40))
    if st == "getup":
        n = len(A["Land"])
        return "Land", _prog(n, 0.35 + 0.65 * min(1.0, f.st / 16))
    return "Idle", 0


def frame_meta(f):
    anim, idx = select(f)
    ss = get(f.ch["sprite"])
    return ss, anim, idx, ss.anims[anim][idx]


def draw(surf, f, x, y, flash=False, dark=False, aura=None):
    ss, anim, idx, fr = frame_meta(f)
    variant = "flash" if flash else ("dark" if dark else None)
    img = ss.image(anim, idx, f.facing, variant)
    ox = fr["ox"] if f.facing > 0 else -fr["ox"] - fr["w"]
    surf.blit(img, (int(x + ox), int(y + fr["oy"])))


def draw_static(surf, cid, anim, idx, x, y, facing=1, scale=1.0, dark=False):
    ss = get(cid)
    idx %= len(ss.anims[anim])
    fr = ss.anims[anim][idx]
    img = ss.image(anim, idx, facing, "dark" if dark else None, scale)
    ox = (fr["ox"] if facing > 0 else -fr["ox"] - fr["w"]) * scale
    surf.blit(img, (int(x + ox), int(y + fr["oy"] * scale)))


def hurt_rect(f):
    ss, anim, idx, fr = frame_meta(f)
    b = fr["body"]
    if f.facing > 0:
        l, r = b[0], b[2]
    else:
        l, r = -b[2], -b[0]
    half = ss.width * 0.42
    l = max(l, -half)
    r = min(r, half)
    top, bot = b[1], b[3]
    return pygame.Rect(int(f.x + l), int(f.y + top), int(max(10, r - l)), int(max(10, bot - top)))


def attack_point(f):
    ss, anim, idx, fr = frame_meta(f)
    if anim.startswith("Attack"):
        fr = ss.anims[anim][ss.meta["peak"][anim]]
    rx, ry = fr["reach"]
    rx = max(rx - 14, ss.width * 0.3)
    return f.x + rx * f.facing, f.y + ry
