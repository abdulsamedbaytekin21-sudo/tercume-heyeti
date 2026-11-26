# Türkçe çevirilerin dayandığı Arapça metin (G-021, 2026-11-26, v1, kutuphaneci)

Birincil = çeviri/neşrin kendi önsözü veya künyesi. İkincil = makale, tanıtım, ansiklopedi, arama özeti.
Hiçbir birincil önsöz bu oturumda okunamadı (ağ kısıtı); hiçbir bilgi varsayımla doldurulmadı.

| Kayıt | Türkçe çeviri | Dayanılan Arapça metin | Düzey | Kanıt (adres + cümle) |
|---|---|---|---|---|
| E-001 | Konuk, Fusûs şerhi (Tahralı-Eraydın; TYEK 2017) | Konuk'un kendi kurduğu Fusûs metni (Bosnevî çizgisi); neşirciler Afîfî, Mansûb, Kılıç–Alkış ile karşılaştırmış. Şerhin kendisi: Konuk el yazması, Konya Mevlânâ Müzesi 3853-3880 | İKİNCİL (arama özeti; birincil PDF erişilemedi) + doğrulanmış ikincil (Karaaslan) | bkz. konuk-fusus-serhi.md G-021 bölümü; https://dergipark.org.tr/en/download/article-file/1476853 ; birincil adres: https://ekitap.yek.gov.tr/Uploads/ProductsFiles/27d472d7-9e77-4698-bfb2-c823bf0f34f8.pdf |
| E-002 | Demirli, Fusûs (Kabalcı 2006) | BULUNAMADI | - | denenenler demirli-fusus.md |
| E-003 | Demirli, Vahdet-i Vücûd ve Esasları (Nusûs) | BULUNAMADI (Âştiyânî varsayılmaz) | - | denenenler konevi-nusus.md |
| E-004 | Demirli, Tasavvuf Metafiziği (Miftâh) | TYEK 2014: Süleymaniye, Ayasofya 1930 yazması (tıpkıbasım, karşılıklı); 2002 baskı: BULUNAMADI | İKİNCİL (okundu) | https://dergipark.org.tr/tr/download/article-file/434549 s. 368: "...Ayasofya Koleksiyonu, 1930 numarada kayıtlı ... yazma nüshası, çeviriyle karşılıklı bir şekilde neşredilmiştir." |

## Ağ izni gereken (bu oturumda erişilemedi)
ekitap.yek.gov.tr ve esatis.yek.gov.tr (Konuk ve Miftâh önsözleri/PDF örnekleri), books.google.com, www.yenisafak.com (Lekesiz eleştirisi), www.kitapyurdu.com (403 bot engeli; izin yetmiyor), ktp.isam.org.tr. En değerli tek adres: Konuk 1. cilt PDF örneği (yek.gov.tr), ayrıca 2. cilt.

## G-021 tur 2 (2026-11-26, kutuphaneci): TYEK önsözleri hâlâ okunamadı
- ekitap.yek.gov.tr ve esatis.yek.gov.tr: ağ izni çalışıyor (CONNECT 200), ancak TLS doğrulaması başarısız: sunucu ara sertifikayı göndermiyor (yalnızca yaprak: CN=*.yek.gov.tr, düzenleyen GlobalSign GCC R46 AlphaSSL CA 2025; hata 21/"unable to get local issuer certificate"). Ara sertifika AIA adresi (secure.globalsign.com) proxy'de 403/çözülemiyor. Doğrulama kapatılmadı. İki deneme (30 sn arayla) aynı sonucu verdi; WebFetch ENOTFOUND.
- Sonuç: Konuk 1./2. cilt ve Miftâh önsözü için birincil teyit YOK; yukarıdaki tablo değişmedi. PDF indirilmedi (veri/kasa/ altında yeni dosya yok).
- Çözüm için gereken: secure.globalsign.com (veya ara sertifika dosyasının kendisi) ağ iznine eklenmeli ya da ara sertifika (gsgccr46alphasslca2025.crt) depoya/ortama elle konmalı.

## G-021 tur 2 SONUÇ (2026-11-26, kutuphaneci): birincil teyit alındı (yukarıdaki "okunamadı" notu geçersiz; TLS, Reis'in birleştirdiği ara sertifika zinciriyle aşıldı)

