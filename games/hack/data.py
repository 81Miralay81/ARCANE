"""Gölge Seferi (hack and slash) verileri: kahramanlar, yetenekler, düşmanlar, bölümler."""

# Yetenek türleri:
#  projectile : mermi (count, spread, speed, pierce, explode)
#  dash       : ileri atılarak yol boyunca vurur
#  uppercut   : öndeki düşmanları havaya kaldırır
#  slam       : zıplayıp yere çakılır, alan hasarı
#  teleport   : en yakın düşmanın arkasına ışınlanıp vurur
#  flurry     : (ultimate) ekrandaki düşmanlar arasında ışınlanarak çoklu vuruş
#  storm      : (ultimate) tüm ekrana dalgalar halinde hasar
#  meteors    : (ultimate) gökten yağan ateş topları
#  pillars    : (ultimate) yerden sırayla fışkıran sütunlar

HEROES = {
    "daiki": dict(name="DAİKİ", title="Dövüş Ustası", color=(90, 170, 255), hp=520, atk=34, spd=4.4,
                  desc="Dengeli usta. Ki enerjisiyle uzak ve yakın dövüşü birleştirir.",
                  skills=[
                      dict(name="Ki Dalgası", type="projectile", cost=18, cd=2.2, dmg=2.2, speed=12, pierce=True,
                           radius=30, style="orb", unlock=1, anim="Attack_3"),
                      dict(name="Ejder Yükselişi", type="uppercut", cost=22, cd=4.0, dmg=2.8, range=150, unlock=3,
                           anim="Attack_1", style="flame"),
                      dict(name="Kasırga Tekmesi", type="dash", cost=26, cd=6.0, dmg=1.0, hits=5, dist=360, unlock=5,
                           anim="Attack_2", style="wind"),
                      dict(name="Ejder Fırtınası", type="storm", cost=70, cd=22.0, dmg=1.6, hits=8, unlock=8,
                           anim="Attack_3", style="dragon", ult=True),
                  ]),
    "jax": dict(name="JAX", title="Sokak Kurdu", color=(255, 70, 170), hp=440, atk=30, spd=5.3,
                desc="En hızlı kahraman. Kısa bekleme süreli yeteneklerle durmadan saldırır.",
                skills=[
                    dict(name="Neon Bıçakları", type="projectile", cost=14, cd=1.6, dmg=1.3, speed=15, count=3,
                         spread=0.22, radius=16, style="blade", unlock=1, anim="Attack_1"),
                    dict(name="Şimşek Hücumu", type="dash", cost=18, cd=3.2, dmg=2.0, hits=2, dist=420, unlock=3,
                         anim="Attack_3", style="lightning"),
                    dict(name="Uçan Diz", type="slam", cost=24, cd=5.0, dmg=2.6, radius=170, unlock=5,
                         anim="Attack_2", style="neon"),
                    dict(name="Neon Kasırgası", type="flurry", cost=65, cd=20.0, dmg=1.2, hits=14, unlock=8,
                         anim="Attack_3", style="neon", ult=True),
                ]),
    "kaito": dict(name="KAİTO", title="Gümüş Alev", color=(255, 90, 60), hp=470, atk=33, spd=4.7,
                  desc="Ateş ustası. Patlayan alevler ve ışınlanmayla kalabalıkları dağıtır.",
                  skills=[
                      dict(name="Gümüş Alev", type="projectile", cost=18, cd=2.0, dmg=1.8, speed=11, explode=130,
                           radius=24, style="fire", unlock=1, anim="Attack_3"),
                      dict(name="Ay Kesiği", type="projectile", cost=22, cd=3.6, dmg=2.4, speed=14, pierce=True,
                           radius=46, style="crescent", unlock=3, anim="Attack_2"),
                      dict(name="Hayalet Adım", type="teleport", cost=24, cd=4.5, dmg=3.0, unlock=5,
                           anim="Attack_3", style="ghost"),
                      dict(name="Kızıl Ay", type="meteors", cost=70, cd=22.0, dmg=2.2, hits=14, unlock=8,
                           anim="Attack_3", style="meteor", ult=True),
                  ]),
    "titus": dict(name="TİTUS", title="Demir Yumruk", color=(255, 190, 60), hp=660, atk=40, spd=3.7,
                  desc="Ağır tank. Yavaş ama zırhlı; yeri sarsarak düşmanları yere serer.",
                  skills=[
                      dict(name="Yer Sarsıntısı", type="projectile", cost=20, cd=2.6, dmg=2.0, speed=9, pierce=True,
                           radius=34, style="quake", ground=True, unlock=1, anim="Attack_3"),
                      dict(name="Buldozer", type="dash", cost=22, cd=4.2, dmg=2.4, hits=1, dist=380, armor=True,
                           unlock=3, anim="Attack_3", style="dust"),
                      dict(name="Gök Çekici", type="slam", cost=28, cd=5.5, dmg=3.4, radius=230, unlock=5,
                           anim="Attack_2", style="quake"),
                      dict(name="Dağ Devrilmesi", type="pillars", cost=70, cd=22.0, dmg=3.0, hits=10, unlock=8,
                           anim="Attack_3", style="rock", ult=True),
                  ]),
}
HERO_ORDER = ["daiki", "jax", "kaito", "titus"]

