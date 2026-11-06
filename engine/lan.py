"""Ağda oyna (LAN) lobisi: oyun kur / katıl, karakter seçimi, başlatma."""
import random

import pygame

from engine.core import GOLD, WHITE, W, H, Scene, is_back, is_confirm, nav_dir, shade, text, vgradient
from engine import net

MODES = [("fight", "DÖVÜŞ ARENASI", "Karşılıklı dövüş"), ("hack", "GÖLGE SEFERİ", "Birlikte macera (co-op)"),
         ("pong", "NEON PONG", "Karşılıklı pong")]
MODE_NAMES = {m[0]: m[1] for m in MODES}


class LanLobby(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.state = "root"
        self.i = 0
        self.t = 0.0
        self.bg = vgradient(W, H, (8, 10, 30), (30, 10, 50))
        self.mode = None
        self.conn = None
        self.side = 0
        self.announcer = self.listener = self.finder = None
        self.ip_text = ""
        self.msg = ""
        self.my = dict(pick=0, ready=False, chapter=0)
        self.other = dict(pick=None, ready=False, profile=None, hero=None)
        self.error = ""

    # ------------------------------------------------------------------ yardımcılar
    def cleanup_net(self):
        for x in (self.announcer, self.listener, self.finder):
            if x:
                x.stop()
        self.announcer = self.listener = self.finder = None

    def disconnect(self, msg=""):
        self.cleanup_net()
        if self.conn:
            self.conn.send({"t": "bye"})
            self.conn.close()
        self.conn = None
        self.state = "root"
        self.i = 0
        self.msg = msg

    def options(self):
        if self.state == "root":
            return ["OYUN KUR", "OYUNA KATIL", "GERİ"]
        if self.state == "host_pick":
            return [m[1] for m in MODES] + ["GERİ"]
        if self.state == "join":
            hosts = self.finder.list() if self.finder else []
            return [f"{MODE_NAMES.get(m, m)}  —  {name}  ({ip})" for ip, m, name, port in hosts] + \
                ["IP ile bağlan: " + (self.ip_text or "_"), "GERİ"]
        return []

    def on_enter(self):
        self.app.audio.play_music("menu")
        if self.conn is not None:
            if self.conn.alive:
                self.state = "setup"
                self.my["ready"] = False
                self.other["ready"] = False
                self.send_pick()
            else:
                self.disconnect("Bağlantı koptu.")

    def send_pick(self):
        if not self.conn:
            return
        m = {"t": "pick", "pick": self.my["pick"], "ready": self.my["ready"], "chapter": self.my["chapter"]}
        if self.mode == "hack":
            from games.hack.camp import profiles
            from games.hack.data import HERO_ORDER
            hid = HERO_ORDER[self.my["pick"]]
            m["hero"] = hid
            m["profile"] = profiles(self.app)[hid]
        self.conn.send(m)

    # ------------------------------------------------------------------ giriş
    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            x, y = e.pos
            if x < 160 and y < 90:
                e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
            elif self.state in ("root", "host_pick", "join"):
                for k in range(len(self.options())):
                    if self.row(k).collidepoint(e.pos):
                        self.i = k
                        e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                        break
                else:
                    return
            elif self.state == "setup":
                if x < W // 3:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)
                elif x > W * 2 // 3:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)
                else:
                    e = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        if self.state == "join" and e.type == pygame.KEYDOWN and self.i == len(self.options()) - 2:
            if e.unicode and (e.unicode.isdigit() or e.unicode == "."):
                self.ip_text = (self.ip_text + e.unicode)[:15]
                return
            if e.key == pygame.K_BACKSPACE:
                self.ip_text = self.ip_text[:-1]
                return
        if is_back(e):
            self.app.audio.play("back")
            if self.state == "root":
                self.cleanup_net()
                self.app.pop()
            else:
                self.disconnect()
            return
        d = nav_dir(e)
        opts = self.options()
        if d and d[1] and opts:
            self.i = (self.i + d[1]) % len(opts)
            self.app.audio.play("menu")
            return
        if self.state == "setup":
            self.setup_input(e, d)
            return
        if not is_confirm(e) or not opts:
            return
        self.app.audio.play("select")
        choice = self.i
        if self.state == "root":
            if choice == 0:
                self.state, self.i = "host_pick", 0
            elif choice == 1:
                self.state, self.i = "join", 0
                self.finder = net.Finder()
            else:
                self.app.pop()
        elif self.state == "host_pick":
            if choice == len(MODES):
                self.state, self.i = "root", 0
                return
            self.mode = MODES[choice][0]
            self.side = 0
            self.listener = net.HostListener()
            self.announcer = net.Announcer(self.mode, "Kanatix-" + net.local_ip().split(".")[-1])
            self.state = "hosting"
        elif self.state == "join":
            hosts = self.finder.list() if self.finder else []
            if choice == len(opts) - 1:
                self.disconnect()
                return
            ip = self.ip_text if choice == len(opts) - 2 else hosts[choice][0]
            if not ip:
                self.msg = "Önce IP adresini yaz (örn. 192.168.1.20)"
                return
            try:
                self.conn = net.connect(ip)
                self.side = 1
                self.state = "waiting_hello"
                self.msg = ""
            except Exception as ex:
                self.msg = f"Bağlanılamadı: {ex}"[:90]

    def setup_input(self, e, d):
        if self.mode == "pong":
            return
        n = 4
        if d and d[0] and not self.my["ready"]:
            self.my["pick"] = (self.my["pick"] + d[0]) % n
            self.app.audio.play("menu")
            self.send_pick()
        elif d and d[1] and self.mode == "hack" and self.side == 0 and not self.my["ready"]:
            from games.hack.camp import profiles
            from games.hack.data import HERO_ORDER, CHAPTERS
            p = profiles(self.app)[HERO_ORDER[self.my["pick"]]]
            mx = min(p["chapter"], len(CHAPTERS)) - 1
            self.my["chapter"] = max(0, min(mx, self.my["chapter"] + d[1]))
            self.send_pick()
        elif is_confirm(e) or (e.type == pygame.KEYDOWN and e.key in (pygame.K_k, pygame.K_f)):
            self.my["ready"] = not self.my["ready"]
            self.app.audio.play("select")
            self.send_pick()

    # ------------------------------------------------------------------ güncelleme
    def update(self, dt):
        self.t += dt
        if self.state == "hosting" and self.listener:
            if self.listener.error:
                self.msg = self.listener.error
            if self.listener.conn:
                self.conn = self.listener.conn
                self.cleanup_net()
                self.conn.send({"t": "hello", "mode": self.mode})
                self.enter_setup()
        if self.conn is None:
            return
        if not self.conn.alive:
            self.disconnect("Bağlantı koptu.")
            return
        for m in self.conn.poll():
            t = m.get("t")
            if t == "hello" and self.side == 1:
                self.mode = m["mode"]
                if self.finder:
                    self.finder.stop()
                    self.finder = None
                self.enter_setup()
            elif t == "pick":
                self.other.update(pick=m.get("pick"), ready=m.get("ready"), hero=m.get("hero"),
                                  profile=m.get("profile"), chapter=m.get("chapter", 0))
            elif t == "start" and self.side == 1:
                self.start_game(m)
                return
            elif t == "bye":
                self.disconnect("Diğer oyuncu ayrıldı.")
                return
        if self.state == "setup" and self.side == 0:
            if self.mode == "pong" or (self.my["ready"] and self.other["ready"] and self.other["pick"] is not None):
                self.host_start()

    def enter_setup(self):
        self.state = "setup"
        self.my = dict(pick=0 if self.side == 0 else 1, ready=False, chapter=0)
        self.other = dict(pick=None, ready=False, profile=None, hero=None)
        self.send_pick()

    def host_start(self):
        seed = random.randrange(1, 1 << 30)
        m = {"t": "start", "mode": self.mode, "seed": seed}
        if self.mode == "fight":
            from games.fighter.stages import STAGES
            m["c"] = [self.my["pick"], self.other["pick"]]
            m["stage"] = random.randrange(len(STAGES))
        elif self.mode == "hack":
            from games.hack.camp import profiles
            from games.hack.data import HERO_ORDER
            hid = HERO_ORDER[self.my["pick"]]
            m["chapter"] = self.my["chapter"]
            m["heroes"] = [[hid, profiles(self.app)[hid]], [self.other["hero"], self.other["profile"]]]
        self.conn.send(m)
        self.start_game(m)

    def start_game(self, m):
        ls = net.Lockstep(self.conn, self.side, m["seed"])
        self.my["ready"] = self.other["ready"] = False
        mode = m.get("mode", self.mode)
        if mode == "fight":
            from games.fighter.scene import FightScene
            c0, c1 = m["c"]
            self.app.push(FightScene(self.app, c0, c1, m["stage"], False, net=ls))
        elif mode == "hack":
            from games.hack.camp import profiles
            from games.hack.level import HackLevel
            heroes = [list(x) for x in m["heroes"]]
            # kendi kahramanımızın profili gerçek kayıt nesnesi olsun (ilerleme kaydedilsin)
            mine = heroes[self.side]
            real = profiles(self.app)[mine[0]]
            if mine[1] is not real:
                data = dict(mine[1])
                real.clear()
                real.update(data)
            heroes[self.side][1] = real
            self.app.push(HackLevel(self.app, mine[0], real, m["chapter"], net=ls,
                                    heroes=[tuple(h) for h in heroes], seed=m["seed"]))
        else:
            from games.pong import PongGame
            self.app.push(PongGame(self.app, net=ls))

    # ------------------------------------------------------------------ çizim
    def row(self, k):
        return pygame.Rect(W // 2 - 330, 200 + k * 66, 660, 54)

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        for i in range(-4, 20):
            x = i * 90 + (self.t * 30) % 90
            pygame.draw.line(s, (20, 18, 50), (x, 0), (x - 300, H), 16)
        text(s, "AĞDA OYNA (LAN)", 54, (W // 2, 60), GOLD, outline=4)
        pygame.draw.rect(s, (40, 24, 60), (20, 20, 120, 46), border_radius=12)
        text(s, "◄ GERİ", 22, (80, 43), WHITE)
        ip = net.local_ip()
        text(s, f"Bu bilgisayarın IP adresi: {ip}", 18, (W // 2, 110), (170, 200, 255))
        if self.state in ("root", "host_pick", "join"):
            sub = {"root": "Aynı ağdaki (aynı modem / Wi-Fi) iki cihazla oyna",
                   "host_pick": "Hangi oyunu kuracaksın?",
                   "join": "Ağdaki oyunlar aranıyor..." + ("" if self.options()[:-2] else "  (henüz bulunamadı)")}[self.state]
            text(s, sub, 22, (W // 2, 160), WHITE)
            for k, opt in enumerate(self.options()):
                r = self.row(k)
                sel = k == self.i
                pygame.draw.rect(s, (60, 26, 96) if sel else (24, 14, 40), r, border_radius=12)
                if sel:
                    pygame.draw.rect(s, GOLD, r, 3, border_radius=12)
                text(s, opt, 24, r.center, WHITE if sel else (180, 170, 200))
            if self.state == "join":
                text(s, "Bulunamazsa: oyunu kuran bilgisayarın IP adresini 'IP ile bağlan' satırına yaz ve ENTER'a bas",
                     16, (W // 2, H - 70), (190, 180, 220))
        elif self.state == "hosting":
            text(s, f"{MODE_NAMES[self.mode]} kuruldu", 34, (W // 2, 230), WHITE, outline=2)
            dots = "." * (int(self.t * 2) % 4)
            text(s, "Arkadaşının katılması bekleniyor" + dots, 26, (W // 2, 300), (190, 210, 255))
            text(s, f"Diğer bilgisayarda: Ağda Oyna → Oyuna Katıl  (IP: {ip})", 22, (W // 2, 360), GOLD)
            text(s, "Windows güvenlik duvarı izin isterse 'Özel ağlar' için İZİN VER'i seç.", 18, (W // 2, 420),
                 (200, 190, 230))
        elif self.state == "waiting_hello":
            text(s, "Bağlanıldı, kurucu bekleniyor...", 30, (W // 2, 300), WHITE)
        elif self.state == "setup":
            self.draw_setup(s)
        if self.msg:
            text(s, self.msg, 20, (W // 2, H - 40), (255, 160, 120), outline=1)

    def draw_setup(self, s):
        text(s, MODE_NAMES[self.mode] + "  •  " + ("KURUCU (1P)" if self.side == 0 else "KATILAN (2P)"), 28,
             (W // 2, 160), WHITE, outline=2)
        if self.mode == "pong":
            text(s, "Başlıyor...", 30, (W // 2, 330), GOLD)
            return
        from games.fighter import sprites
        if self.mode == "fight":
            from games.fighter.characters import CHARACTERS
            names = [c["name"] for c in CHARACTERS]
            cids = [c["sprite"] for c in CHARACTERS]
        else:
            from games.hack.data import HERO_ORDER, HEROES, CHAPTERS
            from games.hack.camp import profiles
            names = [HEROES[h]["name"] for h in HERO_ORDER]
            cids = HERO_ORDER
        for who, data, x in (("SEN", self.my, 330), ("ARKADAŞIN", self.other, W - 330)):
            pick = data["pick"]
            text(s, who, 26, (x, 210), GOLD if who == "SEN" else (170, 200, 255), outline=2)
            if pick is None:
                text(s, "bekleniyor...", 22, (x, 400), (180, 170, 200))
                continue
            sprites.draw_static(s, cids[pick], "Idle", int(self.t * 10), x, 560, 1 if x < W // 2 else -1, 0.95)
            label = names[pick]
            if self.mode == "hack":
                prof = profiles(self.app)[cids[pick]] if who == "SEN" else (data.get("profile") or {})
                label += f"  (Sv {prof.get('level', 1)})"
            text(s, label, 30, (x, 600), WHITE, outline=2)
            text(s, "HAZIR ✓" if data["ready"] else "seçiyor", 24, (x, 640), (120, 255, 140) if data["ready"] else
                 (190, 180, 220))
        if self.mode == "hack":
            ch = self.my["chapter"] if self.side == 0 else self.other.get("chapter", 0) or 0
            text(s, CHAPTERS[ch]["name"], 22, (W // 2, 250), shade((255, 200, 120), 1.0))
            if self.side == 0:
                text(s, "↑ ↓ bölüm seç (açtığın bölümler)", 16, (W // 2, 276), (190, 180, 220))
        text(s, "← → karakter   •   ENTER: hazır   •   ESC: ayrıl", 18, (W // 2, H - 70), (190, 180, 220))
