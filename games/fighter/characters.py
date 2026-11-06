"""Özgün karakterler: istatistikler, renkler, özel hareketler."""

# Hareket komutları (karakter sağa bakarken; numpad gösterimi):
#  7 8 9     ↖ ↑ ↗
#  4 5 6  =  ← · →
#  1 2 3     ↙ ↓ ↘
MOTIONS = {
    "qcf": [2, 3, 6],        # ↓ ↘ →
    "qcb": [2, 1, 4],        # ↓ ↙ ←
    "dp": [6, 2, 3],         # → ↓ ↘
    "qcf2": [2, 3, 6, 2, 3, 6],  # ↓ ↘ → ↓ ↘ →
}
MOTION_TEXT = {"qcf": "↓ ↘ →", "qcb": "↓ ↙ ←", "dp": "→ ↓ ↘", "qcf2": "↓ ↘ → ↓ ↘ →"}

CHARACTERS = [
    {
        "id": "kaan",
        "name": "KAAN",
        "title": "Anadolu Ateşi",
        "desc": "Dengeli dövüşçü. Uzaktan ateş topu, yakına kartal yumruğu.",
        "scale": 1.0, "bulk": 1.0, "speed": 4.2, "jump": 17.0, "health": 1000, "power": 1.0,
        "hair_style": "short", "sleeve": None, "hand_wrap": True,
        "palette": dict(skin=(226, 170, 124), top=(34, 40, 64), pants=(46, 46, 54), glove=(226, 170, 124),
                        belt=(196, 40, 40), hair=(26, 18, 14), accent=(230, 180, 60), wrap=(236, 232, 220),
                        eye=(70, 45, 25)),
        "alt": dict(skin=(226, 170, 124), top=(110, 26, 30), pants=(30, 28, 32), glove=(226, 170, 124),
                    belt=(230, 180, 60), hair=(26, 18, 14), accent=(230, 180, 60), wrap=(40, 40, 46),
                    eye=(70, 45, 25)),
        "fx": (255, 120, 30),
        "specials": [
            {"name": "Ateş Topu", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 90, "speed": 9.5,
             "radius": 24, "color": (255, 130, 30), "startup": 12, "recovery": 22, "pose": ("push_s", "push")},
            {"name": "Kartal Yumruğu", "motion": "dp", "button": "P", "type": "rising", "dmg": 130, "vy": -15.5,
             "vx": 2.5, "hits": 2, "invuln": 8, "startup": 3, "recovery": 18, "pose": ("upper_s", "upper"), "limb": "hand_f"},
            {"name": "Kasırga Tekmesi", "motion": "qcb", "button": "K", "type": "dash", "dmg": 110, "vx": 6.5,
             "dur": 34, "air": True, "hits": 3, "startup": 6, "recovery": 14, "pose": ("spin_a", "spin_b"), "limb": "foot_f"},
        ],
        "super": {"name": "Alev Fırtınası", "motion": "qcf2", "button": "P", "type": "projectile", "dmg": 300,
                  "speed": 11.0, "radius": 46, "color": (255, 90, 20), "hits": 5, "startup": 16, "recovery": 26,
                  "pose": ("push_s", "push")},
    },
    {
        "id": "zeyna",
        "name": "ZEYNA",
        "title": "Rüzgârın Kızı",
        "desc": "Çok hızlı, hava hâkimi. Darbeleri hafif ama kombosu uzun.",
        "scale": 0.94, "bulk": 0.86, "speed": 5.2, "jump": 18.5, "health": 900, "power": 0.88,
        "hair_style": "ponytail", "sleeve": "tank", "tank": True, "tight_pants": True, "armband": True,
        "palette": dict(skin=(214, 160, 120), top=(30, 150, 190), pants=(24, 60, 110), glove=(240, 240, 250),
                        belt=(250, 210, 80), hair=(26, 20, 40), accent=(250, 210, 80), shoe=(240, 240, 250),
                        wrap=(250, 210, 80)),
        "alt": dict(skin=(214, 160, 120), top=(200, 60, 140), pants=(70, 20, 70), glove=(250, 250, 250),
                    belt=(120, 240, 220), hair=(120, 30, 40), accent=(120, 240, 220), shoe=(250, 250, 250),
                    wrap=(120, 240, 220)),
        "fx": (90, 230, 255),
        "specials": [
            {"name": "Rüzgâr Hançeri", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 70, "speed": 13.0,
             "radius": 16, "color": (90, 230, 255), "startup": 9, "recovery": 16, "pose": ("push_s", "push")},
            {"name": "Ay Takla Tekmesi", "motion": "dp", "button": "K", "type": "rising", "dmg": 120, "vy": -16.5,
             "vx": 3.0, "hits": 2, "invuln": 7, "startup": 3, "recovery": 16, "pose": ("kick_s", "round"), "limb": "foot_f"},
            {"name": "Şimşek Tekmesi", "motion": "qcf", "button": "K", "type": "dash", "dmg": 100, "vx": 11.0,
             "dur": 20, "air": True, "hits": 2, "startup": 7, "recovery": 16, "pose": ("flykick", "flykick"), "limb": "foot_f"},
        ],
        "super": {"name": "Fırtına Dansı", "motion": "qcf2", "button": "K", "type": "dash", "dmg": 290, "vx": 12.5,
                  "dur": 44, "air": False, "hits": 7, "startup": 12, "recovery": 22, "pose": ("spin_a", "spin_b"), "limb": "foot_f"},
    },
    {
        "id": "demir",
        "name": "DEMİR",
        "title": "Dağların Pehlivanı",
        "desc": "Yavaş ama devasa güç. Yer sarsan darbeler, yüksek can.",
        "scale": 1.14, "bulk": 1.25, "speed": 3.3, "jump": 15.5, "health": 1150, "power": 1.22,
        "hair_style": "bald", "bare_chest": True, "champ_belt": True, "hand_wrap": True, "strap": False,
        "palette": dict(skin=(196, 134, 92), top=(120, 70, 40), pants=(70, 90, 50), glove=(110, 70, 40),
                        belt=(220, 170, 50), hair=(30, 22, 18), accent=(220, 170, 50), shoe=(60, 40, 30)),
        "alt": dict(skin=(196, 134, 92), top=(40, 40, 40), pants=(140, 30, 30), glove=(40, 40, 40),
                    belt=(220, 220, 230), hair=(30, 22, 18), accent=(220, 220, 230), shoe=(30, 30, 30)),
        "fx": (255, 210, 90),
        "specials": [
            {"name": "Deprem", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 100, "speed": 7.5,
             "radius": 26, "color": (230, 180, 80), "ground": True, "startup": 16, "recovery": 24, "pose": ("slam_s", "slam")},
            {"name": "Boğa Hücumu", "motion": "qcb", "button": "P", "type": "dash", "dmg": 140, "vx": 9.0,
             "dur": 24, "air": False, "hits": 1, "startup": 10, "recovery": 20, "pose": ("charge", "charge"), "limb": "sho",
             "armor": True},
            {"name": "Gök Gürültüsü", "motion": "dp", "button": "K", "type": "stomp", "dmg": 150, "vy": -14.0,
             "vx": 5.0, "hits": 1, "startup": 6, "recovery": 22, "pose": ("stomp_air", "stomp"), "limb": "foot_f"},
        ],
        "super": {"name": "Dağ Devrilmesi", "motion": "qcf2", "button": "P", "type": "dash", "dmg": 290, "vx": 10.0,
                  "dur": 30, "air": False, "hits": 3, "startup": 14, "recovery": 26, "pose": ("charge", "slam"), "limb": "sho",
                  "armor": True},
    },
]

