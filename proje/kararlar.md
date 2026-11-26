# Karar kaydı

Her karar tarih, karar, gerekçe biçiminde eklenir. Eski kararlar silinmez; değişen karar yeni satırla "şu kararın yerine" diye yazılır.

## 2026-11-26
- **Kapsam:** Pilot Ekberî gelenekle sınırlı. Kelam, felsefe ve diğer gelenekler şemanın izin verdiği ama yol haritasının ertelediği alanlar.
- **Mütercim yerine kâhin:** Pilotta 3–4 eserin yayımlanmış Türkçe çevirisi mütercim gibi davranacak. Fark ≠ hata; mümkünse aynı eserin iki çevirisi kullanılacak.
- **Öğretici veri:** Arapça–Türkçe pasaj düzeyinde hizalanmış çiftler. Tek başına Arapça metin öğretici değildir.
- **Arapça kaynak:** Türkçe çevirinin dayandığı baskıdan alınır. OpenITI birincil kaynak değildir (önceki projede sorun çıkardı); gerekirse yalnızca yardımcı karşılaştırma için.
- **İlk eser:** Konuk'un Fusûs şerhi, yapısı gereği paragraf hizalaması hazır olduğu için.
- **Vektörleme:** Hafızadır, öğrenme değildir. Birincil erişim kök ve lafız eşleşmesi; vektör araması yardımcı. Gömme modeli seçimi kendi test setimizle ölçülerek yapılacak (BGE-M3, LaBSE, Arapça odaklı alternatifler).
- **Sızıntı:** Test edilen eserin çiftleri hafızada bulunmaz. En az bir az bilinen metin, model ezberini ölçmek için korpusta olacak.
- **Telif:** Yayımlanmış çeviriler ilk "kurum kasası" gibi izole tutulacak. Ticari kullanım ve eğitim için hukukçu görüşü alınacak. Yayınevleriyle hizmet karşılığı veri lisansı yolu araştırılacak.
- **Ekip düzeni:** Reis her zaman Opus. Üyeler işin zorluğuna göre Opus/Sonnet/Haiku. Kritik teslimler Mümeyyiz denetiminden geçer.

## 2026-11-26 (G-002 / G-009 denetimi sonrası)
- **Eser bazında dışarıda bırakma şerhleri de kapsar:** Test edilen eser bir şerhin asıl metniyse (ör. Fusûs), o şerhin (ör. Konuk) çiftleri de hafızadan çıkarılır. Gerekçe: şerh asıl metni içerir; sızıntı olur. Dışlama elle girilen bir sütuna değil, birimden türetilen eser bağına dayanmalı.
- **Türkçe metin omurgaya hiçbir yoldan giremez:** Engel baskı türüne (`ceviri`) değil, dil ve lisansa bağlanır; şerh ve neşir baskılarındaki Türkçe metin de kasadadır.
- **Kurum seçimi (pilot):** Pilotta tek kurum var; korunan sınır omurga–kasa ayrımıdır ve rollerle tutulur. `heyet.kurum` oturum ayarı pilotta kalabilir. İkinci kurum eklenmeden önce kurum başına rol ve `current_user` eşlemesi zorunludur.
- **Terim kararları kasada durur:** Türkçe karşılık çeviriden türediği için. Omurgaya serbest karşılık gerekirse ayrı arındırma göçü ve hukukçu görüşü gerekir.
- **Kota (T-0009):** Kullanıcının Claude kotası Pro. Opus yalnızca Mümeyyiz denetimi ve ıstılah/anlam kararlarında; EVREN ölçümü (G-011) sonuçlanınca ucuz işler oraya taşınır.
- **Anlam ekol taşımaz (G-010 Ö4):** Ekol, dönem ve müellif yalnızca tanıklıkta durur; `omurga.anlam`'daki ekol/dönem sütunları kaldırılır. Gerekçe: aynı anlam farklı ekollerde tanıklanabilir; ekol bilgisi tanığa aittir.
- **Kavram kayıtları taslak girer (G-010 Ş1):** Baskıdan okunmuş tanıklığı olmayan hiçbir anlam veya ilişki `onayli` olamaz. Bellekten çıkarılan anlam ayrımları "yüksek güven" taşısa bile taslaktır; bağımsız doğrulama baskı ve insan incelemesiyle yapılır.
- **Asıl metin ve şerh ayrı eserdir (G-010 Ö2):** Fusûs ana metni ile Konuk şerhi ayrı eser kayıtlarıdır; şerh–asıl metin bağı ilişkiyle kurulur.
- **Gömme test seti hafızaya girmez (G-005):** degerlendirme/gomme_testi.jsonl çift hafızasına, örnek havuzuna ve kavram ağına konmaz; yalnızca ölçüm içindir.
- **Sözlükçü (kullanıcı kararı):** Sözlükler eser gibi değil, ayrı bir kaynak türü olarak ele alınır. Çevrilen eser, Türkçe çeviriyle olduğu kadar orijinalin yazıldığı döneme ait sözlüklerle de kıyaslanır; önce çağdaş ya da önceki sözlüklere başvurulur, eserden sonraki sözlükler ikincil tanıktır. Bu iş için heyete Sözlükçü (sozlukcu) eklendi. Sözlük maddelerini anlamlara ayırma Istılahçı'dan Sözlükçü'ye geçti; kavram ağına giden nihai anlam kararı Istılahçı'da kalır.
- **Şerh–asıl bağının tek kaynağı (G-002 düzeltmesi):** "İlişkiyle kurulur" ifadesinin yerine: bağın hakikat kaynağı `eser.ust_eser_kimlik` sütunudur; `serh_eder` kenarı isteğe bağlıdır ve bu sütunla çelişemez. Gerekçe: dışlama işlevi tek ve denetlenebilir bir bağa dayanmalı.
- **Telifli Arapça baskı (Reis, hukukçu görüşüne kadar geçici):** Lisans sınıfı `telifli` olan Arapça baskıların (ör. modern tahkikler; H-5) metni ortak omurgaya girmez, kasada durur. Bunun için kasada Arapça birim tablosu açılacak. Hukukçu klasik metnin tahkikten ayrılabileceğini söylerse bu karar gözden geçirilir.
- **Onaylı tanıklık geri çekilirse:** Bağlı onaylı anlam otomatik düşmez; insan incelemesine düşer.
- **OCR (G-018):** Matbu Arapça baskılarda ham katman Tesseract (ara) + sütun kırpma ile üretilir; archive.org'un hazır OCR'ı kullanılmaz (daha kötü). Tashih zorunludur; madde başları ve rakamlar ⟨?⟩ işaretlenip elle okunur. Litografi baskılar için yöntem (Kraken tipi model ya da dijital metinle mukabele) ihtiyaç doğduğunda seçilecek; şimdilik ertelendi.
- **Lisansı bilinmeyen Arapça baskı kasaya gider (G-020 Y1):** Omurgaya yalnızca lisansı `serbest` olarak belirlenmiş Arapça baskı girer; `bilinmiyor` (varsayılan) baskı kasada durur. Gerekçe: omurgadaki sürüm geçmişi silinemez, sonradan telifli çıkan metin temizlenemez.
- **Öncelik (kullanıcı):** Asıl iş, Türkçe çevirilerin hangi Arapça baskıdan yapıldığını tespit etmektir. Arapça tarama toplamak bu tespite tabidir.
