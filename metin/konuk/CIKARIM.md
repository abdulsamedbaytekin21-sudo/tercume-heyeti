# G-022 Konuk 1. cilt: PDF'ten Arapça ve Türkçe metin çıkarımı (Musahhih)

Kaynak: Ahmed Avni Konuk, Fusûsu'l-Hikem Tercüme ve Şerhi, 1. cilt (TYEK çeviri yazı), PDF 892 s. (InDesign, metin katmanlı).
Girdi (telifli, değişmedi): `veri/kasa/envanter/konuk1/konuk1.pdf`. Çıktı (telifli): `veri/kasa/metin/konuk1/`.
Kod: `metin/konuk/cikar.py`, test: `metin/konuk/test_cikar.py` (`cd metin/konuk && python3 -m unittest`, 15 test, sentetik veri).
Bu dizine telifli metin konmaz; çıktı yalnız kasadadır.

## Kullanım
`python3 metin/konuk/cikar.py veri/kasa/envanter/konuk1/konuk1.pdf veri/kasa/metin/konuk1 [--ilk N --son M]`
Gerekli: pdfplumber (pdfminer.six), Pillow, `pdftoppm`, `tesseract` (yalnız metinsiz sayfalar için). Tüm cilt yaklaşık 1 dakika.

## Çıktılar
- `ham.jsonl`: blok başına `sayfa` (PDF), `basili_sayfa` (üst bilgiden), `sira`, `tur`, `dil`, `ham` (PDF metin akışı, hiç düzeltilmemiş; Arapçada görsel sıra ve U+FFFD dahil), `yazi`, `boyut`, `top`, `x0`.
- `temiz.jsonl`: aynı anahtarlar, `ham` yerine `metin` (mantıksal sıra, düzeltilmiş). Normalleştirme (hareke kaldırma vb.) yapılmaz; o katman `metin/normallestir.py`'nin işidir.
- `cid_sayim.json`: hemzeli elif glif (CID) sayımı; yeni, tanınmayan CID çıkarsa betik uyarı basar.
- Blok türleri: `arapca` (dil `ar` / `fa` sezgisel), `terceme`, `serh`, `baslik`, `baslik_sayfa` (üst bilgi: sayfa no + koşan başlık), `dipnot`, `isaret` (Arapça satıra giren "[6/45]" gibi bölüm işareti), `ocr_sayfa`.
- Toplam 13 485 blok: 4 498 Arapça/Farsça satır, 3 821 şerh, 3 670 tercüme, 846 üst bilgi, 445 dipnot, 156 başlık, 44 işaret, 5 OCR sayfası.

## Metin katmanı bulguları (Arapça)
1. Arapça Scheherazade ile dizilmiş, harfler **görsel (soldan sağa) sırada** gelir; her satır parçası harf harf tersine çevrilerek mantıksal sıra elde edilir. Sunum biçimli harf yok (NFKC yine uygulanır). Hareke, akışta tabanından önce geldiği için ters çevirmeyle tabanın ardına düşer; doğrulandı.
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
- Arapça içeren Türkçe paragraf (satır içi Arapça) bloğa Arapça satırın üstünden ve altından ayrı iki paragraf olarak girer; tek paragraf olarak birleştirilmez (Mukabeleci bilsin).
- `dil` ayrımı (ar/fa) işlev sözcüğü sezgisidir; kısa Farsça mısralar `ar` kalabilir.
- Arapçada çok kısa blok (tek harf, ör. "m") sayfa üzerindeki yazı tipi artığı olabilir (p. 98); elle kontrol edilmedi.
- Harekenin metin katmanı sağlam kabul edildi (PDF'nin kendisi); yalnız أَ/أُ özel işlendi. Başka glif-birleşik hareke (örn. ligatür içinde) görsel olarak taranmadı; CID envanteri her 13. sayfadan örneklemle çıkarıldı (tam cilt koşusunda yeni hemzeli elif CID'si görülmedi).
