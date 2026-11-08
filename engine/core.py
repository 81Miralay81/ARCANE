"""Kanatix Arcade - ortak motor: pencere, sahne yönetimi, yazı tipleri, kayıt."""
import json
import math
import os
import sys

import pygame

VERSION = "1.3.4"
TITLE = "Kanatix Arcade"
W, H = 1280, 720
FPS = 60

# Renk paleti
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 200, 60)
RED = (230, 50, 60)
CYAN = (60, 220, 255)
MAGENTA = (255, 60, 200)
GREEN = (80, 240, 120)
DARK = (12, 10, 24)


def resource_path(*parts):
    """PyInstaller ile paketlenince de dosya yolunu doğru bulur."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


def data_dir():
    if os.environ.get("ANDROID_PRIVATE"):
        root = os.environ["ANDROID_PRIVATE"]
    elif os.name == "nt":
        root = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        root = os.path.join(os.path.expanduser("~"), ".local", "share")
    path = os.path.join(root, "KanatixArcade")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        import tempfile
        path = tempfile.gettempdir()
    return path


class Save:
    """Rekorlar ve ayarlar (APPDATA/KanatixArcade/kayit.json)."""

    def __init__(self):
        self.path = os.path.join(data_dir(), "kayit.json")
        self.data = {"scores": {}, "settings": {"volume": 0.7, "music": 0.5, "difficulty": 1, "fullscreen": False}}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.data["scores"].update(loaded.get("scores", {}))
            self.data["settings"].update(loaded.get("settings", {}))
        except Exception:
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def best(self, game):
        return self.data["scores"].get(game, 0)

    def submit(self, game, score):
        if score > self.best(game):
            self.data["scores"][game] = score
            self.save()
            return True
        return False

    @property
    def settings(self):
        return self.data["settings"]


_font_cache = {}


def font(size, bold=True):
    key = (size, bold)
    if key not in _font_cache:
        f = None
        try:
            f = pygame.font.Font(resource_path("assets", "fonts", "DejaVuSansCondensed-Bold.ttf"), int(size * 0.95))
        except Exception:
            f = None
        for name in (() if f else ("bahnschrift", "segoeuisemibold", "segoeui", "arialblack", "arial")):
            try:
                path = pygame.font.match_font(name, bold=bold)
                if path:
                    f = pygame.font.Font(path, size)
                    break
            except Exception:
                continue
        if f is None:
            f = pygame.font.Font(None, int(size * 1.35))
            f.set_bold(bold)
        _font_cache[key] = f
    return _font_cache[key]


# Her yazı tipinde bulunmayan semboller: bunları kendimiz çiziyoruz (Windows'ta kutu çıkmasın)
ICON_ANGLES = {"→": 0, "↘": 45, "↓": 90, "↙": 135, "←": 180, "↖": 225, "↑": 270, "↗": 315, "►": 0, "◄": 180}
ICONS = set(ICON_ANGLES) | {"↔", "♥"}


def _draw_icon(surf, ch, rect, color):
    cx, cy = rect.center
    s = rect.h * 0.36
    if ch == "♥":
        r = s * 0.55
        pygame.draw.circle(surf, color, (int(cx - r * 0.9), int(cy - r * 0.4)), int(r))
        pygame.draw.circle(surf, color, (int(cx + r * 0.9), int(cy - r * 0.4)), int(r))
        pygame.draw.polygon(surf, color, [(cx - r * 1.85, cy - r * 0.2), (cx + r * 1.85, cy - r * 0.2), (cx, cy + s * 0.95)])
        return
    if ch == "↔":
        for a in (0, 180):
            _draw_arrow(surf, cx + (s * 0.45 if a == 0 else -s * 0.45), cy, s * 0.75, a, color, shaft=False)
        pygame.draw.line(surf, color, (cx - s * 0.8, cy), (cx + s * 0.8, cy), max(2, int(s * 0.32)))
        return
    if ch in ("►", "◄"):
        a = math.radians(ICON_ANGLES[ch])
        pts = [(cx + math.cos(a) * s, cy), (cx - math.cos(a) * s * 0.7, cy - s * 0.85), (cx - math.cos(a) * s * 0.7, cy + s * 0.85)]
        pygame.draw.polygon(surf, color, pts)
        return
    _draw_arrow(surf, cx, cy, s, ICON_ANGLES[ch], color)


def _draw_arrow(surf, cx, cy, s, deg, color, shaft=True):
    a = math.radians(deg)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    tip = (cx + dx * s, cy + dy * s)
    back = (cx - dx * s, cy - dy * s)
    head = s * 0.75
    hb = (tip[0] - dx * head, tip[1] - dy * head)
    if shaft:
        pygame.draw.line(surf, color, back, hb, max(2, int(s * 0.34)))
    pygame.draw.polygon(surf, color, [tip, (hb[0] + nx * head * 0.75, hb[1] + ny * head * 0.75),
                                      (hb[0] - nx * head * 0.75, hb[1] - ny * head * 0.75)])


def render_rich(f, msg, color):
    """Yazıyı çizer; ok gibi sembolleri yazı tipinden değil, şekil olarak çizer."""
    msg = str(msg)
    if not any(c in ICONS for c in msg):
        return f.render(msg, True, color)
    h = f.get_height()
    icon_w = int(h * 0.85)
    parts = []
    buf = ""
    for c in msg:
        if c in ICONS:
            if buf:
                parts.append(("t", buf))
                buf = ""
            parts.append(("i", c))
        else:
            buf += c
    if buf:
        parts.append(("t", buf))
    imgs = [(k, f.render(v, True, color) if k == "t" else v) for k, v in parts]
    width = sum(img.get_width() if k == "t" else icon_w for k, img in imgs)
    out = pygame.Surface((max(1, width), h), pygame.SRCALPHA)
    x = 0
    for k, img in imgs:
        if k == "t":
            out.blit(img, (x, 0))
            x += img.get_width()
        else:
            _draw_icon(out, img, pygame.Rect(x, 0, icon_w, h), color)
            x += icon_w
    return out


def text(surf, msg, size, pos, color=WHITE, anchor="center", shadow=True, outline=0, ocolor=BLACK, alpha=255):
    f = font(size)
    img = render_rich(f, msg, color)
    rect = img.get_rect(**{anchor: pos})
    if outline:
        o = render_rich(f, msg, ocolor)
        for dx in range(-outline, outline + 1, max(1, outline)):
            for dy in range(-outline, outline + 1, max(1, outline)):
                if dx or dy:
                    surf.blit(o, rect.move(dx, dy))
    elif shadow:
        s = render_rich(f, msg, (0, 0, 0))
        s.set_alpha(min(160, alpha))
        surf.blit(s, rect.move(3, 3))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, rect)
    return rect


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def vgradient(w, h, top, bottom):
    s = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(s, lerp_color(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
    return s


def glow_circle(radius, color, intensity=1.0):
    """Toplama (additive) karışımla kullanılacak yumuşak ışık halesi."""
    size = radius * 2
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = max(6, radius // 2)
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        k = (1 - i / steps) ** 1.6 * intensity
        col = tuple(min(255, int(c * k)) for c in color)
        pygame.draw.circle(s, col + (255,), (radius, radius), r)
    return s


_glow_cache = {}


def blit_glow(surf, pos, radius, color, intensity=1.0):
    # renk ve yarıçapı kademelendir: önbellek tutsun, her karede yeniden üretilmesin (takılmayı önler)
    radius = max(4, (int(radius) + 3) // 4 * 4)
    color = tuple(min(255, (int(c * intensity) + 7) // 16 * 16) for c in color[:3])
    if not any(color):
        return
    key = (radius, color)
    g = _glow_cache.get(key)
    if g is None:
        if len(_glow_cache) > 900:
            _glow_cache.clear()
        g = glow_circle(radius, color, 1.0)
        _glow_cache[key] = g
    surf.blit(g, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_ADD)


_logo_cache = {}


def draw_kanatix_logo(surf, center, scale=1.0, t=0.0):
    """Kanatix ortak logosu (kanat işareti, assets/logo_mark.png)."""
    size = max(16, int(150 * scale))
    img = _logo_cache.get(size)
    if img is None:
        try:
            base = pygame.image.load(resource_path("assets", "logo_mark.png")).convert_alpha()
            img = pygame.transform.smoothscale(base, (size, size))
        except Exception:
            img = pygame.Surface((size, size), pygame.SRCALPHA)
        _logo_cache[size] = img
    blit_glow(surf, (int(center[0]), int(center[1])), int(size * 0.62), (70, 34, 20), 0.9)
    surf.blit(img, img.get_rect(center=(int(center[0]), int(center[1]))))


class Scene:
    def __init__(self, app):
        self.app = app

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    def on_enter(self):
        pass


class App:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption(f"{TITLE} v{VERSION}")
        try:
            icon = pygame.image.load(resource_path("assets", "icon.png"))
            pygame.display.set_icon(icon)
        except Exception:
            pass
        self.save = Save()
        from engine.touch import is_android
        flags = pygame.SCALED | (pygame.FULLSCREEN if is_android() else pygame.RESIZABLE)
        try:
            self.screen = pygame.display.set_mode((W, H), flags, vsync=1)
        except Exception:
            self.screen = pygame.display.set_mode((W, H), flags)
        if self.save.settings.get("fullscreen"):
            try:
                pygame.display.toggle_fullscreen()
            except Exception:
                pass
        self.clock = pygame.time.Clock()
        from engine.audio import Audio
        self.audio = Audio(self.save.settings)
        self.scenes = []
        self.running = True
        self.time = 0.0
        self.joysticks = []
        self.update_status = None
        from engine.touch import is_android
        self.android = is_android()
        st = self.save.settings
        self.touch_mode = st.get("touch", "auto") == "on" or (st.get("touch", "auto") == "auto" and self.android)
        self._init_joysticks()

    def _init_joysticks(self):
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            try:
                j = pygame.joystick.Joystick(i)
                j.init()
                self.joysticks.append(j)
            except Exception:
                pass

    def push(self, scene):
        self.scenes.append(scene)
        scene.on_enter()

    def pop(self):
        if self.scenes:
            self.scenes.pop()
        if self.scenes:
            self.scenes[-1].on_enter()
        else:
            self.running = False

    def replace(self, scene):
        if self.scenes:
            self.scenes.pop()
        self.push(scene)

    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            self.save.settings["fullscreen"] = not self.save.settings.get("fullscreen")
            self.save.save()
        except Exception:
            pass

    def run(self, first_scene):
        self.push(first_scene)
        while self.running and self.scenes:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 20)
            self.time += dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                    self._init_joysticks()
                elif self.scenes:
                    self.scenes[-1].handle(event)
            if not self.scenes:
                break
            scene = self.scenes[-1]
            scene.update(dt)
            if self.scenes and self.scenes[-1] is scene:
                scene.draw(self.screen)
                pygame.display.flip()
        self.save.save()
        pygame.quit()


def is_confirm(event):
    return (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)) or \
        (event.type == pygame.JOYBUTTONDOWN and event.button in (0, 7, 9))


def is_back(event):
    return (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_AC_BACK)) or \
        (event.type == pygame.JOYBUTTONDOWN and event.button in (1, 6, 8))


def nav_dir(event):
    """Menülerde yön: (dx, dy) ya da None."""
    if event.type == pygame.KEYDOWN:
        m = {pygame.K_UP: (0, -1), pygame.K_w: (0, -1), pygame.K_DOWN: (0, 1), pygame.K_s: (0, 1),
             pygame.K_LEFT: (-1, 0), pygame.K_a: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_d: (1, 0)}
        return m.get(event.key)
    if event.type == pygame.JOYHATMOTION and event.value != (0, 0):
        return (event.value[0], -event.value[1])
    return None


class Particles:
    """Basit, hızlı parçacık sistemi."""

    def __init__(self):
        self.items = []

    def emit(self, x, y, n, color, speed=4.0, life=30, size=4, gravity=0.15, spread=math.tau, angle=0.0, glow=False, drag=0.96):
        import random
        for _ in range(n):
            a = angle + (random.random() - 0.5) * spread
            sp = speed * (0.4 + random.random() * 0.8)
            self.items.append([x, y, math.cos(a) * sp, math.sin(a) * sp, life * (0.6 + random.random() * 0.5), life,
                               size * (0.6 + random.random() * 0.7), color, gravity, glow, drag])

    def update(self, k=1.0):
        alive = []
        for p in self.items:
            p[0] += p[2] * k
            p[1] += p[3] * k
            p[2] *= p[10]
            p[3] = p[3] * p[10] + p[8] * k
            p[4] -= k
            if p[4] > 0:
                alive.append(p)
        self.items = alive

    def draw(self, surf, ox=0, oy=0):
        for x, y, vx, vy, life, maxl, size, color, g, glow, drag in self.items:
            t = life / maxl
            r = max(1, int(size * t + 0.5))
            pos = (int(x - ox), int(y - oy))
            if glow:
                blit_glow(surf, pos, max(3, r * 3), tuple(int(c * t) for c in color), 1.0)
            pygame.draw.circle(surf, color, pos, r)
