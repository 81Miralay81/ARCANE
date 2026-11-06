"""Detaylı karakter çizimi.

Karakter 2 kat büyük çizilip yumuşatılarak küçültülür (kenar yumuşatma).
Her uzuv kas profiliyle, ışık-gölge ve parlama ile çizilir.
"""
import math

import pygame

from engine.core import shade
from games.fighter.skeleton import Body

SS = 2                       # süper örnekleme katsayısı
OUT = (14, 10, 18)
LIGHT = (-0.55, -0.83)       # ışık sol üstten gelir

# Uzuv kalınlık profilleri (baştan uca 7 örnek)
PROF = {
    "ua": [1.00, 1.10, 1.18, 1.12, 0.98, 0.88, 0.82],
    "fa": [0.86, 0.96, 1.00, 0.94, 0.84, 0.76, 0.70],
    "th_gi": [1.18, 1.20, 1.16, 1.10, 1.04, 0.98, 0.94],
    "sh_gi": [0.96, 0.98, 1.00, 1.03, 1.07, 1.12, 1.16],
    "th_tight": [1.12, 1.14, 1.08, 1.00, 0.94, 0.88, 0.82],
    "sh_tight": [0.84, 0.94, 1.00, 0.92, 0.80, 0.70, 0.64],
    "torso": [0.84, 0.78, 0.80, 0.90, 1.02, 1.12, 1.10],
}


