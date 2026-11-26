# veri/ham/KAYNAKLAR.md (G-016, kutuphaneci, 2026-11-26, v1)

DURUM (v3): Keşif TAMAM. 5/5 öncelikli öğe indirildi (bölüm 'İNDİRİLENLER' ve 'v3'). 'ENGEL (v2)' bölümü artık TARİHİDİR: o alan adları sonradan izinlendi ve indirme başarılı oldu. Henüz denenmeyenler: AAlexandrina-151950, -188000.
Aşağıdaki sha1 değerleri archive.org metadata API'sinin bildirdiği değerlerdir (indirilen dosyadan hesaplanmadı); indirme sonrası sha256 hesaplanıp eklenecek.
Telif gerekçesi sütunu bir ön değerlendirmedir, hukuki hüküm değildir: baskı yılı eski (<=1938 tarihli) ve çağdaş tahkik/editör emeği görünmüyor; eserlerin müellifleri 8.-12./14.-18. yüzyıl. Tarihler archive.org künyesinden, DOĞRULANMADI (sayfa görüntüsünden teyit yok).

## ENGEL (ağ)
archive.org/advancedsearch.php ve /metadata/ çalışıyor. /download/ ise şu alt alan adlarına yönleniyor ve proxy HTTP 403 (connect_rejected) veriyor:
- dn711002.ca.archive.org (AAlexandrina-060267 için)
- dn721900.ca.archive.org (AAlexandrina-146529 için)
- dn760109.eu.archive.org (ar117myst97 için)
- ia801506.us.archive.org (doğrudan erişim denemesi de 403)
Yönlendirme alan adı öğeye göre değişiyor (dn*.ca/eu/us.archive.org, ia*.us.archive.org). Gerekli: `*.archive.org` joker izni. Zorlanmadı.

## Adaylar (hepsi archive.org; sayfa sayısı metadata'da yok = doğrulanmadı)
Dosya adı biçimi: <kimlik>/<ad>.pdf (+ _djvu.txt OCR). Boyut bayt, sha1 archive.org'dan.

