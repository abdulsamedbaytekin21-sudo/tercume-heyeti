# db/

Yapılandırılmış katman (PostgreSQL, hakikat kaynağı) ve vektör katmanı (pgvector) için şema ve geçiş dosyaları.
Şema kararları Mimar'ın işidir; bu klasöre şema yazılmadan önce ilgili kart ve denetim gerekir.

## Göç dosyaları
- `001_cekirdek.sql` yukarı, `001_cekirdek.down.sql` aşağı (şemaları, rolleri düşürür; eklentileri bırakır).
- Gereksinim: PostgreSQL 15+ (16'da denendi), eklentiler `pg_trgm`, `vector`.
- Çalıştırma: `psql -v ON_ERROR_STOP=1 -d VT -f db/001_cekirdek.sql`. Sıradaki göçler `002_...` diye gider; her biri kendi `.down.sql` dosyasıyla.

## Şemalar ve varlıklar
**omurga** (ortak, telifsiz veri): `donem`, `ekol` (kendi üst kaydına bağlı), `eser` → `baski` (tur: nesir/serh/ceviri; lisans_sinifi; ham dosya sha256)
→ `metin_birimi` (bâb/sayfa/paragraf/cümle...; `metin` + `metin_normal` + `kok_dizisi`, pg_trgm dizinli).
`terim` (lafız, kök, lemma) → `anlam` → `taniklik` (eser, cilt, sayfa, ekol, dönem, metin birimi).
`iliski`: türlendirilmiş kenar; iki ucu `varlik_kayit` üzerinden herhangi bir omurga varlığına bağlanır (FK ile bütünlük), tür `iliski_turu` tablosundan (genişletilebilir).
`gomme_modeli` + `vektor`: türetilmiş veri; model adı/sürümü/boyutu/ön işleme kayıtlı, `girdi_ozeti` ile bayatlık denetlenir, boyut tetikleyiciyle model kaydına karşı doğrulanır.
**kasa** (kurum kasası): `kurum`, `turkce_birim` (telifli çeviri metni), `cift` + `cift_uye` (1-n, n-1, n-m hizalama; `hizalama_guveni`, `durum`), `terim_karari` (kaynak çift kimliğiyle), `vektor` (kasa kaynaklı).

Her tabloda `kimlik uuid` (PK, değişmez; tetikleyici değişikliği reddeder) ve `surum` (her UPDATE'te +1). Eski satır `surum_gecmisi`'ne jsonb olarak yazılır (omurga ve kasa ayrı).

## İzolasyon
- Kasa tablolarının hepsi `ENABLE + FORCE ROW LEVEL SECURITY`; politika: `kurum_kimlik = kasa.gecerli_kurum()` (oturum ayarı `heyet.kurum`). Ayar yoksa hiçbir satır görünmez/yazılmaz.
- Roller: `heyet_omurga_okur/yazar`, `heyet_kasa_okur/yazar` (NOLOGIN). Omurga rolleri kasa şemasına erişemez; kasa yazarı omurgayı yalnızca okur.
- Çeviri baskısına bağlı metin birimi omurgaya yazılamaz (tetikleyici); Türkçe metin yalnızca kasada.
- `cift.eser_kimlik` ve `vektor.eser_kimlik` eser bazında dışarıda bırakma sorgusu içindir (`WHERE eser_kimlik <> :test_eseri`).

## Bilinen sınırlar ve açık noktalar
- `heyet.kurum` oturumun kendi beyanıdır: uygulama bağlantı rolü bunu kullanıcıdan alamaz, sunucu tarafı ayarlamalıdır. Gerçek çok kiracılı kullanımda kurum başına veritabanı rolü + `current_user` eşlemesi düşünülmeli (karar bekliyor).
- Süper kullanıcı ve tablo sahibi dışındaki roller için geçerlidir; FORCE ile sahip de bağlıdır, ama süper kullanıcı RLS'yi atlar.
- `kasa.terim_karari` Türkçe karşılığı taşıdığı için kasadadır; ortak omurgaya "serbest" terim karşılığı gerekirse ayrı bir onay/arındırma göçü gerekir (hukuki görüş bekleniyor).
- ANN (HNSW) dizini yok: vektör sütunu boyutsuz olduğundan model seçilince kısmi dizin eklenir, örn.
  `CREATE INDEX ON omurga.vektor USING hnsw ((gomme::vector(1024)) vector_cosine_ops) WHERE model_kimlik = '...';`
- Ekol/dönem ataması eser, anlam, tanıklıkta doğrudan sütun; ek bağlar `iliski` ile.