def _sprite(cid, name, title, desc, speed, jump, health, power, fx, specials, super_):
    return {"id": cid, "name": name, "title": title, "desc": desc, "sprite": cid, "scale": 1.0, "bulk": 1.0,
            "speed": speed, "jump": jump, "health": health, "power": power, "fx": fx,
            "palette": {}, "alt": {}, "specials": specials, "super": super_}


SPRITE_CHARACTERS = [
    _sprite("daiki", "DAİKİ", "Dövüş Ustası", "Geleneksel dövüş ustası. Ki dalgası ve ejder yükselişiyle dengeli.",
            4.3, 17.0, 1000, 1.0, (90, 170, 255),
            [{"name": "Ki Dalgası", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 90, "speed": 9.5,
              "radius": 26, "color": (90, 170, 255), "startup": 12, "recovery": 20, "pose": ("push_s", "push"), "anim": "Attack_3"},
             {"name": "Ejder Yükselişi", "motion": "dp", "button": "P", "type": "rising", "dmg": 130, "vy": -15.5, "vx": 2.5,
              "hits": 2, "invuln": 8, "startup": 3, "recovery": 18, "pose": ("upper_s", "upper"), "limb": "hand_f", "anim": "Attack_1"},
             {"name": "Kasırga Tekmesi", "motion": "qcb", "button": "K", "type": "dash", "dmg": 110, "vx": 6.5, "dur": 34,
              "air": True, "hits": 3, "startup": 6, "recovery": 14, "pose": ("spin_a", "spin_b"), "limb": "foot_f",
              "anim": "Attack_2", "spin": True}],
            {"name": "Ejder Fırtınası", "motion": "qcf2", "button": "P", "type": "projectile", "dmg": 300, "speed": 11.0,
             "radius": 48, "color": (110, 190, 255), "hits": 5, "startup": 16, "recovery": 26, "pose": ("push_s", "push"),
             "anim": "Attack_3"}),
    _sprite("jax", "JAX", "Sokak Kurdu", "Hızlı ve çevik. Kısa sürede uzun kombolar kurar.",
            5.1, 18.0, 920, 0.9, (255, 70, 170),
            [{"name": "Neon Bıçağı", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 70, "speed": 13.0,
              "radius": 17, "color": (255, 90, 190), "startup": 9, "recovery": 16, "pose": ("push_s", "push"), "anim": "Attack_1"},
             {"name": "Uçan Diz", "motion": "dp", "button": "K", "type": "rising", "dmg": 120, "vy": -16.5, "vx": 3.0,
              "hits": 2, "invuln": 7, "startup": 3, "recovery": 16, "pose": ("kick_s", "round"), "limb": "foot_f", "anim": "Attack_2"},
             {"name": "Şimşek Hücumu", "motion": "qcf", "button": "K", "type": "dash", "dmg": 100, "vx": 11.0, "dur": 20,
              "air": False, "hits": 2, "startup": 7, "recovery": 16, "pose": ("flykick", "flykick"), "limb": "foot_f", "anim": "Attack_3"}],
            {"name": "Neon Kasırgası", "motion": "qcf2", "button": "K", "type": "dash", "dmg": 290, "vx": 12.5, "dur": 44,
             "air": False, "hits": 7, "startup": 12, "recovery": 22, "pose": ("spin_a", "spin_b"), "limb": "foot_f",
             "anim": "Attack_2", "spin": True}),
    _sprite("kaito", "KAİTO", "Gümüş Saçlı Meydan Okuyan", "Kendinden emin, uzak mesafe ustası. Ateşle oynar.",
            4.6, 17.5, 960, 0.95, (255, 90, 60),
            [{"name": "Gümüş Alev", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 85, "speed": 10.5,
              "radius": 22, "color": (255, 110, 60), "startup": 11, "recovery": 18, "pose": ("push_s", "push"), "anim": "Attack_3"},
             {"name": "Ay Kesiği", "motion": "dp", "button": "K", "type": "rising", "dmg": 125, "vy": -16.0, "vx": 3.0,
              "hits": 2, "invuln": 7, "startup": 3, "recovery": 17, "pose": ("kick_s", "round"), "limb": "foot_f", "anim": "Attack_2"},
             {"name": "Hayalet Adım", "motion": "qcb", "button": "K", "type": "dash", "dmg": 100, "vx": 10.0, "dur": 22,
              "air": False, "hits": 2, "startup": 6, "recovery": 15, "pose": ("flykick", "flykick"), "limb": "foot_f", "anim": "Attack_2"}],
            {"name": "Kızıl Ay", "motion": "qcf2", "button": "P", "type": "projectile", "dmg": 300, "speed": 12.0,
             "radius": 44, "color": (255, 70, 50), "hits": 5, "startup": 16, "recovery": 24, "pose": ("push_s", "push"),
             "anim": "Attack_3"}),
    _sprite("titus", "TİTUS", "Demir Yumruk", "Ağır sıklet. Yavaş ama her darbesi yer sarsar.",
            3.4, 15.5, 1150, 1.2, (255, 190, 60),
            [{"name": "Yer Sarsıntısı", "motion": "qcf", "button": "P", "type": "projectile", "dmg": 100, "speed": 7.5,
              "radius": 26, "color": (230, 180, 80), "ground": True, "startup": 16, "recovery": 24, "pose": ("slam_s", "slam"),
              "anim": "Attack_3"},
             {"name": "Buldozer", "motion": "qcb", "button": "P", "type": "dash", "dmg": 140, "vx": 9.0, "dur": 24, "air": False,
              "hits": 1, "startup": 10, "recovery": 20, "pose": ("charge", "charge"), "limb": "sho", "armor": True, "anim": "Attack_3"},
             {"name": "Gök Çekici", "motion": "dp", "button": "K", "type": "stomp", "dmg": 150, "vy": -14.0, "vx": 5.0, "hits": 1,
              "startup": 6, "recovery": 22, "pose": ("stomp_air", "stomp"), "limb": "foot_f", "anim": "Attack_2"}],
            {"name": "Dağ Devrilmesi", "motion": "qcf2", "button": "P", "type": "dash", "dmg": 290, "vx": 10.0, "dur": 30,
             "air": False, "hits": 3, "startup": 14, "recovery": 26, "pose": ("charge", "slam"), "limb": "sho", "armor": True,
             "anim": "Attack_3"}),
]

