# G-022 Konuk 1. cilt: PDF'ten Arapça ve Türkçe metin çıkarımı (Musahhih)

Kaynak: Ahmed Avni Konuk, Fusûsu'l-Hikem Tercüme ve Şerhi, 1. cilt (TYEK çeviri yazı), PDF 892 s. (InDesign, metin katmanlı).
Girdi (telifli, değişmedi): `veri/kasa/envanter/konuk1/konuk1.pdf`. Çıktı (telifli): `veri/kasa/metin/konuk1/`.
Kod: `metin/konuk/cikar.py`, test: `metin/konuk/test_cikar.py` (`cd metin/konuk && python3 -m unittest`, 24 test, sentetik veri).
Bu dizine telifli metin konmaz; çıktı yalnız kasadadır.

## Kullanım
`python3 metin/konuk/cikar.py veri/kasa/envanter/konuk1/konuk1.pdf veri/kasa/metin/konuk1 [--ilk N --son M]`
Gerekli: pdfplumber (pdfminer.six), Pillow, `pdftoppm`, `tesseract` (yalnız metinsiz sayfalar için). Tüm cilt yaklaşık 1 dakika.

## Çıktılar
- `ham.jsonl`: blok başına `sayfa` (PDF), `basili_sayfa` (üst bilgiden), `sira`, `tur`, `dil`, `ham` (PDF metin akışı, hiç düzeltilmemiş; Arapçada görsel sıra ve U+FFFD dahil), `yazi`, `boyut`, `top`, `x0`.
- `temiz.jsonl`: aynı anahtarlar, `ham` yerine `metin` (mantıksal sıra, düzeltilmiş). Normalleştirme (hareke kaldırma, ﷺ'nin açık yazıya çevrilmesi vb.) yapılmaz; o katman `metin/normallestir.py`'nin işidir.
- `cid_sayim.json`: hemzeli elif glif (CID) sayımı; yeni, tanınmayan CID çıkarsa betik uyarı basar.
- Blok türleri: `arapca` (dil `ar` / `fa` sezgisel), `terceme`, `serh`, `baslik`, `baslik_sayfa` (üst bilgi: sayfa no + koşan başlık), `dipnot`, `isaret` (Arapça satıra giren "[6/45]" gibi bölüm işareti), `ocr_sayfa`.
- Toplam 12 690 blok (G-026 sonrası): 4 448 Arapça/Farsça satır, 3 084 şerh, 3 665 tercüme, 846 üst bilgi, 442 dipnot, 156 başlık, 44 işaret, 5 OCR sayfası.

## Metin katmanı bulguları (Arapça)
1. Arapça Scheherazade ile dizilmiş, harfler **görsel (soldan sağa) sırada** gelir; her satır parçası harf harf tersine çevrilerek mantıksal sıra elde edilir. Sunum biçimli harf yok (NFKC yine uygulanır; ﷺ ﷲ ﷵ gibi U+FDF0–FDFF kısaltma ligatürleri hariç, bunlar olduğu gibi korunur). Hareke, akışta tabanından önce geldiği için ters çevirmeyle tabanın ardına düşer; doğrulandı.
2. Hemzeli elif (أ إ آ) metinde **sıfır genişlikli hemze + ayrı elif tabanı** (U+FFFD ya da ا, lam-elif ligatüründe ا) olarak gelir; "�" bu tabandır. Kural: her hemzeli harf, akışta bitişik ve genişliği hemzenin x'ini kapsayan tabanı yutar. Yalnız kalan U+FFFD, ا olur. (İlk deneme olan "aynı x'teki FFFD'yi at" kuralı lam/fe/şın sonrasındaki hemzelerde `فاإن`, `الاأرض` gibi fazladan elif üretiyordu; düzeltildi.)
3. أَ ve أُ **tek glif**tir ve metin katmanında yalnız U+0623 görünür: fetha/damme düz metinden okunamaz. pdfminer kancasıyla glif CID'si alınır: s. 84'te sayfa görüntüsüne karşı doğrulanarak 1110 = أَ, 1111 = أُ, 913 = harekesiz أ; 914 = إ (kesre ayrı karakter), 912 = آ. Eşleme örnek sayfalarla doğrulandı, tüm ciltte başka CID çıkmadı.
4. `ي` ile `ء` arasına giren ayırıcı boşluk (شيء) silinir. Satır başına kaçan yetim hareke atılır. Tatvil (ـ) çıkarılır.
5. Metin Konuk'un Arapçasıdır; yazım Persian ک (U+06A9) gibi font seçimlerini içerebilir (örn. أَکُنْ). Bunlara dokunulmadı (özgün yazım korunur); karşılaştırma katmanında katlanmalıdır.
6. Satır sonu çıkarımı: Arapça satırlar beyit hemistişleri ve satır içi "[x/y]" işaretlerinde ayrı blok olur; sıra yukarıdan aşağı, aynı satırda sağdan sola.

## Türkçe katmanı
Mantıksal sırada gelir, sorunsuz. `tur` sezgisel ve yazı tipinden gelir: Nimbus Sans = `terceme` (Fusûs metninin çevirisi), "Ya'ni:/Tercüme:" ile başlayan paragraf = `terceme`, Garamond = `serh`, kalın = `baslik`. Üst indis rakam (boy < 8) `[^n]` olur. Satır sonu tire, devamı küçük harfle başlıyorsa birleştirilir (kesin değil: "hikmet-/i" gibi gerçek tireli bileşikler yanlış birleşebilir). Dipnot: sayfadaki ayraç çizgisinin altı.

## Elle kontrol (Arapça blok)
Yöntem: sayfa görüntüsü (130 dpi tam sayfa, 300+ dpi kırpım) çıktı satırıyla karşılaştırıldı; tek okuyucu, bağımsız mukabele yok.
Sayfalar (PDF): 84, 144, 176, 304, 500, 701 (6 sayfa; Arapça, Farsça beyit, âyet, hadis, satır içi işaretler). Toplam 58 satır, 3 255 karakter, 521 sözcük.
- Çıktı yöntemi ilk kurulduğunda bulunan hatalar (hepsi düzeltildi): fazladan elif (`الاأرض`, `فاإنَّ`, `نشاأة`, `الْاأَشْيَاءَ` türü; s. 84, 176, 304'te toplam yaklaşık 8 sözcük), أَ/أُ'da kayıp fetha/damme (s. 84'te 6 sözcük), `الشي ءِ` (1), satır başında yetim fetha (1).
- Son kurallarla aynı 6 sayfada **kalan hata: 0 / 58 satır** (görülebilen harf, hamze, elif, sözcük sırası, harekede). Küçük baskıda hareke teyidi sınırlıdır: bu yüzden "0 / 3 255 karakter" tek okuyuculu gözlemdir; gerçek karakter hata oranı için "gözle ≤ %1" okunmalıdır.
- Tüm cilt otomatik değişmez kontrolleri: U+FFFD 0, elif + hemzeli elif yan yana 0, boşluk + yalın hemze 0, tatvil 0, başta hareke 0. (Bu kontroller doğruluk değil, tutarlılık gösterir.)

## Bilinen sorunlar
- PDF s. 4-7, 9 (Takdim vb.) metin katmansız: Tesseract (`eng`; `tur` modeli kurulu değil) ile okundu, `tur: ocr_sayfa`. Türkçe aksan ve harfler (ı ş ğ ü) kaybolur ("kiiltiir"); **güvenilmez, Türkçe model gelince yeniden okunmalı**. S. 8, 24, 122, 142, 464, 600, 654, 750, 892 boş sayfadır (mürekkep yok), çıktıda yer almaz.
- Ön bölümde (s. 1-25) ayraçsız kutu notu (s. 17) satır satır paragraf olur; dipnot ayrımı yalnız ayraç çizgisi olan sayfalarda çalışır.
- Arapça içeren Türkçe paragraf (satır içi Arapça) tek blok olmaz: blok sırası Türkçe | Arapça | Türkçe olarak okuma sırasındadır (G-026'dan sonra doğru sırada); birleştirme tüketicinin (hat.py) işidir.
- Dipnottaki Arapça `dipnot` bloğunun içinde `{ar: ...}` olarak durur (G-026); dipnot varyantını pasaja bağlamak hat.py'nin işidir (denetim Ö-2).
- `dil` ayrımı (ar/fa) işlev sözcüğü sezgisidir; kısa Farsça mısralar `ar` kalabilir.
- Arapçada çok kısa blok (tek harf, ör. "m") sayfa üzerindeki yazı tipi artığı olabilir (p. 98); elle kontrol edilmedi.
- Harekenin metin katmanı sağlam kabul edildi (PDF'nin kendisi); yalnız أَ/أُ özel işlendi. Başka glif-birleşik hareke (örn. ligatür içinde) görsel olarak taranmadı; CID envanteri her 13. sayfadan örneklemle çıkarıldı (tam cilt koşusunda yeni hemzeli elif CID'si görülmedi).

## G-026 düzeltmesi (Denetim G-003: Ö-1, Ö-2, K-1)
Neden: Türkçe parçalar `top`'a göre sıralanıyor, Arapça ayrıca `top/6`'ya göre sıralanıyor ve Arapça satırın hemen altındaki Türkçe satır
(`any(ar_top ...)` kuralı) her zaman yeni paragraf sayılıyordu. Satır içi Arapçalı bir satırda "Türkçe | Arapça | Türkçe" parçaları (üst
üste 1-1,5 pt fark) yanlış sıraya düşüyor, satır sonu tire yanlış parçayla birleşiyordu (s. 177, 194, 214, 216, 220).
Yöntem: parçalar `top` ile görsel satırlara kümelenir (tolerans 6 pt, satır aralığı >= 14 pt); karışık satırda Türkçe parçalar x0'a göre soldan sağa,
bitişik Arapça/[x/y] parçaları kendi aralarında sağdan sola; yalnız Arapça satırda eskisi gibi sağdan sola. Arapçalı satırı izleyen
Türkçe satır artık otomatik yeni paragraf olmaz (girinti/yazı tipi/aralık kuralları geçerli). Dipnot ayracının altındaki Arapça (Ö-2) dipnot
paragrafına `{ar: ...}` olarak katılır, gövdede `arapca` bloğu olmaz. K-1: U+FDF0–FDFF aralığı NFKC dışında bırakıldı (ham/temiz katmanda ﷺ aynen).
Önce/sonra (tüm cilt, 892 s.): temiz.jsonl 13 485 -> 12 690 blok; şerh 3 821 -> 3 084 (yanlış bölünmüş paragraflar birleşti), tercüme 3 670 -> 3 665,
dipnot 445 -> 442 (dipnota giren Arapça satırlar yüzünden birleşen dipnotlar), arapca 4 498 -> 4 448 (50 satır dipnota geçti; dipnotta 25 blokta
35 `{ar: ...}` parçası, gövdede 0), isaret 44 -> 44 (küme aynı). 508 sayfada en az bir blok değişti. Karışık (Türkçe+Arapça) görsel satır: 1 329,
502 sayfada. U+FDFA: 0 -> 31 blok (açık yazı "صلى الله عليه وسلم" 31 -> 0); U+FDF5 (ﷵ) vb. de korunur.
Elle kontrol: s. 177, 194, 214, 216, 220 sayfa görüntüsüyle satır satır karşılaştırıldı (Türkçe parçalar ve Arapça sırası birebir); s. 196 dipnot 110/111 `dipnot`ta, gövdede yok.
Önceki sürüm yedeği çalışma dizininde tutulmadı (yeniden üretim 1 dk).

## 2. cilt (G-033): TYEK 2024, 2. baskı
Girdi (telifli): `veri/kasa/envanter/yek-827-fusus-konuk/cilt2.pdf` (888 s., E-007). Çıktı (telifli): `veri/kasa/metin/konuk2/` (ham.jsonl, temiz.jsonl, cid_sayim.json).
Komut: `python3 metin/konuk/cikar.py <cilt2.pdf> veri/kasa/metin/konuk2 --sep-min 100 --indeks-ilk 771` (1. cilt komutu değişmedi; yeni seçeneklerin varsayılanı eski davranıştır).
**1. cilt çıktısı bayt bayt aynı** (kod değişikliklerinden sonra konuk1 yeniden üretildi, `cmp` ham+temiz: aynı). Bu kontrol, yazı tipi eşitliğinde (`max(set(...))`) süreçten sürece değişen eski bir belirsizliği ortaya çıkardı (3 blokta `tur`/`yazi` bazen farklı); eşitlikte artık italik olmayan, sonra sıralı ilk yazı tipi seçilir (referans çıktıyla uyumlu, PYTHONHASHSEED 1-4'ten bağımsız).
Yazı tipleri 1. ciltle aynı (Scheherazade/Suleymaniye Arapça-Farsça, AGaramond, Nimbus Sans). Farklar ve uyarlamalar:
1. **Bölüm işareti üst indisli: "[25¹/4]"**. Kod üst indis rakamı dipnot çağrısına çeviriyordu ("[25[^1]/4]", 192 yerde yanlış dipnot çağrısı, s. 411 vd.). Artık rakamdan sonra "/" geliyorsa Unicode üst indis olarak kalır: `[25¹/4]` (191 işaret; 1. ciltte böyle işaret yok). Dipnot çağrıları: 272, hepsinin dipnotu var.
2. **Dipnot ayracı**: dipnotu sayfanın çoğunu kaplayan sayfalarda (s. 394: ayraç top=117; s. 707: top=225) ayraç 400'ün üstünde kalıyordu; `--sep-min 100` ile yakalanır (cilt 2'de ayraç olan tek bu iki sayfa bu aralıkta, yanlış pozitif yok). Dipnot 284 blok; 4 dipnot çağrısız (s. 251/506, 304/523: varyant çağrısı Arapça içinde ya da yok; 592/19 ve 665/2398: önceki sayfadan devam eden dipnot).
3. **Dizin sayfaları (s. 771 sonrası)**: üst indis rakamlar dizinde sayfa göndermesidir (kavram/kişi dizinleri; "[^1348]" yanlışı); `--indeks-ilk 771` ile düz rakam kalır.
4. **UYARI, okunamayan sayfalar: s. 777-782 (Hadis dizini) ve s. 858.** Bu sayfalar TraditionalNaskh yazı tipiyle dizilmiş ve metin katmanı eksik (harfler "(cid:N)" ya da İbrani yer tutucu). Tahmin edilmedi: okunamayan glifler `⟨?⟩` (188 blok). Rakamlar ve bağlı hareke okunur. Hemzeli elif CID'leri (أ 200, إ 204) bu yazı tipinde doğrulanmadı; bu sayfalarda Arapça harekeye güvenilmez. Bu dizin sayfaları çeviri çiftine girmemeli; gerekirse OCR (Arapça Tesseract modeli kurulu değil) ya da elle.
5. Yeni CID 198 = آ (Suleymaniye, s. 596, görüntüyle doğrulandı: "از آن"); `BILINEN_ALEF_CID`'e eklendi. Arapçadaki rakam dizisi (görsel sırada) ters çevirme sonrası düzeltilir (yalnız Naskh dizin sayfalarında rakam var).
6. Üst bilgi: çift sayfalarda sayfa no, çubuk ve başlık üst üste biner; `baslik_sayfa` "1262KELİME-İ … │" gibi (boşluksuz) çıkabilir; basılı sayfa numarası yine okunur. Düzeltilmedi (çevirilmeyen üst bilgi).
Sayılar (G-033 ilk çıktısı; G-036 sonrası aşağıda: 12 065 blok; 12 103 blok, 880 sayfa; s. 1-7 ön bölüm, boş sayfa yok sayıldı): 4 355 arapca (3 849 ar + 314 fa dışında 192 dizin bloğu), 3 734 terceme, 2 663 serh, 284 dipnot, 854 üst bilgi, 158 başlık, 55 isaret. U+FDFA 47 blok (açık yazı 0); `{ar:` yalnız dipnotta (21 parça), gövdede 0.
Tutarlılık kontrolleri (dizin sayfaları hariç, 4 163 Arapça blok): U+FFFD 0, tatvil 0, elif+hemzeli elif yan yana 0, boşluk+yalın hemze 0, başta hareke 0, `⟨?⟩` 0.
Elle kontrol (sayfa görüntüsüne karşı, tek okuyucu): s. 200 (iki satır içi Arapça "إذْ …", tercüme, [18/3]), 394 (uzun dipnot 553, ayet), 400 (Fusûs Arapçası, ayetler), 411 ([25¹/3], dipnot 563), 596 (Farsça beyit dipnotu, آ), 700 (karışık ayet satırı + Farsça beyit + dipnot 700). Türkçe parçalar ve Arapça sırası birebir; Arapça harekede küçük baskı sınırı 1. ciltteki gibi (sözcük düzeyinde teyit).
Not: Türkçe taraf Osmanlıca metnin çeviri yazısıdır (E-007).

### G-036 düzeltmesi (Denetim G-034: Ö-1, K-2)
Neden: 2. ciltte Arapça yazı tipiyle (Scheherazade, 8,7 pt) dizilmiş küçük rakamlar iki yerde Arapça sanılıyordu.
(a) "[25¹/47]" bölüm işaretinin üst indisi: işaret "[25" (şerh), "1" (arapca), "/47]" (şerh) diye üç bloğa bölünüyor, Arapça seriyi kırıyordu (s. 416-612, 19 yer; fass 11-12).
(b) Arapça satıra yapışan dipnot çağrısı ("…كشفيًّا،523", s. 304; "…البلاءِ.506", s. 251): Arapça metne rakam giriyordu.
Çözüm (`_arapca_rakamlari_ayir`): Arapça yazı tipli ve < 10 pt rakam grubu "/" ile devam ediyor ve önünde rakam varsa Türkçe üst indis olur, işaret bütün kalır (`isaret` bloğu, "[25¹/47]"); aksi halde metinden çıkarılır ve en yakın Arapça bloğa `dipnot_ref` alanı (liste, yalnız varsa) olarak bağlanır.
Önce/sonra (cilt 2): parçalı işaret parçası 38 -> 0; tek parça `isaret` bloğu +19 (74 toplam); toplam blok 12 103 -> 12 065; Arapça bloklarda rakam (dizin s. 777-782, 858 hariç) 21 -> 0 (19 işaret + 2 dipnot çağrısı); `dipnot_ref`: s. 251 ["506"], s. 304 ["523"]. 1. ciltte Arapça yazı tipli rakam yok: çıktı bayt bayt aynı (PYTHONHASHSEED=6 ile yeniden üretilip `cmp` ham+temiz). 26 test.
