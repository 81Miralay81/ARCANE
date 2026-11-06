"""Ses efektleri ve müzik: dışarıdan dosya gerekmez, hepsi kodla üretilir."""
import array
import math
import random

import pygame

RATE = 22050


def _env(i, n, attack=0.01, release=0.3):
    t = i / n
    a = min(1.0, t / attack) if attack > 0 else 1.0
    r = min(1.0, (1 - t) / release) if release > 0 else 1.0
    return a * r


def synth(freq=440, dur=0.2, wave="square", vol=0.5, slide=0.0, noise=0.0, attack=0.005, release=0.5, vibrato=0.0):
    n = int(RATE * dur)
    out = array.array("h")
    phase = 0.0
    rnd = random.Random(int(freq * 1000 + dur * 100))
    last_noise = 0.0
    for i in range(n):
        t = i / RATE
        f = max(20.0, freq + slide * t + (math.sin(t * 40) * vibrato))
        phase += f / RATE
        p = phase % 1.0
        if wave == "square":
            v = 1.0 if p < 0.5 else -1.0
        elif wave == "saw":
            v = 2 * p - 1
        elif wave == "tri":
            v = 4 * abs(p - 0.5) - 1
        else:
            v = math.sin(phase * math.tau)
        if noise:
            if i % 2 == 0:
                last_noise = rnd.uniform(-1, 1)
            v = v * (1 - noise) + last_noise * noise
        v *= _env(i, n, attack / dur if dur else 0, release) * vol
        s = int(max(-1.0, min(1.0, v)) * 32000)
        out.append(s)
        out.append(s)
    return out


def mix(*arrs):
    n = max(len(a) for a in arrs)
    out = array.array("h", [0]) * n
    for a in arrs:
        for i, v in enumerate(a):
            out[i] = max(-32767, min(32767, out[i] + v))
    return out


def concat(*arrs):
    out = array.array("h")
    for a in arrs:
        out.extend(a)
    return out


