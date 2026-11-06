# Sürüm Günlüğü

## v1.2.1 (2026-11-06)
**Neden:** APK telefonda açılır açılmaz kapanıyordu; Windows güncellemesi %0'da kayboluyordu.

- APK düzeltmesi: telefon için derlenen pygame'de çizim modülünün bir parçası (SIMD blit) eksikti, oyun ekrana hiçbir şey çizemeden kapanıyordu. Eksik dosyalar derlemeye eklendi (emülatör kaydıyla bulundu)
- Windows güncelleyici: her sürüm ayrı dosyaya iniyor, asıl exe yolu hatırlanıyor, hata olursa ekranda nedeni yazıyor

## v1.2.0 (2026-11-06)
**Neden:** Kapsamlı bir hack and slash modu istendi; APK telefonda açılır açılmaz kapanıyordu.

- YENİ MOD: Gölge Seferi (hack and slash). 4 kahraman, her birine 3 yetenek + 1 ultimate (sinematik giriş), kombo zinciri, ağır saldırı, zıplama saldırısı, kaçma
- 4 gölge düşman türü + elit düşmanlar, 3 bölüm, her bölümde 4 dalga ve boss (öfke evresi, meteor, çağırma, dalga saldırıları)
- İlerleme: XP ve seviye, seviyeyle açılan yetenekler, yetenek puanları (5 seviye), altınla can/güç/kritik/enerji geliştirmeleri, iksirler, Kabus zorluğu, kayıtlı ilerleme
- Kombo rütbesi (D'den SSS'ye), hasar sayıları, kritik vuruşlar, kılıç izleri, şok dalgaları, ganimet toplama
- Telefon için ayrı oyun kolu: saldırı / ağır / zıpla / kaç / 4 yetenek / iksir
- Hata olursa oyun artık sessizce kapanmıyor, hatayı ekranda gösteriyor
- APK açılış sorununu bulmak için emülatör testi eklendi

## v1.1.2 (2026-11-06)
**Neden:** Exe maç sırasında kapanıp yeniden açılıyordu; eski karakter ve arenalar istenmedi; ekrandaki tuş harfleri klavyedekiyle uyuşmuyordu.

- Güncelleme döngüsü düzeltildi: eski exe tamamen kapanmadan dosya değiştirilemiyor, oyun eski sürümle yeniden açılıp her seferinde tekrar güncellemeye çalışıyordu. Artık exe'nin kapanması bekleniyor, Türkçe karakterli klasör yolları destekleniyor, aynı sürüm ikinci kez denenmiyor
- Eski çizgi karakterler (Kaan, Zeyna, Demir) ve kodla çizilen arenalar kaldırıldı; yalnızca Daiki, Jax, Kaito, Titus ve 3 resimli arena kaldı
- Ekrandaki tuş göstergeleri gerçek klavye tuşlarını gösteriyor (K = Yumruk, L = Tekme; 2 oyunculuda 1. oyuncu F / G)
- APK derlemesi için Java 17 ayarı

## v1.1.1 (2026-11-06)
**Neden:** Oyun açılınca güncellemenin otomatik ve görünür şekilde yapılması istendi.

- Açılışta güncelleme kontrolü; yeni sürüm varsa menü kilitlenir, ilerleme çubuğuyla indirilir ve oyun yeni sürümle kendiliğinden yeniden açılır
- Eski exe kapanmadan kopyalanamazsa güncelleme betiği birkaç kez tekrar dener
- Eksik indirilen dosya kurulmaz

## v1.1.0 (2026-11-06)
**Neden:** Görseller zayıf bulundu, oyun takılıyordu, özel hareketler ekranda görünmüyordu ve telefon (APK) sürümü istendi.

- 4 yeni çizimli karakter: Daiki, Jax, Kaito, Titus (StreetFighter2D-Game reposundan, MIT lisansı; kaynak gösterildi)
- 3 yeni resimli arena: Ejder Kalesi (kıvılcımlar), Neon Çatı (yağmur), Gece Metrosu (yağmur)
- Takılma düzeltmeleri: müzik açılışta arka planda hazırlanıyor, ışık efektleri önbellekte tutuluyor, süper/nakavt duraklamaları kısaldı
- Dövüş sırasında ekranda özel hareket listesi (TAB ile aç/kapa), karakter seçiminde de komutlar görünüyor
- Yeni 4'lü zincir: Yumruk → Yumruk → Tekme → Tekme → özel hareket → Süper (Ustalık Kombosu)
- Windows'ta oklar kutu olarak görünüyordu: oklar artık çiziliyor, Türkçe karakterli yazı tipi oyuna gömüldü
- Android APK: solda yön çemberi, sağda Yumruk / Tekme, her özel hareket ve süper için tek dokunuşluk tuşlar
- Mini oyunlara dokunmatik kontrol, telefonda zorunlu güncelleme ekranı

## v1.0.0 (2026-11-06)
**Neden:** İlk sürüm. Klasik atari oyunlarını tek bir Kanatix uygulamasında toplamak için hazırlandı.

- Dövüş Arenası: 3 özgün karakter (Kaan, Zeyna, Demir), her birine 3 özel hareket ve 1 süper hareket
- Kombo sistemi: zincir saldırılar, özel harekete iptal, süper bitirici, kombo sayacı
- Saldırgan bilgisayar rakibi (Kolay / Normal / Zor)
- 3 arena: Boğaz Gün Batımı, Kapadokya Şafağı, Gece Çarşısı
- Mini oyunlar: Neon Yılan, Tuğla Kırıcı, Uzay İstilası, Neon Pong
- Kodla üretilen müzik ve ses efektleri
- Gamepad desteği, tam ekran (F11), rekor kaydı
- GitHub Releases üzerinden zorunlu otomatik güncelleme
