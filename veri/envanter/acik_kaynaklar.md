# Açık kaynak taraması (G-030, 2026-11-28, kutuphaneci)

Kapsam: ekitap.yek.gov.tr (TYEK e-Kitap; erişim 200, TLS zinciri ile doğrulandı). Yalnızca yayıncının kendi sitesindeki açık "İndir" bağlantıları kullanıldı; gölge kütüphane kullanılmadı. Siteden 172 ürün sayfası tarandı (ana sayfa + Dinî İlimler Serisi + Yeni Çıkanlar listeleri; sitenin tüm kataloğu olduğu doğrulanmadı). PDF'ler `veri/kasa/envanter/<kimlik>/` altında (gitignore; depoya girmez).
TARANMADI: esatis.yek.gov.tr (satış sitesi, ayrı tarama yapılmadı), dergipark.org.tr, archive.org.

Telif notu (hüküm değil): Her TYEK PDF'inin künyesinde "Copyright © TYEK. Her hakkı mahfuzdur ... izinsiz çoğaltılamaz" yazıyor, buna karşın aynı yayıncı sitesinde ücretsiz indirme sunuyor. Hizalama/vektör türetme için kullanım HUKUKİ SORUDUR (H-1..H-6 ile birlikte). Dosyalar kasada kalır.