def note_freq(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def make_music(tempo=132, bars=4, bass_line=None, lead=None, drums=True, vol=0.22):
    """Basit chiptune döngüsü: bas + melodi + davul."""
    step = 60 / tempo / 4  # 16'lık nota
    steps = bars * 16
    n_step = int(RATE * step)
    total = steps * n_step
    buf = array.array("h", [0]) * (total * 2)

    def add(start_step, arr):
        o = start_step * n_step * 2
        for i, v in enumerate(arr):
            j = o + i
            if j >= len(buf):
                break
            buf[j] = max(-32767, min(32767, buf[j] + v))

    for s in range(steps):
        if bass_line:
            nn = bass_line[(s // 2) % len(bass_line)]
            if nn and s % 2 == 0:
                add(s, synth(note_freq(nn), step * 1.9, "tri", vol * 1.3, release=0.4))
        if lead:
            nn = lead[s % len(lead)]
            if nn:
                add(s, synth(note_freq(nn), step * 1.6, "square", vol * 0.45, release=0.6, vibrato=3))
        if drums:
            if s % 8 == 0:
                add(s, synth(110, 0.12, "sine", vol * 2.2, slide=-500, release=0.8))
            if s % 8 == 4:
                add(s, synth(200, 0.10, "sine", vol * 1.2, noise=0.85, release=0.9))
            if s % 2 == 1:
                add(s, synth(6000, 0.03, "sine", vol * 0.35, noise=1.0, release=0.9))
    return buf


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.ok = False
        self.sounds = {}
        self.music = {}
        self.music_channel = None
        self.current = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 2, 512)
            init = pygame.mixer.get_init()
            self.rate = init[0] if init else RATE
            self.ok = True
            pygame.mixer.set_num_channels(24)
            self._build()
            self.prebuild_music()
        except Exception:
            self.ok = False

    def _snd(self, arr):
        return pygame.mixer.Sound(buffer=arr.tobytes())

    def _build(self):
        S = self._snd
        self.sounds = {
            "menu": S(synth(660, 0.06, "square", 0.25, release=0.6)),
            "select": S(concat(synth(660, 0.06, "square", 0.3), synth(990, 0.10, "square", 0.3))),
            "back": S(synth(330, 0.10, "square", 0.25, slide=-600)),
            "whoosh": S(synth(800, 0.12, "sine", 0.25, noise=0.9, slide=-2500, release=0.9)),
            "hit_l": S(mix(synth(180, 0.10, "square", 0.45, noise=0.7, slide=-600), synth(90, 0.12, "sine", 0.6, slide=-200))),
            "hit_h": S(mix(synth(140, 0.20, "square", 0.55, noise=0.75, slide=-500), synth(60, 0.25, "sine", 0.8, slide=-80))),
            "block": S(mix(synth(1200, 0.06, "square", 0.25, noise=0.5), synth(500, 0.08, "tri", 0.3))),
            "fireball": S(synth(300, 0.45, "saw", 0.35, noise=0.55, slide=-300, release=0.7)),
            "special": S(concat(synth(400, 0.05, "square", 0.3), synth(800, 0.18, "saw", 0.3, slide=900))),
            "super": S(mix(synth(200, 0.9, "saw", 0.35, slide=600, release=0.6), synth(100, 0.9, "square", 0.25, noise=0.3, slide=200))),
            "ko": S(mix(synth(90, 1.1, "square", 0.5, noise=0.6, slide=-60, release=0.8), synth(45, 1.1, "sine", 0.7))),
            "land": S(synth(120, 0.08, "sine", 0.4, noise=0.6, slide=-200)),
            "jump": S(synth(300, 0.09, "square", 0.18, slide=1400)),
            "round": S(concat(synth(523, 0.12, "square", 0.3), synth(659, 0.12, "square", 0.3), synth(784, 0.25, "square", 0.3))),
            "fight": S(mix(synth(392, 0.5, "saw", 0.3, vibrato=8), synth(196, 0.5, "square", 0.3))),
            "coin": S(concat(synth(988, 0.06, "square", 0.3), synth(1319, 0.18, "square", 0.3))),
            "eat": S(synth(520, 0.07, "square", 0.3, slide=1800)),
            "boom": S(synth(80, 0.5, "square", 0.55, noise=0.9, slide=-60, release=0.9)),
            "laser": S(synth(1400, 0.12, "square", 0.22, slide=-6000)),
            "bounce": S(synth(440, 0.04, "square", 0.25)),
            "brick": S(synth(700, 0.05, "tri", 0.35, noise=0.2)),
            "lose": S(concat(synth(392, 0.15, "square", 0.3), synth(330, 0.15, "square", 0.3), synth(262, 0.4, "square", 0.3, slide=-80))),
            "win": S(concat(*[synth(note_freq(n), 0.11, "square", 0.3) for n in (72, 76, 79, 84, 79, 84)])),
            "powerup": S(concat(*[synth(note_freq(n), 0.05, "square", 0.25) for n in (64, 68, 71, 76, 80, 83)])),
        }
        self._music_specs = {
            "menu": dict(tempo=118, bars=4, bass_line=[45, 45, 52, 52, 48, 48, 50, 50, 45, 45, 52, 52, 53, 53, 52, 50],
                         lead=[69, 0, 72, 0, 76, 0, 74, 72, 0, 0, 69, 0, 71, 72, 0, 0,
                               69, 0, 72, 0, 76, 0, 79, 77, 0, 0, 76, 0, 74, 0, 72, 0], drums=True),
            "fight": dict(tempo=150, bars=4, bass_line=[40, 40, 52, 40, 43, 43, 55, 43, 38, 38, 50, 38, 45, 47, 48, 47],
                          lead=[64, 0, 67, 64, 0, 69, 0, 67, 64, 0, 62, 0, 64, 0, 0, 0,
                                64, 0, 67, 64, 0, 71, 0, 72, 71, 0, 69, 0, 67, 0, 69, 0], drums=True),
            "game": dict(tempo=128, bars=4, bass_line=[48, 48, 55, 55, 53, 53, 50, 50, 48, 48, 55, 55, 57, 55, 53, 52],
                         lead=[72, 0, 76, 79, 0, 76, 0, 72, 74, 0, 77, 81, 0, 79, 77, 0,
                               72, 0, 76, 79, 0, 84, 0, 83, 81, 0, 79, 0, 77, 76, 74, 0], drums=True),
        }

    def play(self, name, vol=1.0):
        if not self.ok:
            return
        s = self.sounds.get(name)
        if s:
            ch = s.play()
            if ch:
                ch.set_volume(self.settings.get("volume", 0.7) * vol)

    def prebuild_music(self):
        """Müzikleri arka planda önceden üret (oyun içinde takılma olmasın)."""
        import threading

        def work():
            for name, spec in self._music_specs.items():
                if name not in self.music:
                    try:
                        self.music[name] = self._snd(make_music(**spec))
                    except Exception:
                        pass
                    if self._pending == name:
                        self._pending = None
                        self.play_music(name)
        if self.ok:
            threading.Thread(target=work, daemon=True).start()

    _pending = None

    def play_music(self, name):
        if not self.ok or self.current == name:
            return
        self.stop_music()
        if name not in self.music:
            # henüz hazır değil: hazır olunca çalacak
            self._pending = name
            return
        self.current = name
        self.music_channel = self.music[name].play(loops=-1)
        if self.music_channel:
            self.music_channel.set_volume(self.settings.get("music", 0.5))

    def stop_music(self):
        if self.music_channel:
            self.music_channel.stop()
        self.music_channel = None
        self.current = None

    def refresh_volume(self):
        if self.music_channel:
            self.music_channel.set_volume(self.settings.get("music", 0.5))