def _mix(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def _norm(dx, dy):
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


def profile_poly(a, b, widths, extra=0.0):
    """a->b ekseni boyunca genişlik profiliyle çokgen (sol kenar, sağ kenar)."""
    dx, dy = _norm(b[0] - a[0], b[1] - a[1])
    nx, ny = -dy, dx
    n = len(widths)
    left, right = [], []
    for i, w in enumerate(widths):
        t = i / (n - 1)
        cx, cy = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        hw = w / 2 + extra
        left.append((cx + nx * hw, cy + ny * hw))
        right.append((cx - nx * hw, cy - ny * hw))
    return left, right, (nx, ny)


def limb(surf, a, b, base_w, prof, color, ow, muscle_line=False, dark=False):
    widths = [base_w * k for k in prof]
    L, R, (nx, ny) = profile_poly(a, b, widths, ow)
    pygame.draw.polygon(surf, OUT, L + R[::-1])
    pygame.draw.circle(surf, OUT, (int(a[0]), int(a[1])), int(widths[0] / 2 + ow))
    pygame.draw.circle(surf, OUT, (int(b[0]), int(b[1])), int(widths[-1] / 2 + ow))
    L, R, _ = profile_poly(a, b, widths)
    pygame.draw.polygon(surf, color, L + R[::-1])
    pygame.draw.circle(surf, color, (int(a[0]), int(a[1])), int(widths[0] / 2))
    pygame.draw.circle(surf, color, (int(b[0]), int(b[1])), int(widths[-1] / 2))
    # ışık hangi tarafta?
    lit_left = (nx * LIGHT[0] + ny * LIGHT[1]) > 0
    shadow_side = R if lit_left else L
    lit_side = L if lit_left else R
    centre = [((l[0] + r[0]) / 2, (l[1] + r[1]) / 2) for l, r in zip(L, R)]
    shadow_c = _mix(color, 0.72 if not dark else 0.8)
    mid = [(c[0] * 0.75 + s[0] * 0.25, c[1] * 0.75 + s[1] * 0.25) for c, s in zip(centre, shadow_side)]
    pygame.draw.polygon(surf, shadow_c, mid + shadow_side[::-1])
    if not dark:
        hl = [(c[0] * 0.45 + l[0] * 0.55, c[1] * 0.45 + l[1] * 0.55) for c, l in zip(centre, lit_side)]
        pygame.draw.lines(surf, _mix(color, 1.22), False, hl[1:-1], max(2, int(base_w * 0.14)))
    if muscle_line and not dark:
        # kas ayrım çizgisi
        m = [(c[0] * 0.6 + s[0] * 0.4, c[1] * 0.6 + s[1] * 0.4) for c, s in zip(centre, shadow_side)][1:5]
        pygame.draw.lines(surf, _mix(color, 0.62), False, m, max(1, int(base_w * 0.07)))
    return L, R


def fist(surf, el, hand, size, glove, facing, dark, wrap=None):
    dx, dy = _norm(hand[0] - el[0], hand[1] - el[1])
    nx, ny = -dy, dx
    L, W_ = size * 1.15, size * 1.0
    cx, cy = hand[0] + dx * size * 0.25, hand[1] + dy * size * 0.25
    pts = []
    for sx, sy in ((-0.5, -0.5), (0.5, -0.45), (0.55, 0.0), (0.5, 0.45), (-0.5, 0.5)):
        pts.append((cx + dx * L * sx + nx * W_ * sy, cy + dy * L * sx + ny * W_ * sy))
    o = [(cx + (p[0] - cx) * 1.0 + 0, p[1]) for p in pts]
    pygame.draw.polygon(surf, OUT, o, int(size * 0.5))
    pygame.draw.circle(surf, OUT, (int(cx + dx * L * 0.35), int(cy + dy * L * 0.35)), int(W_ * 0.55 + size * 0.12))
    g = _mix(glove, 0.8) if dark else glove
    pygame.draw.polygon(surf, g, pts)
    pygame.draw.circle(surf, g, (int(cx + dx * L * 0.35), int(cy + dy * L * 0.35)), int(W_ * 0.55))
    if not dark:
        # parmak eklemleri
        for k in (-0.3, 0.0, 0.3):
            p1 = (cx + dx * L * 0.42 + nx * W_ * k, cy + dy * L * 0.42 + ny * W_ * k)
            p2 = (cx + dx * L * 0.12 + nx * W_ * k, cy + dy * L * 0.12 + ny * W_ * k)
            pygame.draw.line(surf, _mix(g, 0.7), p1, p2, max(1, int(size * 0.09)))
        pygame.draw.circle(surf, _mix(g, 1.3), (int(cx - nx * W_ * 0.15 + LIGHT[0] * 3), int(cy - ny * W_ * 0.15 + LIGHT[1] * 3)),
                           max(2, int(size * 0.18)))
    if wrap:
        a = (hand[0] - dx * size * 0.35 + nx * W_ * 0.55, hand[1] - dy * size * 0.35 + ny * W_ * 0.55)
        b = (hand[0] - dx * size * 0.35 - nx * W_ * 0.55, hand[1] - dy * size * 0.35 - ny * W_ * 0.55)
        pygame.draw.line(surf, OUT, a, b, int(size * 0.5))
        pygame.draw.line(surf, _mix(wrap, 0.8 if dark else 1.0), a, b, int(size * 0.32))


def foot(surf, ankle, shin_angle, facing, s, color, dark, shoe=False):
    fa = math.radians(shin_angle - 90)
    fdx, fdy = math.sin(fa) * facing, math.cos(fa)          # ayak ucunun yönü
    ux, uy = -math.sin(math.radians(shin_angle)) * facing, -math.cos(math.radians(shin_angle))  # baldıra doğru
    heel = (ankle[0] - fdx * 6 * s - ux * 6 * s, ankle[1] - fdy * 6 * s - uy * 6 * s)
    toe = (ankle[0] + fdx * 22 * s - ux * 5 * s, ankle[1] + fdy * 22 * s - uy * 5 * s)
    top_ = (ankle[0] + fdx * 12 * s + ux * 3 * s, ankle[1] + fdy * 12 * s + uy * 3 * s)
    back = (ankle[0] - fdx * 5 * s + ux * 5 * s, ankle[1] - fdy * 5 * s + uy * 5 * s)
    pts = [back, top_, (toe[0] + ux * 3 * s, toe[1] + uy * 3 * s), toe, heel]
    pygame.draw.polygon(surf, OUT, pts, int(5 * s))
    pygame.draw.polygon(surf, color, pts)
    if shoe and not dark:
        sole = [(heel[0], heel[1]), (toe[0], toe[1])]
        pygame.draw.line(surf, (235, 235, 240), sole[0], sole[1], max(2, int(3 * s)))
        pygame.draw.line(surf, _mix(color, 1.25), back, top_, max(2, int(2.5 * s)))
    elif not dark:
        pygame.draw.line(surf, _mix(color, 0.8), heel, toe, max(1, int(2 * s)))


def draw_head(surf, ch, pal, J, T, pose, facing, s, t, skin, hair, flash):
    hp = T(J["head"])
    r = Body(ch).L["head"] * (1.0 if ch["hair_style"] != "bald" else 1.04)
    ha = math.radians(pose["torso"] + pose["head"])
    ux, uy = math.sin(ha) * facing, -math.cos(ha)        # yukarı
    fx, fy = math.cos(ha) * facing, math.sin(ha)         # ileri (yüz yönü)

    def P(f, u):
        return (hp[0] + fx * r * f + ux * r * u, hp[1] + fy * r * f + uy * r * u)

    style = ch.get("hair_style")
    # boyun
    sho, nk = T(J["sho"]), T(J["neck"])
    nw = 15 * s * ch.get("bulk", 1.0)
    limb(surf, sho, P(-0.1, -0.6), nw, [1.15, 1.05, 1.0, 0.95, 0.95, 0.95, 0.95], _mix(skin, 0.86), 2.5 * s)
    # at kuyruğu kafanın arkasında
    if style == "ponytail":
        sw = math.sin(t * 7) * 0.25
        base = P(-0.85, 0.45)
        p1 = (base[0] - fx * 18 * s + 0, base[1] - fy * 18 * s + 8 * s)
        p2 = (p1[0] - fx * 14 * s + math.sin(t * 7) * 5 * s, p1[1] + 18 * s)
        p3 = (p2[0] - fx * 6 * s + math.sin(t * 7 + 1) * 7 * s, p2[1] + 18 * s)
        limb(surf, base, p1, 15 * s, [1, 1.05, 1.0, 0.95, 0.9, 0.85, 0.8], hair, 2.5 * s)
        limb(surf, p1, p2, 12 * s, [1, 0.98, 0.95, 0.9, 0.85, 0.75, 0.7], hair, 2.5 * s)
        limb(surf, p2, p3, 9 * s, [1, 0.9, 0.8, 0.7, 0.55, 0.4, 0.25], hair, 2.5 * s)
        del sw
    # kafatası + çene silueti
    jaw = [P(0.62, -0.25), P(0.55, -0.75), P(0.15, -1.02), P(-0.35, -0.82), P(-0.8, -0.2)]
    pygame.draw.circle(surf, OUT, (int(hp[0]), int(hp[1])), int(r + 2.5 * s))
    pygame.draw.polygon(surf, OUT, jaw, int(5 * s))
    pygame.draw.circle(surf, skin, (int(hp[0]), int(hp[1])), int(r))
    pygame.draw.polygon(surf, skin, jaw)
    # yüz gölgesi: ışık sol üstten, sağ alt taraf gölgede
    cres = []
    for i in range(13):
        a = math.radians(-60 + i * 15)
        cres.append((hp[0] + math.cos(a) * r, hp[1] + math.sin(a) * r))
    for i in range(12, -1, -1):
        a = math.radians(-60 + i * 15)
        cres.append((hp[0] - r * 0.28 + math.cos(a) * r * 0.92, hp[1] - r * 0.12 + math.sin(a) * r * 0.92))
    pygame.draw.polygon(surf, _mix(skin, 0.84), cres)
    # kulak
    ear = P(-0.3, 0.0)
    er_ = pygame.Rect(0, 0, int(r * 0.34), int(r * 0.48))
    er_.center = (int(ear[0]), int(ear[1]))
    pygame.draw.ellipse(surf, _mix(skin, 0.6), er_.inflate(int(3 * s), int(3 * s)))
    pygame.draw.ellipse(surf, _mix(skin, 0.92), er_)
    pygame.draw.arc(surf, _mix(skin, 0.72), er_.inflate(-int(r * 0.12), -int(r * 0.16)), 1.0, 4.4, max(1, int(1.5 * s)))
    # burun
    nose = [P(0.9, 0.02), P(1.06, -0.26), P(0.88, -0.3)]
    pygame.draw.polygon(surf, skin, nose)
    pygame.draw.lines(surf, _mix(skin, 0.55), False, nose, max(1, int(1.6 * s)))
    # ağız
    m1, m2 = P(0.78, -0.55), P(0.52, -0.58)
    pygame.draw.line(surf, _mix(skin, 0.5), m1, m2, max(1, int(2.2 * s)))
    # göz
    eye = P(0.6, 0.12)
    ew, eh = r * 0.3, r * 0.17
    er = pygame.Rect(0, 0, int(ew), int(eh))
    er.center = (int(eye[0]), int(eye[1]))
    pygame.draw.ellipse(surf, (245, 245, 245), er)
    iris = (int(eye[0] + fx * ew * 0.22), int(eye[1] + fy * ew * 0.22))
    pygame.draw.circle(surf, pal.get("eye", (60, 40, 30)), iris, max(2, int(eh * 0.5)))
    pygame.draw.circle(surf, (10, 8, 12), iris, max(1, int(eh * 0.25)))
    pygame.draw.line(surf, OUT, P(0.42, 0.24), P(0.8, 0.2), max(2, int(2.5 * s)))
    # öfkeli kaş
    b1, b2 = P(0.4, 0.4), P(0.85, 0.3)
    pygame.draw.line(surf, hair if style != "bald" else _mix(skin, 0.45), b1, b2, max(2, int(3.5 * s)))

    # saç
    if style == "short":
        spikes = []
        for i in range(8):
            a0 = math.radians(60 + i * 19)        # alından enseye
            base1 = (math.cos(a0 - 0.22), math.sin(a0 - 0.22))
            base2 = (math.cos(a0 + 0.22), math.sin(a0 + 0.22))
            # yay: f ekseninden u eksenine
            def arc(v, k):
                return P(v[0] * k * 0.95 + (-0.1), v[1] * k * 0.95 + 0.15)
            tip_k = 1.55 + (0.2 if i % 2 else 0)
            tipv = (math.cos(a0 + 0.35), math.sin(a0 + 0.35))
            spikes.append([arc(base1, 0.75), arc(tipv, tip_k), arc(base2, 0.75)])
        # temel saç kütlesi
        cap = [P(0.62, 0.72), P(0.4, 1.08), P(-0.1, 1.2), P(-0.75, 0.9), P(-1.05, 0.25), P(-0.95, -0.25),
               P(-0.55, 0.15), P(0.15, 0.62)]
        for sp in spikes:
            pygame.draw.polygon(surf, OUT, sp, int(6 * s))
        pygame.draw.polygon(surf, OUT, cap, int(6 * s))
        for sp in spikes:
            pygame.draw.polygon(surf, hair, sp)
        pygame.draw.polygon(surf, hair, cap)
        pygame.draw.lines(surf, _mix(hair, 1.6), False, [P(0.4, 0.85), P(-0.05, 1.0), P(-0.5, 0.85)], max(2, int(3 * s)))
        # favori
        pygame.draw.polygon(surf, hair, [P(-0.02, 0.45), P(0.14, 0.45), P(0.06, -0.15), P(-0.05, -0.12)])
    elif style == "ponytail":
        cap = [P(0.9, 0.35), P(0.6, 0.95), P(0.0, 1.15), P(-0.7, 0.9), P(-1.05, 0.3), P(-0.95, -0.2),
               P(-0.4, 0.15), P(0.25, 0.42)]
        pygame.draw.polygon(surf, OUT, cap, int(6 * s))
        pygame.draw.polygon(surf, hair, cap)
        # perçem
        bang = [P(0.95, 0.4), P(0.85, -0.05), P(0.6, 0.35), P(0.45, 0.1), P(0.35, 0.55)]
        pygame.draw.polygon(surf, hair, bang)
        pygame.draw.lines(surf, _mix(hair, 2.2), False, [P(0.55, 0.85), P(0.0, 1.0), P(-0.55, 0.8)], max(2, int(3 * s)))
        clip = P(-0.85, 0.45)
        pygame.draw.circle(surf, OUT, (int(clip[0]), int(clip[1])), int(5.5 * s))
        pygame.draw.circle(surf, pal["accent"], (int(clip[0]), int(clip[1])), int(4 * s))
    elif style == "bald":
        pygame.draw.ellipse(surf, _mix(skin, 1.22), pygame.Rect(0, 0, int(r * 0.7), int(r * 0.4)).move(
            int(P(-0.15, 0.62)[0] - r * 0.35), int(P(-0.15, 0.62)[1] - r * 0.2)))
        beard = [P(0.72, -0.35), P(0.65, -0.95), P(0.25, -1.3), P(-0.25, -1.05), P(-0.55, -0.4), P(-0.3, -0.2),
                 P(0.15, -0.5), P(0.45, -0.38)]
        pygame.draw.polygon(surf, OUT, beard, int(5 * s))
        pygame.draw.polygon(surf, hair, beard)
        mus = [P(0.95, -0.38), P(0.55, -0.32), P(0.3, -0.55), P(0.6, -0.55)]
        pygame.draw.polygon(surf, hair, mus)
        pygame.draw.lines(surf, _mix(hair, 1.8), False, [P(0.4, -0.8), P(0.15, -1.05)], max(1, int(2 * s)))
    # alın bandı
    if pal.get("band"):
        b1, b2 = P(-0.95, 0.5), P(0.95, 0.42)
        bw = int(8 * s)
        pygame.draw.line(surf, OUT, b1, b2, bw + int(4 * s))
        pygame.draw.line(surf, pal["band"], b1, b2, bw)
        pygame.draw.line(surf, _mix(pal["band"], 1.3), P(-0.6, 0.56), P(0.8, 0.5), max(1, int(2 * s)))
        knot = P(-0.98, 0.45)
        for k, ph in ((1.0, 0.0), (0.8, 1.3)):
            e1 = (knot[0] - fx * 14 * s, knot[1] + 4 * s + math.sin(t * 9 + ph) * 4 * s)
            e2 = (knot[0] - fx * 30 * s * k, knot[1] + 10 * s + math.sin(t * 9 + ph + 1) * 7 * s)
            pygame.draw.lines(surf, OUT, False, [knot, e1, e2], int(8 * s))
            pygame.draw.lines(surf, pal["band"], False, [knot, e1, e2], int(5 * s))


def _draw(surf, ch, pose, x, y, facing, grounded, flash, tint, t, pal):
    body = Body(ch)
    J = body.joints(pose)
    oy = body.ground_offset(J) if grounded else -(body.L["th"] + body.L["sh"]) * 0.92
    s = body.s
    bulk = ch.get("bulk", 1.0)
    ow = 2.6 * s

    def T(p):
        return (x + p[0] * facing, y + p[1] + oy)

    _hip0, _sho0 = T(J["hip"]), T(J["sho"])
    _d0 = _norm(_sho0[0] - _hip0[0], _sho0[1] - _hip0[1])
    NF = (-_d0[1], _d0[0]) if facing > 0 else (_d0[1], -_d0[0])
    TW = 44 * s * bulk

    cols = dict(skin=pal["skin"], top=pal["top"], pants=pal["pants"], glove=pal["glove"], belt=pal["belt"],
                hair=pal["hair"], accent=pal["accent"], shoe=pal.get("shoe"), wrap=pal.get("wrap"), band=pal.get("band"))
    if flash:
        cols = {k: ((255, 255, 255) if v else v) for k, v in cols.items()}
    elif tint:
        cols = {k: (tuple(min(255, int(v[i] * 0.7 + tint[i] * 0.3)) for i in range(3)) if v else v) for k, v in cols.items()}
    pal2 = dict(pal)
    pal2.update({k: v for k, v in cols.items() if v})
    skin, top, pants = cols["skin"], cols["top"], cols["pants"]
    tight = ch.get("tight_pants", False)
    sleeve = ch.get("sleeve")      # "gi" kolsuz yırtık / None

    def leg(side, dark):
        hip, kn, ft = T(J["hip"]), T(J["knee_" + side]), T(J["foot_" + side])
        c = _mix(pants, 0.8) if dark else pants
        lw = 24 * s * bulk
        limb(surf, hip, kn, lw, PROF["th_tight" if tight else "th_gi"], c, ow, muscle_line=tight, dark=dark)
        limb(surf, kn, ft, lw * 0.82, PROF["sh_tight" if tight else "sh_gi"], c, ow, muscle_line=tight, dark=dark)
        if not tight and not dark:
            # kumaş kırışıkları
            for k in (0.3, 0.55):
                p = (kn[0] + (ft[0] - kn[0]) * k, kn[1] + (ft[1] - kn[1]) * k)
                pygame.draw.arc(surf, _mix(c, 0.7), pygame.Rect(p[0] - 6 * s, p[1] - 4 * s, 12 * s, 8 * s), 3.5, 5.8,
                                max(1, int(2 * s)))
        fc = cols["shoe"] or skin
        foot(surf, ft, J["ang_shin_" + side], facing, s, _mix(fc, 0.82) if dark else fc, dark, shoe=bool(cols["shoe"]))
        if cols["wrap"] and not cols["shoe"]:
            pass
        if not tight and not cols["shoe"]:
            # paça
            d = _norm(ft[0] - kn[0], ft[1] - kn[1])
            n = (-d[1], d[0])
            cw = lw * 0.82 * 1.2 / 2
            a = (ft[0] - d[0] * 5 * s + n[0] * cw, ft[1] - d[1] * 5 * s + n[1] * cw)
            b = (ft[0] - d[0] * 5 * s - n[0] * cw, ft[1] - d[1] * 5 * s - n[1] * cw)
            pygame.draw.line(surf, OUT, a, b, int(6 * s))
            pygame.draw.line(surf, _mix(c, 0.85), a, b, int(3 * s))

    def arm(side, dark):
        sh0, el, hd = T(J["sho"]), T(J["el_" + side]), T(J["hand_" + side])
        k_off = 0.16 if side == "f" else -0.12
        hp0 = T(J["hip"])
        sh = (sh0[0] + (hp0[0] - sh0[0]) * 0.14 + NF[0] * TW * k_off, sh0[1] + (hp0[1] - sh0[1]) * 0.14 + NF[1] * TW * k_off)
        sk = _mix(skin, 0.82) if dark else skin
        aw = 15.5 * s * bulk
        limb(surf, sh, el, aw, PROF["ua"], sk, ow, muscle_line=True, dark=dark)
        limb(surf, el, hd, aw, PROF["fa"], sk, ow, muscle_line=False, dark=dark)
        # omuz (deltoid)
        dr = int(aw * 0.62)
        pygame.draw.circle(surf, OUT, (int(sh[0]), int(sh[1])), dr + int(ow))
        pygame.draw.circle(surf, sk, (int(sh[0]), int(sh[1])), dr)
        if not dark:
            pygame.draw.circle(surf, _mix(sk, 1.15), (int(sh[0] + LIGHT[0] * dr * 0.35), int(sh[1] + LIGHT[1] * dr * 0.35)),
                               max(2, dr // 3))
        if sleeve == "gi":
            c = _mix(top, 0.8) if dark else top
            e = (sh[0] + (el[0] - sh[0]) * 0.42, sh[1] + (el[1] - sh[1]) * 0.42)
            limb(surf, sh, e, aw * 1.45, [1.0, 1.02, 1.04, 1.06, 1.08, 1.1, 1.12], c, ow, dark=dark)
            d = _norm(el[0] - sh[0], el[1] - sh[1])
            n = (-d[1], d[0])
            hw = aw * 1.45 * 1.12 / 2
            for k in (-0.7, 0.0, 0.7):
                p0 = (e[0] + n[0] * hw * k, e[1] + n[1] * hw * k)
                tri = [(p0[0] + n[0] * hw * 0.35, p0[1] + n[1] * hw * 0.35), (p0[0] - n[0] * hw * 0.35, p0[1] - n[1] * hw * 0.35),
                       (p0[0] + d[0] * 6 * s, p0[1] + d[1] * 6 * s)]
                pygame.draw.polygon(surf, c, tri)
        elif sleeve == "tank" and not dark:
            pygame.draw.line(surf, OUT, (sh[0] - 6 * s, sh[1] - 4 * s), (sh[0] + 6 * s, sh[1] - 6 * s), int(7 * s))
            pygame.draw.line(surf, top, (sh[0] - 6 * s, sh[1] - 4 * s), (sh[0] + 6 * s, sh[1] - 6 * s), int(4 * s))
        if ch.get("armband") and not dark:
            a = (el[0] + (hd[0] - el[0]) * 0.55, el[1] + (hd[1] - el[1]) * 0.55)
            d = _norm(hd[0] - el[0], hd[1] - el[1])
            n = (-d[1], d[0])
            w = aw * 0.55
            pygame.draw.line(surf, OUT, (a[0] + n[0] * w, a[1] + n[1] * w), (a[0] - n[0] * w, a[1] - n[1] * w), int(8 * s))
            pygame.draw.line(surf, cols["accent"], (a[0] + n[0] * w, a[1] + n[1] * w), (a[0] - n[0] * w, a[1] - n[1] * w), int(5 * s))
        fist(surf, el, hd, 15 * s * bulk, cols["glove"], facing, dark, cols["wrap"] if ch.get("hand_wrap") else None)

    # --- arka uzuvlar
    leg("b", True)
    arm("b", True)

    # --- gövde
    hip, sho = T(J["hip"]), T(J["sho"])
    tw = 44 * s * bulk
    bare = ch.get("bare_chest", False)
    tc = skin if bare else top
    d = _norm(sho[0] - hip[0], sho[1] - hip[1])
    L, R = limb(surf, (hip[0] + d[0] * 8 * s, hip[1] + d[1] * 8 * s), sho, tw, PROF["torso"], tc, ow, muscle_line=False)
    nf = NF

    def along(k, side):
        cx = hip[0] + (sho[0] - hip[0]) * k
        cy = hip[1] + (sho[1] - hip[1]) * k
        return (cx + nf[0] * side * tw * 0.5, cy + nf[1] * side * tw * 0.5)

    if bare:
        # göğüs kası ve karın
        pec = [along(0.62, 0.95), along(0.78, 0.9), along(0.92, 0.35), along(0.66, 0.1)]
        pygame.draw.lines(surf, _mix(skin, 0.68), False, pec, max(2, int(3 * s)))
        for k in (0.3, 0.42, 0.54):
            pygame.draw.line(surf, _mix(skin, 0.75), along(k, 0.15), along(k, 0.65), max(1, int(2.2 * s)))
        pygame.draw.line(surf, _mix(skin, 0.75), along(0.24, 0.42), along(0.6, 0.42), max(1, int(2.2 * s)))
        pygame.draw.circle(surf, _mix(skin, 0.6), (int(along(0.7, 0.72)[0]), int(along(0.7, 0.72)[1])), max(2, int(2.2 * s)))
        if ch.get("strap"):
            pygame.draw.line(surf, OUT, along(1.0, 0.8), along(0.25, -0.9), int(9 * s))
            pygame.draw.line(surf, cols["accent"], along(1.0, 0.8), along(0.25, -0.9), int(6 * s))
    else:
        # gi yakası (V) ve kruvaze
        neck = T(J["neck"])
        v = along(0.5, 0.25)
        pygame.draw.polygon(surf, skin, [along(0.98, 0.75), along(0.98, -0.2), v])
        pygame.draw.lines(surf, _mix(skin, 0.75), False, [along(0.9, 0.55), along(0.72, 0.38)], max(1, int(2 * s)))
        lap_c = _mix(top, 0.62) if not ch.get("tank") else cols["accent"]
        pygame.draw.line(surf, OUT, along(1.0, 0.8), v, int(7 * s))
        pygame.draw.line(surf, lap_c, along(1.0, 0.8), v, int(4 * s))
        pygame.draw.line(surf, OUT, along(1.0, -0.25), v, int(7 * s))
        pygame.draw.line(surf, lap_c, along(1.0, -0.25), v, int(4 * s))
        if not ch.get("tank"):
            pygame.draw.line(surf, _mix(top, 0.62), v, along(0.12, -0.8), max(2, int(3 * s)))
            for k in (0.35, 0.6):
                pygame.draw.arc(surf, _mix(top, 0.72),
                                pygame.Rect(along(k, -0.3)[0] - 8 * s, along(k, -0.3)[1] - 5 * s, 16 * s, 10 * s), 3.6, 5.6,
                                max(1, int(2 * s)))
        del neck
    # kalça bloğu
    hw = 10 * s * bulk
    hc = (hip[0] + d[0] * 4 * s, hip[1] + d[1] * 4 * s)
    pa, pb = (hc[0] - nf[0] * hw, hc[1] - nf[1] * hw), (hc[0] + nf[0] * hw, hc[1] + nf[1] * hw)
    rr = 15 * s * bulk
    for p_ in (pa, pb):
        pygame.draw.circle(surf, OUT, (int(p_[0]), int(p_[1])), int(rr + ow))
    pygame.draw.line(surf, OUT, pa, pb, int(rr * 2 + ow * 2))
    pygame.draw.line(surf, pants, pa, pb, int(rr * 2))
    for p_ in (pa, pb):
        pygame.draw.circle(surf, pants, (int(p_[0]), int(p_[1])), int(rr))
    pygame.draw.circle(surf, _mix(pants, 0.78), (int(pa[0] + 3 * s), int(pa[1] + 5 * s)), int(rr * 0.7))
    # kemer
    bpos = (hip[0] + d[0] * 9 * s, hip[1] + d[1] * 9 * s)
    bw = tw * 0.48
    b1 = (bpos[0] - nf[0] * bw, bpos[1] - nf[1] * bw)
    b2 = (bpos[0] + nf[0] * bw, bpos[1] + nf[1] * bw)
    if ch.get("champ_belt"):
        pygame.draw.line(surf, OUT, b1, b2, int(17 * s))
        pygame.draw.line(surf, _mix(cols["belt"], 0.7), b1, b2, int(13 * s))
        plate = along(0.14, 0.45)
        pygame.draw.circle(surf, OUT, (int(plate[0]), int(plate[1])), int(11 * s))
        pygame.draw.circle(surf, cols["belt"], (int(plate[0]), int(plate[1])), int(9 * s))
        pygame.draw.circle(surf, _mix(cols["belt"], 1.25), (int(plate[0] - 2 * s), int(plate[1] - 2 * s)), int(3.5 * s))
    else:
        pygame.draw.line(surf, OUT, b1, b2, int(12 * s))
        pygame.draw.line(surf, cols["belt"], b1, b2, int(8 * s))
        knot = (bpos[0] + nf[0] * bw * 0.3, bpos[1] + nf[1] * bw * 0.3)
        sway = math.sin(t * 6) * 3 * s
        for k in (-1, 1):
            e = (knot[0] + k * 5 * s * facing + sway, knot[1] + 20 * s)
            pygame.draw.line(surf, OUT, knot, e, int(9 * s))
            pygame.draw.line(surf, cols["belt"], knot, e, int(5 * s))
        pygame.draw.circle(surf, OUT, (int(knot[0]), int(knot[1])), int(6 * s))
        pygame.draw.circle(surf, cols["belt"], (int(knot[0]), int(knot[1])), int(4.5 * s))

    draw_head(surf, ch, pal2, J, T, pose, facing, s, t, skin, cols["hair"], flash)

    # --- ön uzuvlar
    leg("f", False)
    arm("f", False)
    return J, oy


_buf_cache = {}


def draw_fighter_hd(surf, ch, pose, x, y, facing, grounded=True, flash=0, alpha_tint=None, t=0.0, palette=None, ss=SS):
    pal = palette or ch["palette"]
    sc = ch["scale"]
    left, up, down = int(250 * sc), int(340 * sc), int(70 * sc)
    w, h = left * 2, up + down
    key = (w * ss, h * ss)
    buf = _buf_cache.get(key)
    if buf is None:
        if len(_buf_cache) > 8:
            _buf_cache.clear()
        buf = pygame.Surface(key, pygame.SRCALPHA)
        _buf_cache[key] = buf
    buf.fill((0, 0, 0, 0))
    big = dict(ch, scale=sc * ss)
    _draw(buf, big, pose, left * ss, up * ss, facing, grounded, flash, alpha_tint, t, pal)
    img = pygame.transform.smoothscale(buf, (w, h)) if ss != 1 else buf
    surf.blit(img, (int(x) - left, int(y) - up))