## Hizalamaya uygunluk özeti
| Kimlik | Eser | Arapça+Türkçe aynı ciltte | Metin katmanı | Karar |
|---|---|---|---|---|
| yek-827 | Konuk, Fusûs Tercüme ve Şerhi, cilt 1-2 (2. baskı 2024) | Evet: Fusûs Arapça paragrafı + Türkçe tercüme + şerh iç içe | Evet, Arapça dahil (Arapça harekeli, okunur) | UYGUN, öncelikli |
| yek-697 | Şa'rânî, el-Yevâkît ve'l-Cevâhir (İbnü'l-Arabî görüşleri), 2 cilt, 2019 | Evet: karşılıklı sayfa (tek sayfa Arapça, karşı sayfa Türkçe; sayfa no ortak) | Latin kısım tamam; ARAPÇA KATMAN BOZUK (harfler eksik) | KOŞULLU: Arapça için OCR gerekir |
| yek-625 | İbnü'l-Arabî, Şerhu Hal'i'n-Na'leyn, 2017 | Evet: karşılıklı sayfa; Türkçe [Metin]/[Şerh] bölümlü | Latin tamam; Arapça katman bozuk (örnek s. 401) | KOŞULLU: OCR gerekir |
| yek-560 | İbn Fûrek, el-İbâne an Turuki'l-Kâsidîn, 2014 | Evet: karşılıklı sayfa | Latin tamam; Arapça katman bozuk (örnek s. 151) | KOŞULLU; Ekberî değil (tasavvuf ıstılahı, kenar külliyat) |
| yek-857 | Konevî, Miftâhu'l-Gayb (2. baskı 2025) | Doğrulanmadı: Yayın türü "Çeviri - Tıpkıbasım", Süleymaniye Ayasofya 1930 | YOK (592 sayfa görüntü, metin çıkmıyor) | UYGUN DEĞİL şimdilik; OCR + Türkçe kısmın varlığı doğrulanmalı |
| yek-662 | Konuk Fusûs, tıpkıbasım (el yazması görüntüsü) | Hayır (Osmanlıca el yazması) | YOK (görüntü) | İNDİRİLDİ SONRA SİLİNDİ: 827 aynı eserin çeviri yazısı; tıpkıbasım hizalamaya yaramaz |

## Kayıtlar

### E-007 Konuk, Fusûs Tercüme ve Şerhi, 2. baskı (TYEK), cilt 1 ve 2 (E-001'in dijital kaynağı)
- Sayfa: https://ekitap.yek.gov.tr/urun/fusûsu’l-hikem-tercume-ve-serhi--1-2-ciltler-ceviri-yazi---ikinci-baski-_827.aspx (200). Ürün kodu 297.
- Künye (PDF iç kapağından): TYEK Yayınları 82, Dinî İlimler Serisi 12; çeviri yazı/hazırlık Mustafa Tahralı, Selçuk Eraydın, M. Nedim Tan, Ercan Alkan (Marmara Ü.); editör Tahralı; son okuma Göker İnan, İsmet İpek; arşiv kaydı Konya Mevlana Müzesi 3868-3880 (cilt 2, 13 defter) ve 3853-3867 (cilt 1, 14 defter); 1. baskı İstanbul 2017, 2. baskı 2024; ISBN 978-975-17-3882-2 (takım), 978-975-17-3890-5 (2. cilt).
- Özgün dil: Osmanlı Türkçesi (yani Türkçe taraf Konuk'un Osmanlıca metninin çeviri yazısıdır, modern Türkçe değildir; ıstılah kararlarında not edilmeli).
- Dosyalar (kasa): 
  - veri/kasa/envanter/yek-827-fusus-konuk/cilt1.pdf, 3318437 B, 892 s., sha256 6e4d6205df2e72da7b228547331c9dd1f46f68989f5d62acfcd883e54b21ac29
  - veri/kasa/envanter/yek-827-fusus-konuk/cilt2.pdf, 3671179 B, 888 s., sha256 32ce0c7937b97c2db8d19eab1db5e3a3ed636aa9713774dbba2a8b4253dbadc0
  - Önceden vardı: veri/kasa/envanter/konuk1/konuk1.pdf (cilt 1, 1. baskı 2017, 892 s., sha256 20636ab2a850767f10c3aef6817062657db51cdcc400dd58ca7c41ab5077e61e). Cilt 1 için iki baskı var; hangisinin esas alınacağı kararı bekliyor (iki PDF'in oluşturma tarihi aynı, 2017-08-09; 2. baskı PDF'i 2024-11-18'de değiştirilmiş).
- Metin katmanı: var. Cilt 2 örnek ölçümü (pdftotext): ~2,36 M karakter, ~268 bin Arapça harf; Fusûs Arapçası, Mesnevî beyitleri, âyetler Arapça/Farsça olarak çıkıyor; sayfalar "Fusûsu'l-Hikem Tercüme ve Şerhi │ 873" başlığıyla basılı sayfa numarası taşıyor.
- Sayfa eşlemesi: metinde "[15/6]" biçiminde işaretler var (719 adet cilt 2'de); büyük olasılıkla Konuk yazmasının defter/sayfa numarasıdır; anlamı DOĞRULANMADI (önsözden teyit gerekir). Bu, yazma sayfasına eşleme için kullanılabilir.
- Arapça metin: Konuk'un kendi kurduğu metin; dipnotlarda "Ya'kûb Hân ve Bosnevî nüshaları üzerine yazılmıştır" gibi nüsha notları var (cilt 2 örneklemesi), bkz. dayanak_baski.md/E-006.
- Dikkat: Arapça pdftotext çıktısı görsel sıra/harekeyle gelir; satır kırılması ve RTL sıralama hizalama öncesi normalleştirme ister (Musahhih). Büyük metin modele okutulmadı; yalnızca örneklendi.
- Telif: TYEK "her hakkı mahfuzdur"; H-1 kapsamında.

### E-008 Şa'rânî, el-Yevâkît ve'l-Cevâhir fî Beyâni Akâidi'l-Ekâbir (İbnü'l-Arabî'nin görüşleri), Türkçe çeviri ve Arapça metin, 2 cilt, TYEK 2019
- Sayfa: https://ekitap.yek.gov.tr/urun/el-yevakit-ve’l-cevahir_697.aspx (200). Yayına hazırlayan Mahmut Çınar; yazma Süleymaniye, Âtıf Efendi nr. 1562; ISBN 978-975-17-4343-5 (takım). Konu etiketleri PDF'te: Tasavvuf, Kelâm, İbnü'l-Arabî, Ekberîlik.
- Yapı: karşılıklı sayfa. Örnek: s. 300 Türkçe ("Beşinci Mebhas"), s. 301 Arapça; metin karşılığı gözle teyit edildi (render, s. 301 Arapça sayfa okunaklı).
- Dosyalar: veri/kasa/envanter/yek-697-yevakit-cevahir/cilt1.pdf (2699823 B, 792 s., sha256 742e547109386856f36a23fc98194ffcce6e4f4716e04d992e414623e61abbef); cilt2.pdf (6592025 B, 872 s., sha256 1440318cc42f61f0c3813d0e1357cd2898567f2a9375f4e82387e3f1236e642e).
- Metin katmanı: Latin kısım tam; Arapça sayfalarda katman bozuk (font Unicode eşlemesi eksik, harfler düşüyor; örnek s. 301). Görüntü temiz, yani OCR ile kurtarılabilir. Çevirmenin dayandığı baskı (önsöz) okunmadı.
- Telif: H-2 türü hukuki soru.

### E-009 İbnü'l-Arabî, Şerhu Hal'i'n-Na'leyn (İbn Kasî'nin Hal'u'n-Na'leyn'i üzerine), Arapça eleştirmeli metin ve Türkçe çeviri, TYEK 2017
- Sayfa: https://ekitap.yek.gov.tr/urun/serhu-hal‘i’n-na‘leyn_625.aspx (200). Yayına hazırlayan Ercan Alkan; ISBN 978-975-17-3996-4. Çeviri bölümlü ("[Metin]", "[Şerh]"; "ÜÇÜNCÜ CÜZ" başlığı).
- Yapı: karşılıklı sayfa (s. 400 Türkçe, s. 401 Arapça).
- Dosya: veri/kasa/envanter/yek-625-serhu-hal-in-na-leyn/kitap.pdf, 4409556 B, 742 s., sha256 8bc27c53b03d8b5acba7ffb3d1ba2c4e69c68715cf469782e56f2764002b778b
- Metin katmanı: Latin tam; Arapça bozuk (harekeler var, harfler eksik; örnek s. 401). OCR gerekir. Çevirmen adı sayfada ayrı yazmıyor (yalnızca "yayına hazırlayan"); doğrulanmadı.
- Eserin İbnü'l-Arabî'ye nisbeti sitede "Müellif" olarak veriliyor; kritik kaynak kontrolü yapılmadı.

### E-010 İbn Fûrek, el-İbâne an Turuki'l-Kâsidîn (Tasavvuf Istılahları), TYEK 2014
- Sayfa: https://ekitap.yek.gov.tr/urun/el-ibane-an-turuki’l-kasidin_560.aspx (200). Ahmet Yıldırım, Abdulgaffar Aslan; yazma TSMK Hazine 308; ISBN 978-975-17-3725-0.
- Yapı: karşılıklı sayfa (s. 150 Türkçe, s. 151 Arapça). Ekberî eser DEĞİL; ıstılah karşılaştırması için kenar külliyat.
- Dosya: veri/kasa/envanter/yek-560-el-ibane/kitap.pdf, 4261291 B, 368 s., sha256 390637e0d3fb1e710616e8973b2fd253006604e7999ea1e4fab9af8596c457f9. Arapça katman bozuk (OCR gerekir).

### E-011 Konevî, Miftâhu'l-Gayb (2. baskı, TYEK 2025, Ekrem Demirli)
- Sayfa: https://ekitap.yek.gov.tr/urun/miftahu-l-gayb--ikinci-baski-_857.aspx (200). Tür "Çeviri - Tıpkıbasım"; yazma Ayasofya 1930; ISBN 978-975-17-3749-6.
- Dosya: veri/kasa/envanter/yek-857-miftahu-l-gayb-konevi/kitap.pdf, 40040557 B, 592 s., sha256 d270f0898636a4ad72538a5781587a0711cc2b82f8dd2c2cbb3d2a6409caa1d6. Metin katmanı YOK (görüntü). Türkçe çevirinin bu PDF'te bulunup bulunmadığı DOĞRULANMADI (OCR sonrası bakılmalı). dayanak_baski.md'deki E-004 ile ilişkisi: E-004'te TYEK 2014 baskısı okunmuştu; bu 2. baskı (2025).

### İndirilmeyen ama bulunan Ekberî ile ilgili TYEK yayınları (Arapça+Türkçe birlikte DEĞİL)
- Ankaravî, Zübdetü'l-Fühûs fî Nakşi'l-Fusûs, Osmanlı Türkçesi inceleme-metin, 2026: https://ekitap.yek.gov.tr/urun/zubdetu’l-fuhûs-fi-naksi’l-fusûs_887.aspx (200). Ürün sayfasında PDF var; indirilmedi.
- Bosnevî, Tecelliyât-ı Arâisi'n-Nusûs, Osmanlı Türkçesi inceleme-metin, 2026: https://ekitap.yek.gov.tr/urun/tecelliyat-i-araisi’n-nusûs_901.aspx (200); indirilmedi.
- Fusûsu'l-Hikem Tercüme ve Şerhi tıpkıbasım (662): bkz. özet tablo.
- Kayserî, Cendî, Kâşânî, Bâlî Efendi Fusûs şerhi Türkçe çevirisi: TYEK listelerinde (172 ürün) ilgili başlık BULUNAMADI. Konevî Nusûs, Fenârî Misbâh: bulunamadı.
- Ayn el-Kudât, Zübdetü'l-Hakâik (607, Arapça+Türkçe, Ekberî değil) ve el-Mecmû' fi'l-Meşhûd (884, Âkifzâde; Arapça): listelendi, indirilmedi.

## Açık işler
1. Arapça OCR (Musahhih) E-008, E-009, E-010 için; E-011 için OCR ve Türkçe kısmın varlığı.
2. Konuk 2. cilt ve 1. cilt: önsöz sayfalarından Arapça dayanak (G-021 bulgusuyla kıyas) ve "[15/6]" işaretinin anlamı.
3. esatis, dergipark, archive.org taraması (bu görevde yapılmadı).
4. Telif/lisans: yayıncı sitesindeki ücretsiz indirme ile "her hakkı mahfuzdur" notunun birlikte okunması: hukuki soru.
