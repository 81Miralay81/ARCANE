"""Karakterlerin iskelet tabanlı çizimi.

Her poz eklem açılarından oluşur. Açılar "aşağı" yönden ölçülür,
pozitif değer karakterin baktığı yöne doğru döndürür.
"""
import math

import pygame

from engine.core import shade

POSE_KEYS = ("torso", "head", "ua_f", "fa_f", "ua_b", "fa_b", "th_f", "sh_f", "th_b", "sh_b", "hx", "hy")

BASE = dict(torso=8, head=-4, ua_f=45, fa_f=105, ua_b=25, fa_b=115, th_f=22, sh_f=-14, th_b=-20, sh_b=-6, hx=0, hy=0)


def P(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


POSES = {
    "idle": P(),
    "crouch": P(torso=22, head=-14, ua_f=62, fa_f=95, ua_b=40, fa_b=110, th_f=88, sh_f=-100, th_b=30, sh_b=-112),
    "jump": P(torso=10, ua_f=70, fa_f=90, ua_b=30, fa_b=120, th_f=95, sh_f=-125, th_b=55, sh_b=-120),
    "jump_up": P(torso=4, ua_f=150, fa_f=10, ua_b=120, fa_b=30, th_f=40, sh_f=-70, th_b=-5, sh_b=-30),
    # yumruklar
    "jab_s": P(torso=14, ua_f=65, fa_f=70, ua_b=20, fa_b=120),
    "jab": P(torso=16, ua_f=92, fa_f=2, ua_b=18, fa_b=125, th_f=28),
    "cross_s": P(torso=-2, ua_f=40, fa_f=110, ua_b=40, fa_b=100, th_f=18, th_b=-24),
    "cross": P(torso=30, head=6, ua_f=20, fa_f=120, ua_b=94, fa_b=0, th_f=34, sh_f=-18, th_b=-30, sh_b=0, hx=12),
    # tekmeler
    "kick_s": P(torso=-8, ua_f=60, fa_f=95, th_f=70, sh_f=-110, th_b=-8, sh_b=0),
    "kick": P(torso=-18, head=8, ua_f=30, fa_f=110, ua_b=-10, fa_b=60, th_f=98, sh_f=-4, th_b=-6, sh_b=0),
    "round_s": P(torso=-14, ua_f=50, fa_f=100, ua_b=-15, fa_b=70, th_f=95, sh_f=-120, th_b=-10, sh_b=0),
    "round": P(torso=-30, head=14, ua_f=20, fa_f=80, ua_b=-30, fa_b=40, th_f=128, sh_f=-6, th_b=-10, sh_b=0, hx=-6),
    # çömelik saldırılar
    "cjab": P(torso=26, head=-14, ua_f=86, fa_f=0, ua_b=40, fa_b=110, th_f=88, sh_f=-100, th_b=30, sh_b=-112),
    "sweep_s": P(torso=34, head=-20, ua_f=-10, fa_f=40, ua_b=60, fa_b=60, th_f=60, sh_f=-90, th_b=40, sh_b=-130),
    "sweep": P(torso=44, head=-28, ua_f=-20, fa_f=30, ua_b=-40, fa_b=20, th_f=88, sh_f=-2, th_b=30, sh_b=-130),
    # hava
    "air_p": P(torso=18, ua_f=78, fa_f=-4, ua_b=20, fa_b=120, th_f=90, sh_f=-120, th_b=50, sh_b=-110),
    "air_k": P(torso=-6, ua_f=110, fa_f=40, ua_b=-20, fa_b=60, th_f=62, sh_f=0, th_b=70, sh_b=-130),
    # savunma / hasar
    "block": P(torso=-4, head=-12, ua_f=78, fa_f=112, ua_b=64, fa_b=118, th_f=16, th_b=-26),
    "cblock": P(torso=12, head=-20, ua_f=80, fa_f=110, ua_b=66, fa_b=118, th_f=88, sh_f=-100, th_b=30, sh_b=-112),
    "hit": P(torso=-22, head=-30, ua_f=-10, fa_f=50, ua_b=-30, fa_b=40, th_f=14, sh_f=-8, th_b=-30, sh_b=-6, hx=-6),
    "hit_low": P(torso=34, head=26, ua_f=30, fa_f=20, ua_b=10, fa_b=30, th_f=40, sh_f=-30, th_b=-18, sh_b=-20),
    "air_hit": P(torso=-50, head=-30, ua_f=150, fa_f=20, ua_b=170, fa_b=10, th_f=60, sh_f=-60, th_b=20, sh_b=-40),
    "down": P(torso=-92, head=-90, ua_f=-120, fa_f=-20, ua_b=-150, fa_b=10, th_f=86, sh_f=-4, th_b=96, sh_b=-10),
    "getup": P(torso=30, head=-10, ua_f=10, fa_f=40, ua_b=-10, fa_b=30, th_f=92, sh_f=-110, th_b=20, sh_b=-120),
    # özel hareketler
    "push_s": P(torso=-10, ua_f=-30, fa_f=100, ua_b=-40, fa_b=110, th_f=26, th_b=-30),
    "push": P(torso=22, head=6, ua_f=92, fa_f=0, ua_b=86, fa_b=8, th_f=40, sh_f=-28, th_b=-36, sh_b=0, hx=10),
    "upper_s": P(torso=34, head=-14, ua_f=20, fa_f=60, ua_b=10, fa_b=90, th_f=80, sh_f=-100, th_b=24, sh_b=-108),
    "upper": P(torso=6, head=10, ua_f=170, fa_f=6, ua_b=20, fa_b=110, th_f=70, sh_f=-110, th_b=-10, sh_b=-10),
    "spin_a": P(torso=-6, head=0, ua_f=100, fa_f=20, ua_b=-90, fa_b=20, th_f=96, sh_f=0, th_b=10, sh_b=-60),
    "spin_b": P(torso=6, head=0, ua_f=-90, fa_f=20, ua_b=100, fa_b=20, th_f=10, sh_f=-60, th_b=-96, sh_b=0),
    "flykick": P(torso=-30, head=12, ua_f=150, fa_f=30, ua_b=-40, fa_b=50, th_f=90, sh_f=0, th_b=40, sh_b=-120),
    "charge": P(torso=52, head=-36, ua_f=100, fa_f=60, ua_b=40, fa_b=110, th_f=40, sh_f=-30, th_b=-46, sh_b=0, hx=8),
    "stomp_air": P(torso=0, ua_f=165, fa_f=30, ua_b=160, fa_b=40, th_f=70, sh_f=-120, th_b=40, sh_b=-110),
    "stomp": P(torso=34, head=-20, ua_f=90, fa_f=-30, ua_b=80, fa_b=-20, th_f=70, sh_f=-90, th_b=20, sh_b=-110),
    "slam_s": P(torso=-14, head=10, ua_f=170, fa_f=20, ua_b=165, fa_b=25, th_f=20, th_b=-24),
    "slam": P(torso=56, head=-30, ua_f=50, fa_f=10, ua_b=45, fa_b=12, th_f=44, sh_f=-50, th_b=-30, sh_b=0, hx=10),
    "win": P(torso=-4, head=10, ua_f=172, fa_f=4, ua_b=30, fa_b=110, th_f=10, sh_f=-4, th_b=-12, sh_b=-2),
    "taunt": P(torso=0, head=4, ua_f=110, fa_f=70, ua_b=-20, fa_b=130, th_f=14, th_b=-14),
}


def blend(a, b, t):
    return {k: a[k] + (b[k] - a[k]) * t for k in POSE_KEYS}


def _dir(angle):
    r = math.radians(angle)
    return math.sin(r), math.cos(r)


class Body:
    """Bir pozdan eklem noktalarını hesaplar (bakış yönü sağa)."""

    def __init__(self, ch):
        s = ch["scale"]
        self.s = s
        self.L = dict(torso=60 * s, neck=13 * s, head=19 * s * ch.get("head_k", 1.0), ua=34 * s, fa=32 * s,
                      th=48 * s, sh=46 * s)

    def joints(self, pose):
        L = self.L
        hip = (pose["hx"] * self.s, pose["hy"] * self.s)
        tx, ty = math.sin(math.radians(pose["torso"])), -math.cos(math.radians(pose["torso"]))
        chest = (hip[0] + tx * L["torso"] * 0.55, hip[1] + ty * L["torso"] * 0.55)
        sho = (hip[0] + tx * L["torso"], hip[1] + ty * L["torso"])
        ha = pose["torso"] + pose["head"]
        hx, hy = math.sin(math.radians(ha)), -math.cos(math.radians(ha))
        neck = (sho[0] + hx * L["neck"], sho[1] + hy * L["neck"])
        head = (neck[0] + hx * L["head"] * 0.9, neck[1] + hy * L["head"] * 0.9)
        J = dict(hip=hip, chest=chest, sho=sho, neck=neck, head=head)
        for side in ("f", "b"):
            a1 = pose["ua_" + side]
            a2 = a1 + pose["fa_" + side]
            d1, d2 = _dir(a1), _dir(a2)
            el = (sho[0] + d1[0] * L["ua"], sho[1] + d1[1] * L["ua"])
            ha_ = (el[0] + d2[0] * L["fa"], el[1] + d2[1] * L["fa"])
            J["el_" + side], J["hand_" + side] = el, ha_
            t1 = pose["th_" + side]
            t2 = t1 + pose["sh_" + side]
            e1, e2 = _dir(t1), _dir(t2)
            kn = (hip[0] + e1[0] * L["th"], hip[1] + e1[1] * L["th"])
            ft = (kn[0] + e2[0] * L["sh"], kn[1] + e2[1] * L["sh"])
            J["knee_" + side], J["foot_" + side] = kn, ft
            J["ang_shin_" + side] = t2
        return J

    def ground_offset(self, J):
        """Yerdeyken en alttaki noktanın y=0'a oturması için kaydırma."""
        r = self.L["head"]
        ys = [J["foot_f"][1] + 6 * self.s, J["foot_b"][1] + 6 * self.s, J["knee_f"][1] + 8 * self.s,
              J["knee_b"][1] + 8 * self.s, J["hip"][1] + 12 * self.s, J["sho"][1] + 12 * self.s,
              J["head"][1] + r, J["hand_f"][1] + 6 * self.s, J["hand_b"][1] + 6 * self.s]
        return -max(ys)


def _capsule(surf, a, b, w, color, outline):
    pygame.draw.line(surf, outline, a, b, int(w + 4))
    pygame.draw.circle(surf, outline, (int(a[0]), int(a[1])), int(w / 2 + 2))
    pygame.draw.circle(surf, outline, (int(b[0]), int(b[1])), int(w / 2 + 2))
    pygame.draw.line(surf, color, a, b, int(w))
    pygame.draw.circle(surf, color, (int(a[0]), int(a[1])), int(w / 2))
    pygame.draw.circle(surf, color, (int(b[0]), int(b[1])), int(w / 2))


def _limb(surf, a, b, w1, w2, color, outline, hl=None):
    """Konik uzuv: iki ucu farklı kalınlıkta, kenar çizgili ve parlak şeritli."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1
    nx, ny = -dy / d, dx / d
    pts = [(a[0] + nx * w1 / 2, a[1] + ny * w1 / 2), (b[0] + nx * w2 / 2, b[1] + ny * w2 / 2),
           (b[0] - nx * w2 / 2, b[1] - ny * w2 / 2), (a[0] - nx * w1 / 2, a[1] - ny * w1 / 2)]
    po = [(a[0] + nx * (w1 / 2 + 2.5), a[1] + ny * (w1 / 2 + 2.5)), (b[0] + nx * (w2 / 2 + 2.5), b[1] + ny * (w2 / 2 + 2.5)),
          (b[0] - nx * (w2 / 2 + 2.5), b[1] - ny * (w2 / 2 + 2.5)), (a[0] - nx * (w1 / 2 + 2.5), a[1] - ny * (w1 / 2 + 2.5))]
    pygame.draw.polygon(surf, outline, po)
    pygame.draw.circle(surf, outline, (int(a[0]), int(a[1])), int(w1 / 2 + 2.5))
    pygame.draw.circle(surf, outline, (int(b[0]), int(b[1])), int(w2 / 2 + 2.5))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.circle(surf, color, (int(a[0]), int(a[1])), int(w1 / 2))
    pygame.draw.circle(surf, color, (int(b[0]), int(b[1])), int(w2 / 2))
    if hl:
        k = 0.22
        h1 = (a[0] + nx * w1 * k, a[1] + ny * w1 * k)
        h2 = (b[0] + nx * w2 * k, b[1] + ny * w2 * k)
        pygame.draw.line(surf, hl, h1, h2, max(2, int(min(w1, w2) * 0.22)))


def draw_fighter(*args, **kw):
    """Karakteri ekrana çizer. (x, y) ayakların zemine bastığı nokta."""
    kw.pop("ss", None)
    return draw_fighter_simple(*args, **kw)


def draw_fighter_simple(surf, ch, pose, x, y, facing, grounded=True, flash=0, alpha_tint=None, t=0.0, palette=None):
    pal = palette or ch["palette"]
    body = Body(ch)
    J = body.joints(pose)
    oy = body.ground_offset(J) if grounded else -(body.L["th"] + body.L["sh"]) * 0.92
    s = body.s
    OUT = (16, 12, 20)

    def T(p):
        return (x + p[0] * facing, y + p[1] + oy)

    skin, skin_d = pal["skin"], shade(pal["skin"], 0.78)
    top, top_d = pal["top"], shade(pal["top"], 0.8)
    pants, pants_d = pal["pants"], shade(pal["pants"], 0.8)
    glove, belt, hair, accent = pal["glove"], pal["belt"], pal["hair"], pal["accent"]
    if flash:
        skin = skin_d = top = top_d = pants = pants_d = glove = belt = hair = accent = (255, 255, 255)
    if alpha_tint:
        k = alpha_tint
        skin, skin_d, top, top_d, pants, pants_d, glove, belt, hair, accent = [
            tuple(min(255, int(c[i] * 0.7 + k[i] * 0.3)) for i in range(3))
            for c in (skin, skin_d, top, top_d, pants, pants_d, glove, belt, hair, accent)]

    bulk = ch.get("bulk", 1.0)
    arm_w = 15 * s * bulk
    leg_w = 19 * s * bulk
    sleeves = ch.get("sleeves", False)

    def leg(side, dark):
        hip, kn, ft = T(J["hip"]), T(J["knee_" + side]), T(J["foot_" + side])
        c = pants_d if dark else pants
        _limb(surf, hip, kn, leg_w * 1.15, leg_w * 0.95, c, OUT, None if dark else shade(c, 1.25))
        _limb(surf, kn, ft, leg_w * 0.95, leg_w * 0.7, c, OUT, None if dark else shade(c, 1.25))
        # ayak / ayakkabı
        ang = J["ang_shin_" + side]
        fa = math.radians(ang - 90)
        fdir = (math.sin(fa) * facing, math.cos(fa))
        toe = (ft[0] + fdir[0] * 14 * s, ft[1] + fdir[1] * 14 * s)
        fc = pal.get("shoe", skin_d if dark else skin)
        if dark and "shoe" in pal:
            fc = shade(fc, 0.75)
        _capsule(surf, ft, toe, 11 * s, fc, OUT)
        if pal.get("wrap"):
            pygame.draw.line(surf, pal["wrap"], (ft[0] - 6 * s, ft[1] - 3 * s), (ft[0] + 6 * s, ft[1] - 3 * s), max(2, int(4 * s)))

    def arm(side, dark):
        sh, el, hd = T(J["sho"]), T(J["el_" + side]), T(J["hand_" + side])
        sk = skin_d if dark else skin
        upper = (top_d if dark else top) if sleeves else sk
        _limb(surf, sh, el, arm_w * 1.1, arm_w * 0.9, upper, OUT, None if dark else shade(upper, 1.2))
        _limb(surf, el, hd, arm_w * 0.9, arm_w * 0.75, sk, OUT, None if dark else shade(sk, 1.15))
        gc = shade(glove, 0.75) if dark else glove
        r = int(10 * s * bulk)
        pygame.draw.circle(surf, OUT, (int(hd[0]), int(hd[1])), r + 3)
        pygame.draw.circle(surf, gc, (int(hd[0]), int(hd[1])), r)
        if not dark:
            pygame.draw.circle(surf, shade(gc, 1.35), (int(hd[0] - 3 * s * facing), int(hd[1] - 3 * s)), max(2, r // 3))

    # gölge
    leg(("b"), True)
    arm("b", True)

    # gövde
    hip, sho, chest = T(J["hip"]), T(J["sho"]), T(J["chest"])
    tw = 40 * s * bulk
    if ch.get("bare_chest"):
        _limb(surf, hip, sho, tw * 0.92, tw * 1.12, skin, OUT, shade(skin, 1.12))
        # kas çizgileri
        pygame.draw.line(surf, skin_d, chest, ((chest[0] + sho[0]) / 2, (chest[1] + sho[1]) / 2), max(2, int(3 * s)))
        if "top" in pal and ch.get("vest"):
            _limb(surf, (hip[0] - 0, hip[1]), sho, tw * 0.6, tw * 0.7, top, OUT)
    else:
        _limb(surf, hip, sho, tw * 0.92, tw * 1.12, top, OUT, shade(top, 1.18))
        # yaka (V)
        nk = T(J["neck"])
        v1 = (sho[0] + (chest[0] - sho[0]) * 0.55, sho[1] + (chest[1] - sho[1]) * 0.55)
        pygame.draw.polygon(surf, skin, [(nk[0] - 9 * s, nk[1] + 4 * s), (nk[0] + 9 * s, nk[1] + 4 * s), v1])
        pygame.draw.line(surf, top_d, (nk[0] - 9 * s, nk[1] + 4 * s), v1, max(2, int(3 * s)))
        pygame.draw.line(surf, top_d, (nk[0] + 9 * s, nk[1] + 4 * s), v1, max(2, int(3 * s)))
    # kalça / kemer
    _capsule(surf, (hip[0] - 14 * s * bulk, hip[1]), (hip[0] + 14 * s * bulk, hip[1]), 22 * s, pants, OUT)
    bv = (sho[0] - hip[0], sho[1] - hip[1])
    bl = math.hypot(*bv) or 1
    bpos = (hip[0] + bv[0] / bl * 8 * s, hip[1] + bv[1] / bl * 8 * s)
    pygame.draw.line(surf, OUT, (bpos[0] - 19 * s * bulk, bpos[1]), (bpos[0] + 19 * s * bulk, bpos[1]), int(11 * s))
    pygame.draw.line(surf, belt, (bpos[0] - 17 * s * bulk, bpos[1]), (bpos[0] + 17 * s * bulk, bpos[1]), int(7 * s))
    # kuşak uçları dalgalanır
    sway = math.sin(t * 6) * 4 * s
    tail = [(bpos[0] - 10 * s * facing, bpos[1]), (bpos[0] - 18 * s * facing + sway, bpos[1] + 18 * s),
            (bpos[0] - 12 * s * facing + sway, bpos[1] + 20 * s)]
    pygame.draw.line(surf, OUT, tail[0], tail[1], max(5, int(9 * s)))
    pygame.draw.line(surf, OUT, tail[0], tail[2], max(5, int(9 * s)))
    pygame.draw.line(surf, belt, tail[0], tail[1], max(3, int(5 * s)))
    pygame.draw.line(surf, belt, tail[0], tail[2], max(3, int(5 * s)))

    # kafa
    hp = T(J["head"])
    hr = body.L["head"]
    nk = T(J["neck"])
    _capsule(surf, T(J["sho"]), nk, 13 * s, skin_d, OUT)
    pygame.draw.circle(surf, OUT, (int(hp[0]), int(hp[1])), int(hr + 3))
    pygame.draw.circle(surf, skin, (int(hp[0]), int(hp[1])), int(hr))
    ha = math.radians(pose["torso"] + pose["head"])
    upx, upy = math.sin(ha) * facing, -math.cos(ha)
    fx, fy = math.cos(ha) * facing, math.sin(ha)  # yüzün baktığı yön
    style = ch.get("hair_style", "short")
    if style == "short":
        cap = [(hp[0] + upx * hr * 1.05 - fx * hr * 0.2, hp[1] + upy * hr * 1.05 - fy * hr * 0.2)]
        pygame.draw.circle(surf, hair, (int(hp[0] + upx * hr * 0.35 - fx * hr * 0.25), int(hp[1] + upy * hr * 0.35 - fy * hr * 0.25)), int(hr * 0.92))
        for i in range(4):
            a = -1.2 + i * 0.55
            sx = hp[0] + (upx * math.cos(a) - fx * math.sin(a)) * hr * 1.15
            sy = hp[1] + (upy * math.cos(a) - fy * math.sin(a)) * hr * 1.15
            pygame.draw.circle(surf, hair, (int(sx), int(sy)), int(hr * 0.42))
        pygame.draw.circle(surf, skin, (int(hp[0] + fx * hr * 0.32 - upx * hr * 0.12), int(hp[1] + fy * hr * 0.32 - upy * hr * 0.12)), int(hr * 0.72))
        del cap
    elif style == "ponytail":
        pygame.draw.circle(surf, hair, (int(hp[0] + upx * hr * 0.3 - fx * hr * 0.3), int(hp[1] + upy * hr * 0.3 - fy * hr * 0.3)), int(hr * 0.95))
        pygame.draw.circle(surf, skin, (int(hp[0] + fx * hr * 0.35 - upx * hr * 0.15), int(hp[1] + fy * hr * 0.35 - upy * hr * 0.15)), int(hr * 0.7))
        base = (hp[0] - fx * hr * 0.9 + upx * hr * 0.5, hp[1] - fy * hr * 0.9 + upy * hr * 0.5)
        sw = math.sin(t * 7) * 6 * s
        p1 = (base[0] - fx * 16 * s, base[1] - fy * 16 * s + 8 * s + sw * 0.5)
        p2 = (p1[0] - fx * 16 * s, p1[1] + 14 * s + sw)
        _limb(surf, base, p1, 12 * s, 10 * s, hair, OUT)
        _limb(surf, p1, p2, 10 * s, 4 * s, hair, OUT)
        pygame.draw.circle(surf, accent, (int(base[0]), int(base[1])), int(4 * s))
    elif style == "bald":
        pygame.draw.circle(surf, shade(skin, 1.15), (int(hp[0] + upx * hr * 0.4 - fx * hr * 0.2), int(hp[1] + upy * hr * 0.4 - fy * hr * 0.2)), int(hr * 0.35))
        # sakal
        chin = (hp[0] + fx * hr * 0.45 - upx * hr * 0.55, hp[1] + fy * hr * 0.45 - upy * hr * 0.55)
        pygame.draw.circle(surf, hair, (int(chin[0]), int(chin[1])), int(hr * 0.55))
        pygame.draw.circle(surf, skin, (int(chin[0] + upx * hr * 0.3 + fx * 2), int(chin[1] + upy * hr * 0.3 + fy * 2)), int(hr * 0.35))
    # göz ve kaş
    eye = (hp[0] + fx * hr * 0.55 + upx * hr * 0.12, hp[1] + fy * hr * 0.55 + upy * hr * 0.12)
    pygame.draw.circle(surf, (255, 255, 255), (int(eye[0]), int(eye[1])), max(2, int(3.4 * s)))
    pygame.draw.circle(surf, (20, 20, 30), (int(eye[0] + fx * 1.4), int(eye[1] + fy * 1.4)), max(1, int(1.8 * s)))
    brow1 = (eye[0] - fx * 5 * s + upx * 5 * s, eye[1] - fy * 5 * s + upy * 6 * s)
    brow2 = (eye[0] + fx * 5 * s + upx * 3 * s, eye[1] + fy * 5 * s + upy * 3 * s)
    pygame.draw.line(surf, OUT, brow1, brow2, max(2, int(3 * s)))
    # alın bandı
    if pal.get("band"):
        b1 = (hp[0] + upx * hr * 0.42 - fx * hr, hp[1] + upy * hr * 0.42 - fy * hr)
        b2 = (hp[0] + upx * hr * 0.42 + fx * hr, hp[1] + upy * hr * 0.42 + fy * hr)
        pygame.draw.line(surf, OUT, b1, b2, int(9 * s))
        pygame.draw.line(surf, pal["band"], b1, b2, int(6 * s))
        sw = math.sin(t * 8) * 5 * s
        e1 = (b1[0] - fx * 16 * s, b1[1] - fy * 16 * s + 6 * s + sw)
        e2 = (b1[0] - fx * 26 * s, b1[1] - fy * 26 * s + 12 * s - sw)
        pygame.draw.line(surf, pal["band"], b1, e1, int(5 * s))
        pygame.draw.line(surf, pal["band"], b1, e2, int(4 * s))

    leg("f", False)
    arm("f", False)
    return J, oy


def hurt_rect(ch, pose, x, y, facing, grounded=True):
    body = Body(ch)
    J = body.joints(pose)
    oy = body.ground_offset(J) if grounded else -(body.L["th"] + body.L["sh"]) * 0.92
    pts = [J[k] for k in ("hip", "chest", "sho", "head", "knee_f", "knee_b", "foot_f", "foot_b")]
    xs = [x + p[0] * facing for p in pts]
    ys = [y + p[1] + oy for p in pts]
    pad = 16 * body.s
    left, right = min(xs) - pad, max(xs) + pad
    # gövde genişliğini sınırla (uzanan bacak hurtbox'ı çok büyütmesin)
    cx = x + J["chest"][0] * facing
    left = max(left, cx - 42 * body.s)
    right = min(right, cx + 42 * body.s)
    top = min(ys) - body.L["head"]
    bottom = max(ys) + 6
    return pygame.Rect(int(left), int(top), int(right - left), int(bottom - top))


def limb_point(ch, pose, x, y, facing, limb, grounded=True):
    body = Body(ch)
    J = body.joints(pose)
    oy = body.ground_offset(J) if grounded else -(body.L["th"] + body.L["sh"]) * 0.92
    p = J[limb]
    return (x + p[0] * facing, y + p[1] + oy)
