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