### E-001 Konuk, Fusûsu'l-Hikem Tercüme ve Şerhi (TYEK, ikinci baskı, 1. cilt) — BİRİNCİL
Kaynak: https://ekitap.yek.gov.tr/Uploads/ProductsFiles/27d472d7-9e77-4698-bfb2-c823bf0f34f8.pdf (892 s.; PDF'in 18. sayfası = basılı s. XVIII; yalnız önsöz sayfaları metne çıkarıldı). PDF: veri/kasa/envanter/konuk1/konuk1.pdf (telifli, kasada).
- s. XVII-XVIII (PDF 17-18), "Eser hakkında": "Neşrini takdim ettiğimiz Fusûsu'l-Hikem Tercüme ve Şerhi, 1334-1346 hicrî ve 1915-1929 milâdî yılları arasında kaleme alınmıştır. Müellifi merhum Ahmed Avni Konuk Bey'in el yazısıyla olan nüsha Konya Mevlânâ Müzesi Kütüphânesi'nde 3853-3880 numaralarda kayıtlı bulunmaktadır."
- s. XVIII: "Fusûs'un Arapça cümlelerini, şârihin yaptığı şekilde, Türkçe tercüme paragraflarından önce yazdık. Ahmed Avni Bey'in şerhinde kullandığı Fusûs metni aynen ve ayrıca harekelenerek hazırlandı. [dn 2] Neşirde de yer yer işâret edildiği üzere şârih Ahmed Avni Bey'in kullandığı metin farklı Fusûs şerhlerinden hareketle kendisinin meydana getirdiği tercihli bir metindir."
- s. XVIII dn 2: "Fusûsu'l-Hikem'in Ahmed Avni Bey tarafından inşâ edilen metnini tespit ederken Ebu'l-Alâ Afîfî, Abdülaziz Sultân el-Mansûb ve Mahmud Erol Kılıç-Abdürrahim Alkış neşirlerini de dikkate aldık ... Metni harekelerken ... Tâceddin Hârizmî ve Abdurrahmân Câmî gibi Fusûs şerhlerinin harekeli neşirlerine, ayrıca Milli Kütüphâne (Adana İl Halk Kütüphânesi Koleksiyonu) nr. 100'de kayıtlı olan tamâmı harekelenmiş Dâvûd Kayserî şerhi nüshasına başvurduk. Ortaya çıkan metni son olarak ... Kılıç ve Alkış'ın Fusûs neşriyle karşılaştırdık. ... Ahmed Avni Bey, Fusûs metnini inşâ ederken mevcut neşirler ve şerhlerden ayrıştığı yerlerde daha çok Abdullah Bosnevî'yi tâkip etmektedir."
- s. XVIII: şerh metni Konuk nüshasıyla mukābele edilmiş; dört ayrı istinsâh daha tespit edilmiş, Abdurrahman Âdil Doğru istinsâhının tashihleri dipnotlarda belirtilmiş.
- Sonuç: Arapça Fusûs metni dış bir neşir değil, Konuk'un şerhinde kendi kurduğu "tercihli metin"; ayrışılan yerlerde Bosnevî izleniyor. Neşirciler Afîfî, Mansûb, Kılıç-Alkış'ı yalnızca karşılaştırma/harekeleme için kullandı. Fusûs yazma numarası önsözde verilmiyor; verilen yazmalar şerhe aittir (Konya 3853-3880; Kayserî şerhi Adana İl Halk Ktp. nr. 100 harekeleme yardımcısı).
- Ürün sayfası (ikincil/yayıncı): https://esatis.yek.gov.tr/urun/fusûsu’l-hikem-tercume-ve-serhi--1-2-ciltler-ceviri-yazi---ikinci-baski-_3842.aspx : "Konya Mevlânâ Müzesi Kütüphânesi'nde 3853-3880 numaralarda kayıtlı olan A. Avni Konuk hattı yazma nüshalar esas alınarak".
- 2. cilt: ekitap.yek.gov.tr'de bulunamadı (aynı ürün adresi ekitap'ta 404'e yönleniyor; ana sayfa/kategori listelerinde yok; site araması denendi). Önsöz iki cilt için ortak "Eser hakkında" bölümüdür, 2. cilt ayrıca beklenmiyor ama doğrulanmadı.

### E-004 Demirli, Miftâhu'l-Gayb (Tasavvuf Metafiziği; TYEK 2014 / ikinci baskı) — BİRİNCİL (yayıncı ürün sayfası)
Kaynak: https://esatis.yek.gov.tr/urun/miftahu-l-gayb--ikinci-baski-_3875.aspx
- Künye alanı: "Yayın Türü Çeviri - Tıpkıbasım; Yazma Nüshası Süleymaniye Yazma Eser Ktp., Ayasofya Koleksiyonu, No. 1930".
- Metin: "Prof. Dr. Ekrem Demirli tarafından tercüme edilen eser, Fatih Sultan Mehmed'in mütalaası için hususi olarak istinsah edilen Süleymaniye Yazma Eser Kütüphanesi, Ayasofya Koleksiyonu 1930 numaralı nüsha esas alınarak yayına hazırlanmış olup ikinci baskısı gerçekleştirilmiştir."
- Sonuç: çeviri Ayasofya 1930 yazmasına dayanır; Hâcevî neşrine dayandığına dair işaret yok. Not: ürün sayfası "ikinci baskı"yı gösteriyor; 2014 baskısının ayrı önsözü okunmadı (TYEK ekitap'ında Miftâh PDF'i bulunamadı), 2002 baskı doğrulanmadı.
