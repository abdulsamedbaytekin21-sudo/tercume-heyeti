# G-018 Arapça OCR denemesi (Musahhih)

Araç: Tesseract 5.3.4 (`apt`: tesseract-ocr, tesseract-ocr-ara), `-l ara`, tek model. Sayfalar `pdftoppm -r 300 -gray -png`. CER aracı: `metin/arac/cer.py` (Levenshtein; "ham" = yalnız boşluk sadeleşir, "katlı" = hareke/tatvil çıkar, Fars harfleri ک ی ھ ہ ve doğu rakamları Arapçaya, أإآ→ا, ة→ه katlanır).
Referans: yalnız sayfa görüntüsünde görülen, elle yazıldı, hareke ve kenar notları yok; tek okuyucu (bağımsız mukabele yok). Okuyamadığım yer bırakılmadı çünkü seçilen satırlar nettir; ama referans tek kişilik, bu bir sınırdır.

## 1. Istılâhâtü's-sûfiyye (matbu), pdf s. 40 (basılı s. 37), 552 karakterlik referans (18 satır)

| Yöntem | CER ham | CER katlı |
|---|---|---|
| archive.org ocr.txt | 0,277 | 0,225 |
| Tesseract psm 6, tam sayfa | 0,223 | 0,205 |
| Tesseract psm 4, tam sayfa | 0,228 | 0,210 |
| Tesseract psm 6/4, sütun kırpılmış (kenar notları atılmış) | 0,174 | 0,159 |
| Aynısı 2x büyütülmüş | 0,183 | 0,167 |

Not: Tam sayfa çıktılarda kenar notları (نقصانا، الجمع، نسخ) referansta yok, OCR'da var; bu CER'i bir miktar şişirir. Kırpmak hem bunu hem hatayı düşürür. Tek sayfa, 552 karakter: oranlar ±birkaç puan oynar; sonuç eğilimdir, ölçüm değil.

Tipik hatalar (sayfadan):
- Madde başı terimleri (küçük, sıkışık, şeddeli/ligatürlü harf): en kötü bölge. Örn. "حقيقة الحقائق" → "عق" إل أن" / "عتيقي» إلن كّ"; "الحكمة" → "كر"". Terimler ıstılah sözlüğünün asıl değeri olduğundan bu kabul edilemez.
- Madde numaraları: (١٢٢..١٢٧) → "(11)", "(1:0)", "(157)", "(:15)". Doğu rakamları güvenilmez.
- Nokta (i'câm) kayıpları/kaymaları: عهد→عبر، شهود→شهون، حقيقة→حفيفة، بعض→بعس، الأعظم→الامظم; ع/غ, ق/ف, د/ن, ض/ص karışır.
- Ligatür/şedde: "الربوبية" şeddeli kelimelerde ”، * , ٭ gibi sahte işaretler; "ا ل" ayrımı. Ayırıcı süs (❃) → `*`, `#`, `»`, `0`, `3` gibi değişken karakterler.
- Hareke: bu baskıda yok denecek kadar az (şedde ve küçük ج ع işaretleri); Tesseract hareke üretmiyor, harekeli baskıda sorun çıkması beklenir (ölçülmedi).
- archive.org OCR'ı: Fars harfleri (ک ی ھ ہ) ve Farsça rakamlar basar, "ال" öncesi hemze ekler (إلذات), bazı satırları atar. Katlama bunun bir kısmını telafi eder; arşiv katmanı bu yüzden ham kalmalı, normalleştirme ayrı.

## 2. Fusûs şerhi (litografi), pdf s. 30 (basılı s. 33)

Yoğun, sıkışık nesih-ta'lik litografi, şeddeli satırlar eğik; Tesseract psm 6 satırları yanlış okuma sırasıyla (sağdan sola değil, kelime dizisi ters) ve anlamsız harf dizisi üretti. Son iki satır (202 karakter referans) için CER = 0,653. Sayfa kullanılamaz. archive.org'un ocr.txt'i bu eser için de çöp (Farsça harfli, anlamsız). Sayfa başına aynı yöntemle düzeltme tavsiye edilmez; sıfırdan elle okuma gerekir.

## Sonuç ve öneri

- Matbu, harekesiz, net baskı: Tesseract `ara` ile ~%16-22 CER. Tashih edilmeden ne hizalamaya ne ıstılah çıkarmaya uygun. Ham OCR olarak saklanır (AKIS.md), tashih zorunlu.
- Litografi: Tesseract yetersiz. Önerilen: Arapça'ya özel model (Kraken `arabic_best`/Calamari tipi çizgi tanıyıcı), ya da çok modlu model ile satır satır okuma (anlam yargısı gerektirir; Claude/Opus işi, kota maliyeti yüksek), ya da OpenITI/Shamela gibi dijital metinden baskıyla mukabele edilerek doğrulama (ilke: birincil kaynak değil, yalnız karşılaştırma).
- Ayar: sütun kırpma ve kenar notunu ayrı alana alma en ucuz kazanç (-5 puan). Sonra denenmeli: ikili eşikleme/Sauvola, 400 dpi, çizgi bölütleme (`psm 7` satır satır), `ara` + `fas` dil birleşimi (Farsça katkı bu baskıda gereksiz).
- Madde başı terimleri ve rakamlar için ayrı geçiş: bu bölgeler `⟨?⟩` bayrağıyla işaretlenip elle okunmalı.
- Ölçüm sınırları: tek sayfa, tek referans okuyucusu; en az 5-10 sayfa ve ikinci okuyucu ile yinelenmeli.
- EVREN'e verilebilecek iş: OCR sonrası biçim temizliği (Fars harf katlama, sahte işaretlerin silinmesi); anlam/okuma kararı değil.

## Dosyalar
- `metin/ornek/istilahat_kasani_s40/`: `referans.txt`, `ham_ocr_archive.txt`, `ham_ocr_tesseract_psm6.txt`, `ham_ocr_tesseract_psm4.txt`, `ham_ocr_tesseract_crop_psm6.txt`
- `metin/ornek/fusus_serh_litografi_s30/`: `referans.txt`, `ham_ocr_tesseract_psm6.txt`
- `metin/arac/cer.py`