CHARACTERS = SPRITE_CHARACTERS + CHARACTERS

# Normal saldırılar: startup / active / recovery kare sayıları
NORMALS = {
    "jab": dict(pose=("jab_s", "jab"), limb="hand_f", dmg=40, s=4, a=3, r=8, hitstun=14, block=10, push=4.0, height="mid",
                chain=("cross", "kick"), snd="hit_l"),
    "cross": dict(pose=("cross_s", "cross"), limb="hand_b", dmg=70, s=6, a=3, r=14, hitstun=18, block=12, push=5.0,
                  height="mid", chain=("kick", "round"), snd="hit_l"),
    "kick": dict(pose=("kick_s", "kick"), limb="foot_f", dmg=80, s=7, a=4, r=16, hitstun=20, block=12, push=4.0,
                 height="mid", chain=("round",), snd="hit_h"),
    "round": dict(pose=("round_s", "round"), limb="foot_f", dmg=110, s=8, a=4, r=20, hitstun=22, block=14, push=8.0,
                  height="mid", chain=(), knockdown=True, snd="hit_h"),
    "cjab": dict(pose=("crouch", "cjab"), limb="hand_f", dmg=35, s=4, a=3, r=8, hitstun=13, block=9, push=4.0,
                 height="mid", chain=("cjab", "sweep"), snd="hit_l", crouch=True),
    "sweep": dict(pose=("sweep_s", "sweep"), limb="foot_f", dmg=75, s=8, a=4, r=22, hitstun=20, block=12, push=6.0,
                  height="low", chain=(), knockdown=True, snd="hit_h", crouch=True),
    "air_p": dict(pose=("jump", "air_p"), limb="hand_f", dmg=60, s=4, a=8, r=4, hitstun=16, block=12, push=4.0,
                  height="high", chain=(), snd="hit_l", air=True),
    "air_k": dict(pose=("jump", "air_k"), limb="foot_f", dmg=85, s=5, a=10, r=4, hitstun=18, block=14, push=5.0,
                  height="high", chain=(), snd="hit_h", air=True),
}
