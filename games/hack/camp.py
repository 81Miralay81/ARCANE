"""Gölge Seferi: kahraman seçimi ve kamp (yetenek / geliştirme / bölüm seçimi)."""
import pygame

from engine.core import GOLD, WHITE, W, H, Scene, blit_glow, is_back, is_confirm, nav_dir, shade, text, vgradient
from games.fighter import sprites
from games.hack import data as D


def profiles(app):
    hp = app.save.data.setdefault("hack", {})
    for hid in D.HERO_ORDER:
        if hid not in hp:
            hp[hid] = D.new_profile()
        p = hp[hid]
        for k, v in D.new_profile().items():
            p.setdefault(k, v)
    return hp


class HackSelect(Scene):
    """Kahraman seçimi."""

    def __init__(self, app):
        super().__init__(app)
        self.i = 0
        self.t = 0.0
        self.bg = vgradient(W, H, (14, 6, 28), (50, 8, 30))

    def on_enter(self):
        self.app.audio.play_music("menu")

    def rects(self):
        return [pygame.Rect(70 + k * 290, 150, 270, 470) for k in range(4)]

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if e.pos[0] < 160 and e.pos[1] < 90:
                self.app.pop()
                return
            for k, r in enumerate(self.rects()):
                if r.collidepoint(e.pos):
                    if k == self.i:
                        self.choose()
                    else:
                        self.i = k
                        self.app.audio.play("menu")
            return
        if is_back(e):
            self.app.pop()
            return
        d = nav_dir(e)
        if d and d[0]:
            self.i = (self.i + d[0]) % 4
            self.app.audio.play("menu")
        elif is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_k, pygame.K_j)):
            self.choose()

    def choose(self):
        self.app.audio.play("select")
        hid = D.HERO_ORDER[self.i]
        self.app.push(Camp(self.app, hid))

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        for i in range(-4, 20):
            x = i * 90 + (self.t * 30) % 90
            pygame.draw.line(s, (36, 14, 50), (x, 0), (x - 300, H), 16)
        text(s, "GÖLGE SEFERİ", 58, (W // 2, 52), GOLD, outline=4)
        text(s, "Kahramanını seç", 22, (W // 2, 102), (200, 190, 230))
        pygame.draw.rect(s, (40, 24, 60), (20, 20, 120, 46), border_radius=12)
        text(s, "◄ GERİ", 22, (80, 43), WHITE)
        profs = profiles(self.app)
        for k, (hid, r) in enumerate(zip(D.HERO_ORDER, self.rects())):
            hd = D.HEROES[hid]
            sel = k == self.i
            pygame.draw.rect(s, (34, 18, 52) if not sel else (56, 26, 84), r, border_radius=18)
            if sel:
                blit_glow(s, (r.centerx, r.centery - 40), 200, shade(hd["color"], 0.35))
            clip = s.get_clip()
            s.set_clip(r)
            anim = "Idle" if not sel else "Idle"
            sprites.draw_static(s, hid, anim, int(self.t * 10), r.centerx, r.bottom - 120, 1, 0.95 if sel else 0.85,
                                dark=not sel)
            s.set_clip(clip)
            pygame.draw.rect(s, hd["color"] if sel else (70, 50, 90), r, 3, border_radius=18)
            band = pygame.Surface((r.w, 130), pygame.SRCALPHA)
            band.fill((10, 4, 20, 210))
            s.blit(band, (r.x, r.bottom - 130))
            text(s, hd["name"], 30, (r.centerx, r.bottom - 108), WHITE, outline=2)
            text(s, hd["title"], 18, (r.centerx, r.bottom - 80), shade(hd["color"], 1.2))
            p = profs[hid]
            text(s, f"Seviye {p['level']}   •   {p['gold']} altın", 17, (r.centerx, r.bottom - 52), GOLD)
            done = len(p["cleared"])
            text(s, f"Bölüm {done}/{len(D.CHAPTERS)}" + ("  •  KABUS" if p.get("nightmare") else ""), 16,
                 (r.centerx, r.bottom - 28), (190, 180, 220))
        hd = D.HEROES[D.HERO_ORDER[self.i]]
        text(s, hd["desc"], 20, (W // 2, H - 60), WHITE)
        text(s, "← → seç   •   ENTER / dokun: devam", 17, (W // 2, H - 28), (170, 160, 200))


class Camp(Scene):
    """Kamp: yetenek geliştirme, altınla güçlenme, bölüm seçimi."""

    TABS = ["SAVAŞ", "YETENEKLER", "GELİŞTİRMELER"]

    def __init__(self, app, hid):
        super().__init__(app)
        self.hid = hid
        self.hd = D.HEROES[hid]
        self.tab = 0
        self.i = 0
        self.t = 0.0
        self.msg = ("", 0.0)
        self.bg = vgradient(W, H, (10, 6, 24), (40, 14, 30))

    @property
    def p(self):
        return profiles(self.app)[self.hid]

    def on_enter(self):
        self.app.audio.play_music("menu")
        self.app.save.save()

    def items(self):
        if self.tab == 0:
            n = min(self.p["chapter"], len(D.CHAPTERS))
            rows = list(range(n))
            if len(self.p["cleared"]) >= len(D.CHAPTERS):
                rows.append("nightmare")
            return rows
        if self.tab == 1:
            return [0, 1, 2, 3]
        return [u[0] for u in D.UPGRADES]

    def flash(self, m):
        self.msg = (m, 2.0)

    def activate(self):
        p = self.p
        items = self.items()
        if not items:
            return
        it = items[self.i % len(items)]
        if self.tab == 0:
            if it == "nightmare":
                p["nightmare"] = not p.get("nightmare")
                self.app.audio.play("select")
                self.app.save.save()
                return
            from games.hack.level import HackLevel
            self.app.audio.play("select")
            self.app.save.save()
            self.app.push(HackLevel(self.app, self.hid, p, it))
        elif self.tab == 1:
            sk = self.hd["skills"][it]
            lv = p["skills"][it]
            if lv == 0:
                self.flash(f"{sk['name']} seviye {sk['unlock']}'de açılır")
                self.app.audio.play("back")
            elif lv >= 5:
                self.flash("Bu yetenek en yüksek seviyede")
            elif p["skill_pts"] <= 0:
                self.flash("Yetenek puanın yok — seviye atlayınca kazanırsın")
                self.app.audio.play("back")
            else:
                p["skills"][it] += 1
                p["skill_pts"] -= 1
                self.app.audio.play("powerup")
                self.flash(f"{sk['name']} seviye {lv + 1}!")
        else:
            key = it
            if key == "potion":
                price = 40
                if p["potions"] >= 5:
                    self.flash("En fazla 5 iksir taşıyabilirsin")
                    return
                if p["gold"] < price:
                    self.flash("Yeterli altın yok")
                    self.app.audio.play("back")
                    return
                p["gold"] -= price
                p["potions"] += 1
                self.app.audio.play("coin")
                return
            lv = p["up"][key]
            mx = next(u[4] for u in D.UPGRADES if u[0] == key)
            price = D.upgrade_price(key, lv)
            if lv >= mx:
                self.flash("En yüksek seviyede")
            elif p["gold"] < price:
                self.flash("Yeterli altın yok")
                self.app.audio.play("back")
            else:
                p["gold"] -= price
                p["up"][key] += 1
                self.app.audio.play("powerup")
        self.app.save.save()

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            x, y = e.pos
            if x < 160 and y < 90:
                self.app.pop()
                return
            for k in range(3):
                if pygame.Rect(470 + k * 260, 24, 240, 50).collidepoint(e.pos):
                    self.tab, self.i = k, 0
                    self.app.audio.play("menu")
                    return
            for k in range(len(self.items())):
                if self.row_rect(k).collidepoint(e.pos):
                    self.i = k
                    self.activate()
                    return
            return
        if is_back(e):
            self.app.pop()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
            self.tab = (self.tab + 1) % 3
            self.i = 0
            return
        d = nav_dir(e)
        if d:
            if d[0]:
                self.tab = (self.tab + d[0]) % 3
                self.i = 0
            else:
                n = max(1, len(self.items()))
                self.i = (self.i + d[1]) % n
            self.app.audio.play("menu")
        elif is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_k, pygame.K_j)):
            self.activate()

    def update(self, dt):
        self.t += dt
        if self.msg[1] > 0:
            self.msg = (self.msg[0], self.msg[1] - dt)

    def row_rect(self, k):
        return pygame.Rect(470, 110 + k * 92, 760, 80)

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        p = self.p
        hd = self.hd
        # sol: kahraman
        blit_glow(s, (230, 420), 260, shade(hd["color"], 0.3))
        pygame.draw.ellipse(s, (8, 4, 16), (110, 600, 240, 34))
        sprites.draw_static(s, self.hid, "Idle", int(self.t * 10), 230, 615, 1, 1.25)
        pygame.draw.rect(s, (40, 24, 60), (20, 20, 120, 46), border_radius=12)
        text(s, "◄ GERİ", 22, (80, 43), WHITE)
        text(s, hd["name"], 40, (230, 110), WHITE, outline=3)
        text(s, f"Seviye {p['level']}", 24, (230, 150), GOLD)
        need = D.xp_needed(p["level"])
        pygame.draw.rect(s, (30, 20, 46), (110, 170, 240, 10), border_radius=5)
        pygame.draw.rect(s, (255, 200, 70), (110, 170, int(240 * p["xp"] / need), 10), border_radius=5)
        text(s, f"{p['xp']} / {need} XP", 14, (230, 192), (200, 190, 220))
        text(s, f"Altın: {p['gold']}    İksir: {p['potions']}", 18, (230, 650), GOLD)
        text(s, f"Yetenek puanı: {p['skill_pts']}", 18, (230, 676), (140, 220, 255))
        # sekmeler
        for k, name in enumerate(self.TABS):
            r = pygame.Rect(470 + k * 260, 24, 240, 50)
            sel = k == self.tab
            pygame.draw.rect(s, (70, 30, 100) if sel else (28, 16, 44), r, border_radius=12)
            if sel:
                pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
            text(s, name, 22, r.center, WHITE if sel else (170, 160, 190))
        items = self.items()
        for k, it in enumerate(items):
            r = self.row_rect(k)
            sel = k == self.i
            pygame.draw.rect(s, (56, 26, 84) if sel else (26, 14, 40), r, border_radius=14)
            if sel:
                pygame.draw.rect(s, hd["color"], r, 3, border_radius=14)
            self.draw_row(s, r, it)
        if self.msg[1] > 0:
            text(s, self.msg[0], 22, (850, H - 60), (255, 200, 120), outline=2)
        text(s, "← → sekme   •   ↑ ↓ seç   •   ENTER / dokun: uygula   •   ESC geri", 16, (850, H - 22),
             (170, 160, 200))

    def draw_row(self, s, r, it):
        p = self.p
        if self.tab == 0:
            if it == "nightmare":
                on = p.get("nightmare")
                text(s, "KABUS ZORLUĞU", 26, (r.x + 24, r.y + 26), (255, 90, 90), anchor="midleft")
                text(s, "Düşmanlar çok daha güçlü, ödüller de büyük.", 16, (r.x + 24, r.y + 56), (200, 190, 220),
                     anchor="midleft")
                text(s, "AÇIK" if on else "KAPALI", 24, (r.right - 24, r.centery), GOLD if on else (150, 140, 170),
                     anchor="midright")
                return
            ch = D.CHAPTERS[it]
            text(s, ch["name"], 26, (r.x + 24, r.y + 26), WHITE, anchor="midleft")
            done = it in p["cleared"]
            sub = f"Önerilen seviye {ch['level']}   •   4 dalga + boss: {D.BOSSES[ch['boss']]['name']}"
            text(s, sub, 16, (r.x + 24, r.y + 56), (200, 190, 220), anchor="midleft")
            text(s, "✓ TAMAM" if done else "BAŞLA ►", 22, (r.right - 24, r.centery), GOLD if not done else (120, 230, 140),
                 anchor="midright")
        elif self.tab == 1:
            sk = self.hd["skills"][it]
            lv = p["skills"][it]
            col = self.hd["color"] if not sk.get("ult") else (255, 200, 60)
            pygame.draw.circle(s, shade(col, 0.6), (r.x + 44, r.centery), 28)
            pygame.draw.circle(s, col, (r.x + 44, r.centery), 28, 3)
            text(s, ["1", "2", "3", "4"][it], 22, (r.x + 44, r.centery), WHITE)
            text(s, sk["name"] + ("  (ULTİMATE)" if sk.get("ult") else ""), 24, (r.x + 88, r.y + 26), WHITE,
                 anchor="midleft")
            if lv == 0:
                sub = f"Seviye {sk['unlock']}'de açılır"
            else:
                sub = f"Hasar x{sk['dmg'] * (1 + 0.22 * (lv - 1)):.1f}   •   {sk['cost']} enerji   •   " \
                      f"bekleme {sk['cd'] * (1 - 0.06 * (lv - 1)):.1f} sn"
            text(s, sub, 16, (r.x + 88, r.y + 56), (200, 190, 220), anchor="midleft")
            for k in range(5):
                c = col if k < lv else (60, 50, 80)
                pygame.draw.rect(s, c, (r.right - 200 + k * 34, r.centery - 10, 26, 20), border_radius=5)
            if lv and lv < 5:
                text(s, "+1 puan", 14, (r.right - 115, r.y + 12), (140, 220, 255))
        else:
            u = next(x for x in D.UPGRADES if x[0] == it)
            text(s, u[1], 24, (r.x + 24, r.y + 26), WHITE, anchor="midleft")
            text(s, u[2], 16, (r.x + 24, r.y + 56), (200, 190, 220), anchor="midleft")
            if it == "potion":
                text(s, f"{p['potions']}/5", 20, (r.right - 160, r.centery), WHITE, anchor="midright")
                text(s, "40 altın", 20, (r.right - 24, r.centery), GOLD, anchor="midright")
                return
            lv = p["up"][it]
            mx = u[4]
            for k in range(mx):
                c = (255, 200, 60) if k < lv else (60, 50, 80)
                pygame.draw.rect(s, c, (r.right - 330 + k * 18, r.centery - 8, 13, 16), border_radius=3)
            text(s, "EN YÜKSEK" if lv >= mx else f"{D.upgrade_price(it, lv)} altın", 20, (r.right - 24, r.centery),
                 GOLD, anchor="midright")
