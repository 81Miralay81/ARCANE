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

CHARACTERS = SPRITE_CHARACTERS

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
