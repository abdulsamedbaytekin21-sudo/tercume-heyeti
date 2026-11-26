# Mimari özeti

Kaynaklı ve güven notlu klasik metin çeviri sistemi. Hedef, mütercimin okumasını değil sıfırdan çevirmesini kaldırmak;
arka planda zamanla kavram–dönem–ekol–usul–olay grafiğine dönüşecek bir veri yapısı biriktirmek.

## Katmanlar
1. **Ham kaynak (dosya deposu):** Taranmış baskılar, yayınevi dosyaları, OCR çıktıları. Değiştirilmez; sağlama toplamı ve baskı künyesi tutulur.
2. **Yapılandırılmış katman (PostgreSQL, hakikat kaynağı):** eser, baskı, metin birimi (kalıcı kimlikli), sözlük maddeleri ve anlamları, normalleştirilmiş arama sütunları (harekesiz yazım, kök, lemma, pg_trgm).
3. **Vektör katmanı (pgvector, aynı veritabanı):** Türetilmiş veri; model ve sürümüyle saklanır, yeniden üretilebilir.
4. **Kurum kasası:** Telifli çeviriler, onlardan türeyen hizalamalar ve vektörler; ayrı şema, satır düzeyinde güvenlik.

## Kavram modeli
terim (lafız, kök) → anlam → tanıklık (eser, cilt, sayfa, müellif, ekol, dönem). Ekol, dönem, usul, olay ayrı tablolardır
ve türlendirilmiş ilişki kenarlarıyla bağlanır; yeni katmanlar şema kırılmadan eklenir.

## Öğrenme kanalları
1. **Çift hafızası:** Yeni Arapça birime yapı ve anlamca en yakın hizalanmış çiftler örnek olarak verilir. Arapça taraf vektörlenir.
2. **Terim tablosu:** Hizalamadan çıkan "bu ıstılah burada şu karşılıkla" kararları, kaynak çift kimliğiyle.
3. **Ağırlık eğitimi:** Birkaç bin onaylı çiftten sonra periyodik LoRA. Pilotun ilk aşamasında yok.

## Hizalama hattı
Yapısal çapalar (fass/bâb, sayfa numarası, ayet) → paragraf → cümle/öbek (1-n, n-1, n-m) → terim adayları.
Mütercim ilaveleri ve dipnotlar ayrı işaretlenir. Her çiftin hizalama güven puanı vardır; düşük olanlar insan incelemesine gider.

## Güven notu (S1–S6)
S1 çeviri uzlaşısı, S2 geri çeviri, S3 kavram kapsamı, S4 doğrulayıcı model, S5 zorluk, S6 bütünle uyum.
Kademeli: S3 ve S5 önce; risk görülürse S1, S2, S4. Zorunlu işaret kuralları puandan bağımsız.
Kalibrasyon yalnızca rastgele denetim örnekleminden (%5–10) gelen etiketlerle.

## Pilot: kâhin simülasyonu
Henüz mütercim yok. Yayımlanmış Türkçe çeviriler mütercim yerine kullanılır. Eser bölüm bölüm ilerletilir,
her bölümden sonra düzeltmeler hafızaya ve terim tablosuna işlenir; öğrenme eğrisi, öğrenmesi kapalı temel çalıştırmayla karşılaştırılır.

Aday eserler:
- Fusûsu'l-hikem: Ahmed Avni Konuk şerhi (Arapça paragraf + Türkçe tercüme yan yana yapı) ve Ekrem Demirli çevirisi.
- Konevî, en-Nusûs: Ekrem Demirli çevirisi (küçük, ilk uçtan uca deneme için uygun).
- Konevî, Miftâhu'l-gayb: Demirli çevirisi; Fenârî'nin Misbâhu'l-üns şerhiyle metin–şerh ilişkisi.
- Fütûhât-ı Mekkiyye: Demirli çevirisi (Litera); seçilmiş bâblar.