### A. Fusûsu'l-hikem
| Kimlik | Künye (archive.org) | Telif-dışı ön gerekçe | Dosyalar (sha1) | Not |
|---|---|---|---|---|
| AAlexandrina-060267 | "شرح فصوص الحكم", müellif alanı İbnü'l-Arabî, d.n., 1300 [1883], yer/yayıncı yok | 1883 baskı; müellif 638/1240 | pdf 100716073 B 08c16e8d07b2de1a8572b6b917d5fdf44a052983; djvu.txt 1216854 B 9268298c0304cbfb4b7de83edac398e573db5c47 | Başlık "şerh"; matn mı şerh mi doğrulanmadı. İndirilip ilk sayfalar görülmeli. Öncelikli. |
| AAlexandrina-170380 | Fusûs, "el-Mevsûm bi-ismi'l-Kadem" Hintçe tercümeli, Matba' Ahmedî, 1311 [1894] | 1894 baskı | pdf 145829164 B 3285d043916ab2e8277a601f00a78390e0d9ca33; djvu.txt 436847 B 1267799dc7698edc6aaad736c46b3b5c9413ec08 | Arapça metin + Hint dili (Urdu/Farsça?) tercüme/şerh; doğrulanmadı. |
| AAlexandrina-085017 / 170343 / 143329 | Kayserî şerhi, Tahran/Bombay taş baskıları 1299-1300 / 1882 | Kayserî 751/1350; 1880'ler baskı | indirilmeden sha1 alınmadı (metadata sorgulanmadı) | Şerh; matn şerh içinde gömülü. İkincil aday. |
| AAlexandrina-105985 / 150622 / 127456 / 141527 | Bâlî Efendi şerhi, el-Matba'atü'n-Nefîse el-Osmâniyye, 1309 | 1309 (1891/92) baskı | sha1 alınmadı | Şerh (4 kopya). Matn içeriyor olabilir; İstanbul 1304 değil. |
| AAlexandrina-066179 | Kâşânî şerhi, el-Matba'atü'l-Meymeniyye, 1321 | 1321 (1903) baskı | sha1 alınmadı | Şerh. |
| ar117myst97 | "فصوص الحكم" İbnü'l-Arabî, yayın bilgisi YOK | BELİRSİZ (modern dijital metin olabilir) | epub 886455 B 6d6009a5...; pdf 4215997 B 15f2eb72dd24beee533a38b6d4a73d6ce9868bf8 | Kaynak/baskı yok; telif-dışı gerekçesi kurulamadı; İNDİRİLMEMELİ. |
| BBib-Alex-17145, AAlexandrina-094897, 20230129_20230129_0501, 20260701_20260701_2319 | Afîfî tahkiki (Kahire 1946 ve ta'lîkât) | ÇAĞDAŞ TAHKİK: telifli olabilir | -- | İNDİRİLMEMELİ (G-016 kısıtı). H-6 hukuki soru. |
BULUNAMADI: Bulak 1252 ve İstanbul 1304 Fusûs matn baskıları archive.org aramalarında (başlık/yayıncı/tarih filtreleriyle) çıkmadı. Başka kaynak (HathiTrust, Google Books, Süleymaniye/TDV dijital, SALT, Qatar Digital Library) denenmedi; ağ izni yok/doğrulanmadı.

### B. Istılah sözlükleri
| Kimlik | Eser / baskı | Telif-dışı ön gerekçe | Dosyalar (sha1) |
|---|---|---|---|
| AAlexandrina-195100 | Cürcânî, et-Ta'rîfât; el-Matba'atü'l-Hamîdiyye, 1903 | Cürcânî 816/1413; 1903 baskı | pdf 30063542 B 2e9b4a9b040663914a21b25a8e72ecc7e448c607; djvu.txt 488638 B 61c1eb58926465d98a0acbc05de998bc7bd06d2f |
| AAlexandrina-188000 | Cürcânî, et-Ta'rîfât; Mustafa el-Bâbî el-Halebî, 1938 | 1938 baskı; ancak editör/tahkik emeği olup olmadığı DOĞRULANMADI, orta öncelik | pdf 25041036 B 40e081bd43ad9588079b389b83d275c51a92df3b |
| AAlexandrina-146529 | Kâşânî, Istılâhâtü's-sûfiyye; d.n., [1845] | Kâşânî 736/1335 (ya da 730); 1845 tarihli (Sprenger neşri olabilir; doğrulanmadı) | pdf 14040019 B 947a2a610e4fc733a225c354cae3aa771faf8de7; djvu.txt 179070 B e481becb451c8bdfe54d34677a00d9d696c3814e |
| AAlexandrina-163318 | Tehânevî, Keşşâf; Asiatic Society of Bengal (Kalküta), 1862 | Tehânevî 12./18. yy; 1862 baskı | pdf 72817919 B 433fc6e3b515629aa6cade36e585d82a7fba1569; djvu.txt 3307800 B 3ebc53f80f85761306b9e297bcb911f3f3117eb0 |
| AAlexandrina-151950 | Tehânevî, Keşşâf; Asiatic Society of Bengal, 1862 (ikinci kopya, farklı tarama) | aynı | pdf 114341023 B 3bc7c649e15b080065d7ca595ec738628f24b815; djvu.txt 3453306 B 9fe43e7286bf78aaf3a66834f7a3c4432b2e3651 |
| in.ernet.dli.2015.48782 (ve .196131, .196182 aynı eser) | Sprenger, A Dictionary of the Technical Terms Used in the Sciences of the Musalmans (İngilizce giriş/Kalküta 1854-62), DLI | 1854 | pdf 5912778 B; 48782: 9b329b22c7d8f6853bd37475954a0b65f0b08d24 | İkincil literatür; cilt kapsamı doğrulanmadı. |
Dışarıda bırakılanlar (çağdaş/telifli, indirilmez): Cürcânî Dâru'l-Kütübi'l-İlmiyye 2003 (elshandawily14621), AAlexandrina-068286 (دار الريان), Tehânevî Dahrûc/Mektebetü Lübnân 1996, Tûnus 1971, mujamishthilahatshufiyah ve diğer modern Şâmile/PDF dökümleri.

## Açık işler
1. `*.archive.org` izni (dn*.ca/eu/us.archive.org, ia*.us.archive.org) gelince önce AAlexandrina-060267, -170380, -195100, -146529, -163318 indirilecek; sha256 ve sayfa sayısı yazılacak; ilk sayfalarla künye teyit edilecek.
2. Bulak 1252 / İstanbul 1304 Fusûs matn baskısı için başka kütüphane kaynağı aranacak.
3. Telif durumu hukuki soru olarak ozet.md H-6 ile birlikte kalır.

## İNDİRİLENLER (v2, 2026-11-26; git dışı, veri/ham/<kimlik>/kaynak.pdf ve ocr.txt)
Boyutlar archive.org metadata ile birebir uyuştu. sha256 indirilen dosyadan hesaplandı.
| Kimlik | Dosya | sha256 | Sayfa (pdfinfo) |
|---|---|---|---|
| AAlexandrina-060267 | kaynak.pdf | 9b1653b4478b5758e61b48b8b6d20d11d79f48171c1fc4153e055202f3db232d | 442 |
| AAlexandrina-060267 | ocr.txt | 7cee9deeaba8571b3221d75fe0e9f66300b36747c89e3f41b0e115c871d2458b | -- |
| AAlexandrina-146529 | kaynak.pdf | 53e343569d7c82bf8a3e6b5fb12c03923e127f7d217b5eaf05ff8217932edf5b | 176 |
| AAlexandrina-146529 | ocr.txt | 4014166d87dda62811ab6e4c3b33847b97f4633992b2e48a06082679d03cf821 | -- |

Künye teyidi (ilk sayfalar):
- 060267: Taş baskı (litografi) görünümü; süslü başlık sayfası (s.5) "şerh Fusûs el-hikem" yazıyor; arka planda matn ile şerh iç içe. METİN DEĞİL, ŞERH baskısı. OCR (Arapça/Farsça karışık, bozuk) ilk sayfalarda "el-Kâşânî" ismini veriyor: Kâşânî şerhi olması MUHTEMEL, DOĞRULANMADI. Matn şerhin içine gömülü olduğundan bağımsız Fusûs matni olarak KULLANILAMAZ. Baskı yeri/yılı sayfalardan okunmadı (arşiv künyesi: 1300 [1883], yayıncı yok). OCR kalitesi kullanılamaz düzeyde (el yazısı/taş baskı); Musahhih işi.
- 146529: Başlık sayfası OCR'ı: "Kitâb Istılâhâti's-sûfiyye, Kemâleddîn Ebi'l-Ganâim Abdürrezzâk b. Kemâleddîn el-Kâşî es-Semerkandî"; önsözde Fusûs şerhi ve te'vilât'tan söz ediliyor. Künye eserle uyumlu. Baskı yeri/yılı sayfadan teyit edilmedi (arşiv: [1845]). OCR ilk sayfada okunur, kalite sonradan ölçülmeli.

## ENGEL (v2, yeni): redirect alt alanları, proxy 403
- dn711007.ca.archive.org (AAlexandrina-195100 Ta'rîfât 1903)
- dn710409.ca.archive.org (AAlexandrina-170380 Fusûs Hintçe tercümeli 1894)
- dn721804.ca.archive.org (AAlexandrina-163318 Keşşâf 1862)
Reis'in eklediği dört alan adı (dn711002.ca, dn721900.ca, dn760109.eu, ia801506.us) çalıştı. Her öğenin dağıtım sunucusu farklı olduğundan, sürdürülebilir çözüm `*.archive.org` jokeri. 151950 (ikinci Keşşâf kopyası) ve 188000 denenmedi.

## İNDİRİLENLER (v3, 2026-11-26)
| Kimlik | Dosya | sha256 | Sayfa |
|---|---|---|---|
| AAlexandrina-195100 | kaynak.pdf | ba1d4195784b1350cfd8cfa8b0a9f15d0bcc5fddea0b985635bc4a1f04eb0492 | 200 |
| AAlexandrina-195100 | ocr.txt | 1101d7f209c8900f6ef2c8d565465fbfc4bf73f963bd8ab9ac990e73e1650f11 | -- |
| AAlexandrina-170380 | kaynak.pdf | 6e413df76a33ff318a61a522067c39efda1fbbc5058ba5ffe67e568239efce60 | 484 |
| AAlexandrina-170380 | ocr.txt | e5e1a6aec0d8538728add6f6ad710e6200be487e30a878fd1b2898610d3d14a6 | -- |
| AAlexandrina-163318 | kaynak.pdf | 7e0adc3ab0753da6344f9317fb23a071e05a0751dfe32ff5c285a92222048b3e | 844 |
| AAlexandrina-163318 | ocr.txt | dccb6691ecc58b2b7d3e1c92638b4edbb3b4a7cd10dcd51cee67a43b4e61a631 | -- |
Boyutlar metadata ile uyuştu. Yeni engel çıkmadı (dn711007.ca, dn710409.ca, dn721804.ca çalıştı).

Künye teyidi:
- 195100: OCR'da "Seyyid eş-Şerîf Ali b. Muhammed el-Cürcânî ... et-Ta'rîfât ... ve beyân risâle ... el-Fütûhât'taki (ıstılahlar)" ; "Mustafa Efendi'nin zimmetine, Ezher civarında Mısır'da basıldı". Ta'rîfât metni "Bâbü'l-elif"ten başlıyor. Yani Mısır baskısı, sonunda/arkasında Fütûhât ıstılahları risâlesi (Ta'rîfât'ın bu baskısına eklenmiş; risâlenin müellifi DOĞRULANMADI). Yıl sayfadan okunmadı (arşiv: 1903). Dikkat: ilave risâle kapsam notu; tek başına Ta'rîfât değildir.
- 170380: Başlık sayfası (s.6, görsel): "Fusûsü'l-hikem" ve "Kunûz-ı Esrâr el-Kadem" (Hint dilinde tercüme/şerh), "Matba' Ahmedî ... Delhi (okunması zayıf)". Arapça metin + Urdu/Fârisî tercüme; OCR bozuk. Saf Arapça Fusûs matni olarak KULLANILAMAZ; matnin içerik olarak tam olup olmadığı DOĞRULANMADI. Matn çıkarımı için sayfa düzeni incelenmeli (Musahhih).
- 163318: Giriş: "Bismillâh... ibâre: bu kitapta Keşşâf'ın ... dört tertip (el-Mu'cem)" ve içindekiler harf sıralı maddeler; sayfa 844. Künye Keşşâf ile uyumlu (Kalküta 1862 arşiv künyesi; başlık sayfası okunmadı, DOĞRULANMADI). OCR orta kalite.
Not: üç dosyada da ilk görsel sayfalar kapak/boş; künye OCR ve s.6 görselinden çıkarıldı.
