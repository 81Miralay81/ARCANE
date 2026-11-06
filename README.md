# Kanatix Arcade

![Kanatix](assets/icon.png)

Retro atari salonu derlemesi. Tek bir `.exe` dosyası, kurulum gerektirmez.
Tüm karakterler, grafikler, müzikler ve sesler bu projeye özgüdür ve kodla üretilir. Dışarıdan alınmış hiçbir oyun dosyası kullanılmaz.

## Oyunlar

| Oyun | Açıklama |
|------|----------|
| **Dövüş Arenası** | 3 özgün dövüşçü, özel hareketler, süper hareketler, kombolar, 3 arena. 1P (bilgisayara karşı) veya 2P |
| **Neon Yılan** | Klasik yılan oyunu, altın elmalar |
| **Tuğla Kırıcı** | Seviyeler ve güçlendirmeler (geniş raket, çoklu top, ekstra can) |
| **Uzay İstilası** | Dalga dalga gelen uzaylılar, kalkanlar, bonus ana gemi |
| **Neon Pong** | Bilgisayara ya da arkadaşına karşı |

## Dövüş Arenası kontrolleri

| | 1. Oyuncu | 2. Oyuncu |
|--|--|--|
| Hareket | W A S D | Yön tuşları |
| Yumruk | F | K (veya Numpad 1) |
| Tekme | G | L (veya Numpad 2) |

Tek oyunculu modda iki tuş takımı da 1. oyuncuyu kontrol eder. Gamepad de desteklenir.

- **Blok:** Geri yöne bas. Alçak saldırılara karşı **↓ + geri** bas.
- **ESC:** Duraklatma menüsünü açar. Menüde tüm karakterlerin **hareket listesi** var.
- **F11:** Tam ekran.

### Özel hareketler (karakter sağa bakarken)

**KAAN (Anadolu Ateşi):** dengeli dövüşçü
- Ateş Topu: ↓ ↘ → + Yumruk
- Kartal Yumruğu: → ↓ ↘ + Yumruk
- Kasırga Tekmesi: ↓ ↙ ← + Tekme
- **SÜPER: Alev Fırtınası:** ↓ ↘ → ↓ ↘ → + Yumruk

**ZEYNA (Rüzgârın Kızı):** hızlı, hava hâkimi
- Rüzgâr Hançeri: ↓ ↘ → + Yumruk
- Şimşek Tekmesi: ↓ ↘ → + Tekme
- Ay Takla Tekmesi: → ↓ ↘ + Tekme
- **SÜPER: Fırtına Dansı:** ↓ ↘ → ↓ ↘ → + Tekme

**DEMİR (Dağların Pehlivanı):** yavaş ama çok güçlü
- Deprem (yerden giden şok dalgası): ↓ ↘ → + Yumruk
- Boğa Hücumu: ↓ ↙ ← + Yumruk
- Gök Gürültüsü (zıplayıp yere çakılma): → ↓ ↘ + Tekme
- **SÜPER: Dağ Devrilmesi:** ↓ ↘ → ↓ ↘ → + Yumruk

### Kombolar
- **Zincir:** Yumruk → Yumruk → Tekme (3 vuruş, yere serer)
- **Alçak zincir:** ↓+Yumruk → ↓+Yumruk → ↓+Tekme (süpürme)
- **İptal kombosu:** Yumruk → Yumruk → hemen bir özel hareket komutu
- **Süper bitirici:** Özel hareket isabet edince süper komutu (süper barı doluysa)
- **Hava kombosu:** Zıpla + Tekme → yere inince Yumruk → Yumruk → özel hareket

Süper barı vurdukça ve vuruş yedikçe dolar. Her dolu bölüm bir süper hareket hakkı verir.

## Çalıştırma (kaynak koddan)

```bash
pip install -r requirements.txt
python main.py
```

## Windows .exe oluşturma

**Kendi bilgisayarında:** `build_exe.bat` dosyasına çift tıkla. Exe `dist\KanatixArcade.exe` konumunda oluşur.

**GitHub üzerinden (otomatik):** `main` dalına her gönderimde (push) GitHub Actions exe'yi derler. Exe, `engine/core.py` içindeki `VERSION` numarasıyla **Releases** sayfasına yüklenir (örn. `v1.0.0`). Elle başlatmak için **Actions → Build EXE → Run workflow** seçeneğini kullan.

## Otomatik güncelleme

Exe her açılışta GitHub Releases'taki son sürümü kontrol eder. Daha yeni bir sürüm varsa onu indirir ve kendini yeniden başlatır (zorunlu güncelleme).
Repo adı `engine/updater.py` içindeki `GITHUB_REPO` satırında yazılıdır. Repo **private** olursa GitHub sürüm bilgisini dışarıya vermez. Bu durumda güncelleme kontrolü sessizce atlanır.

Yeni sürüm çıkarmak için:
1. `engine/core.py` içindeki `VERSION` değerini artır (örn. `1.0.1`)
2. `CHANGELOG.md` dosyasına ne değiştiğini ve nedenini yaz
3. `main` dalına gönder (push). Exe derlenir, yeni sürüm Releases'a çıkar ve açık olan oyunlar kendini günceller.

## Ayarlar ve rekorlar

`%APPDATA%\KanatixArcade\kayit.json` dosyasında saklanır.

## Proje yapısı

```
main.py                  Başlatıcı
engine/                  Pencere, menü, ses sentezi, güncelleme
games/fighter/           Dövüş oyunu (karakterler, iskelet animasyon, arenalar, yapay zekâ)
games/*.py               Mini oyunlar
assets/                  İkon
```
