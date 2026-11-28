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
- **Konuk şerhinin Arapça tarafı (G-021):** Konuk hazır bir Fusûs neşri kullanmamış, kendi tercihli metnini kurmuştur (TYEK neşri önsözü). Bu yüzden Konuk çiftlerinde Arapça taraf, Konuk neşrinin içindeki Arapça metindir; ayrı bir basılı neşirden alınmaz. Bu, "Arapça metin çevirinin dayandığı baskıdan alınır" ilkesinin bu eserdeki uygulamasıdır.
- **Konuk çiftinin Türkçe tarafı (G-003):** Konuk'un düzeni Arapça pasaj → harfî tercüme → "Ya'ni …" îzâh paragrafı → şerhtir. Öğretici çiftin Türkçe tarafı harfî tercümedir; "Ya'ni" îzâhı çifte girmez, ayrı alanda (tr_izah) tutulur, şerh ve şerh içi alıntılar (ayet, hadis, beyit) öğretici çift değildir. Hizalama mütercim ilaveleri ayıklanmış Türkçe üzerinden yapılır. (Düzeltme aşağıda: G-025.)
- **Hizalama güven puanı:** Puan doğruluk olasılığı değildir; yalnızca insan inceleme kuyruğunu belirler. Kalibrasyon denetim örneklemiyle yapılacak (mimari.md).
- **Köşeli parantezler neşir ilavesidir (G-025, önceki maddenin yerine):** Konuk neşrindeki köşeli parantezler mütercimin değil neşir heyetinin ilavesidir (s. 145, dn. 79). Öğretici çiftin Türkçe tarafı parantezsiz metindir; parantezli hâl ayrı alanda korunur. Parantez hiçbir zaman iki cümle satırına bölünmez.
- **Neşir varyantları pasaja bağlanır (G-025):** Neşir heyetinin Arapçayı Fusûs neşirlerine göre değiştirip Konuk'un okumasını dipnota aldığı yerlerde, dipnottaki okuma ilgili pasaja varyant olarak bağlanır. Çiftin Arapça tarafı basılı metindir; varyant ayrıca tutulur.
- **Bütünlük bayrağı (G-025):** Hizalama güven puanı metnin bozuk olup olmadığını ölçmez. Her çift ayrıca çıkarım bütünlüğü bayrağı taşır; bayrağı düşen çift öğretici veriye girmez.
- **Sızıntı, kavram ağını da kapsar (G-025):** Bir eser test eseri yapılırsa, o eserden tanıklıkla kurulmuş kavram kayıtları da test sırasında hafızadan çıkarılır.
- **Türkçe taraftaki satır içi Arapça (G-027):** Konuk'un tercümesi içinde geçen Arapça ibareler (ör. "İmdi [ittekû rabbeküm] kavli") tercümenin parçasıdır; çiftin Türkçe tarafında yerinde kalır ve aralığı işaretlenir. Çıkarılırsa Türkçe eksilir. G-026 ile parça sırası düzeldiğinden `satir_ici_arapca` bayrağı bilgi amaçlıdır, tek başına çifti öğretici veriden çıkarmaz. Köşeli parantezli neşir ilaveleri ise yine çıkarılır.
- **İlk öğretici veri kabul edildi (G-028):** Fass-ı Âdemî, hat-0.2.1: 24 pasaj, 199 cümle çifti; 147'si öğretici uygun. Üç bağımsız örneklemde (20 + 36 + 30 çift) anlam hatası 0; öğretici kümede tahmini sınır kusuru ~%3.
- **Neşir ilaveli satırlar (G-028 K-A):** `nasir_ilavesi` dolu olan cümle satırı, ilavenin karşıladığı Arapça işaretlenene kadar öğretici veri dışında tutulur (hat-0.3).
- **Güven eşiği (G-028):** Pasaj güveninin sapma ölçüsü hat sürümüne sabitlenecek ya da birden çok fasstan hesaplanacak; bir pasajın puanı başka pasajların metnine bağlı olmamalı. Eşiğin kendisi en az 2–3 fass daha denetlenmeden değiştirilmez. Model denetimi insan onayı yerine geçmez; insan inceleme kuyruğu ayrı tutulur.

## 2026-11-28
- **Telif kısıtı kaldırıldı (kullanıcı kararı):** Kullanıcı telifin şu aşamada iş kısıtı olmadığını belirtti. Telifli metin dış hizmetlere (ör. vektör API'si) gönderilebilir. Kasa ayrımı veri düzeni olarak korunur. Korsan/gölge kütüphane kaynakları yine kullanılmaz.
- **Süreç (kullanıcı tanımı):** eser bul → hizala → vektörle → çeviri ajanı referans alsın → geri bildirim ve eğitimle en az hataya. Raporlar bu beş adıma göre verilir.
- **Konuk baskısı (G-030):** 1. cilt için elde olan ve hizalaması denetlenen 2017 (1. baskı) esas kalır; 2. cilt için TYEK 2024 (2. baskı) kullanılır. Her çift hangi baskıdan geldiğini taşır. İki baskı arasındaki farklar ileride 1. cilt için karşılaştırılacak.

- **Hizalama hat-0.3 (G-032):** Sözcük oranı parametreleri sürüme sabit (ln oran ort 0.24, sd0 0.12, kısa pasaj için C/n terimi); kenar bandı (0.55-0.60) için satır güveni belirleyici; ilave dolu + satır içi Arapça yok satır öğretici dışı; kısa artık şüphesi ve komşu satırlar öğretici dışı; sahte pasajlar (harfî tercümesi boş / Arapçası öncekinde geçen) alıntıya. Cilt parametresi (`--cilt`) ve cilt başına kimlik öneki eklendi. Ayrıntı: hizalama/YONTEM.md. Hat-0.2.2 çıktısı `veri/kasa/hizalama/fusus-konuk/surum/hat-0.2.2/` altında.
- **Mûsâ fassının iki şerhi (G-034):** Konuk Mûsâ fassını iki kez şerh etmiştir; aynı Arapçanın iki tercümesi iki ayrı çift olarak tutulur (`serh_no`). İkisi aynı eser ve fass sayılır; dışlama ve test bölmesinde birlikte hareket eder.