# Düşmanlar: sprite, renk tonu, istatistikler, davranış
ENEMIES = {
    "haydut": dict(name="Gölge Haydut", sprite="jax", tint=(120, 80, 190), hp=60, atk=8, spd=3.4, scale=0.66,
                   xp=8, gold=4, ai="melee", reach=90, cd=1.4, windup=0.38),
    "dovuscu": dict(name="Gölge Dövüşçü", sprite="daiki", tint=(80, 100, 210), hp=95, atk=11, spd=2.8, scale=0.7,
                    xp=12, gold=6, ai="melee", reach=100, cd=1.6, windup=0.42),
    "buyucu": dict(name="Ateş Büyücüsü", sprite="kaito", tint=(220, 80, 70), hp=70, atk=12, spd=2.6, scale=0.68,
                   xp=14, gold=8, ai="ranged", reach=520, cd=2.6, windup=0.6),
    "dev": dict(name="Demir Dev", sprite="titus", tint=(130, 130, 150), hp=260, atk=20, spd=1.9, scale=0.82,
                xp=30, gold=16, ai="brute", reach=130, cd=2.6, windup=0.85, armor=True),
}

BOSSES = {
    "golge_usta": dict(name="GÖLGE USTA", sprite="daiki", tint=(80, 60, 160), hp=1800, atk=22, spd=3.2, scale=0.9,
                       xp=260, gold=180, ai="boss", reach=120, cd=1.5, windup=0.5, armor=True,
                       moves=["wave", "dash", "slam"], aura=(120, 90, 255)),
    "neon_kralice": dict(name="NEON KRALİÇE", sprite="jax", tint=(255, 90, 200), hp=2600, atk=26, spd=4.6, scale=0.9,
                         xp=420, gold=280, ai="boss", reach=110, cd=1.1, windup=0.42, armor=True,
                         moves=["dash", "blades", "summon"], aura=(255, 80, 200)),
    "kizil_imparator": dict(name="KIZIL İMPARATOR", sprite="kaito", tint=(255, 70, 50), hp=3800, atk=30, spd=3.6,
                            scale=0.95, xp=700, gold=450, ai="boss", reach=120, cd=1.2, windup=0.5, armor=True,
                            moves=["wave", "meteors", "dash", "summon"], aura=(255, 60, 30)),
}

CHAPTERS = [
    dict(name="Bölüm 1: Ejder Kalesi", stage="stage1.jpg", effect="embers", tint=(255, 140, 60), level=1,
         waves=[["haydut"] * 3, ["haydut", "haydut", "dovuscu"], ["dovuscu", "dovuscu", "haydut", "haydut"],
                ["dovuscu", "haydut", "haydut", "dev"]],
         boss="golge_usta"),
    dict(name="Bölüm 2: Neon Çatı", stage="stage2.jpg", effect="rain", tint=(255, 60, 120), level=5,
         waves=[["haydut", "haydut", "buyucu"], ["dovuscu", "dovuscu", "buyucu", "haydut"],
                ["dev", "buyucu", "buyucu", "haydut"], ["dovuscu", "dovuscu", "dev", "buyucu", "haydut"]],
         boss="neon_kralice"),
    dict(name="Bölüm 3: Gece Metrosu", stage="stage3.jpg", effect="rain", tint=(90, 160, 255), level=9,
         waves=[["dovuscu", "buyucu", "buyucu", "haydut", "haydut"], ["dev", "dev", "buyucu"],
                ["dovuscu", "dovuscu", "dovuscu", "buyucu", "buyucu"], ["dev", "dev", "dovuscu", "buyucu", "haydut", "haydut"]],
         boss="kizil_imparator"),
]

# Kampta altınla alınan geliştirmeler: (anahtar, ad, açıklama, temel fiyat, en yüksek seviye)
UPGRADES = [
    ("hp", "Can", "+%10 en yüksek can", 60, 10),
    ("atk", "Güç", "+%8 saldırı gücü", 70, 10),
    ("crit", "Kritik", "+%4 kritik vuruş şansı", 80, 8),
    ("energy", "Enerji", "+15 enerji ve daha hızlı dolum", 60, 6),
    ("potion", "İksir", "+1 can iksiri (en fazla 5)", 40, 0),
]


def xp_needed(level):
    return int(60 + level * 45 + level ** 2 * 6)


def upgrade_price(key, lv):
    base = next(u[3] for u in UPGRADES if u[0] == key)
    return int(base * (1.45 ** lv))


def new_profile():
    return dict(level=1, xp=0, gold=0, skill_pts=0, skills=[1, 0, 0, 0], up={"hp": 0, "atk": 0, "crit": 0, "energy": 0},
                potions=2, chapter=1, cleared=[], nightmare=False, best_combo=0, kills=0)
