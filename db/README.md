# db/

Yapılandırılmış katman (PostgreSQL, hakikat kaynağı) ve vektör katmanı (pgvector) için şema ve göç dosyaları.
Şema kararları Mimar'ın işidir; geri dönüşü zor kararlar Reis'e bırakılır.

## Göç dosyaları
- `000_roller.sql` / `000_roller.down.sql`: **küme düzeyi** roller (`heyet_omurga_okur/yazar`, `heyet_kasa_okur/yazar`, NOLOGIN). Bir kez, süper kullanıcıyla; idempotent. Down, rollerin hâlâ hak taşıdığı bir veritabanı varsa açık hata verir.
- `001_cekirdek.sql` / `001_cekirdek.down.sql`: veritabanı şeması (`omurga`, `kasa`). Rol oluşturmaz/silmez; roller yoksa açık hata verir. Down yalnız o veritabanındaki iki şemayı düşürür (hakları ve varsayılan hak kayıtları şemayla gider); aynı kümedeki başka veritabanları etkilenmez.
- Gereksinim: PostgreSQL 15+ (`NULLS NOT DISTINCT`, `security_invoker`; 16'da denendi), eklentiler `pg_trgm`, `vector` (eklentiler `public`'te kuruludur; SECURITY DEFINER işlevlerin `search_path`'i `pg_catalog, public`).
- Sıra: `psql -v ON_ERROR_STOP=1 -d postgres -f db/000_roller.sql`, sonra `psql -v ON_ERROR_STOP=1 -d VT -f db/001_cekirdek.sql`. Sıradaki göçler `002_...` ve kendi `.down.sql` dosyasıyla.
- **Up idempotent değildir** (ikinci çalıştırma `schema "omurga" already exists` verir); göç olarak bir kez uygulanır.
- Sonraki göçler: yeni tabloya yazma hakkını açıkça verin (okuma hakkı `ALTER DEFAULT PRIVILEGES` ile otomatiktir; yazma, `surum_gecmisi`/`varlik_kayit` gibi tabloların yanlışlıkla açılmaması için bilerek otomatik değildir) ve `omurga.kayit_ekle(sema, tablo, varlik)` ile sürüm tetikleyicilerini bağlayın.

## Şemalar ve varlıklar
**omurga** (ortak, telifsiz Arapça veri ve kavram ağı)
- `donem`, `ekol`: kendi üst kaydına bağlı; `dis_kimlik` (ör. `ekol:ekberi`).
- `eser` → `baski` → `metin_birimi`. **Asıl metin ve şerh ayrı eserdir**; şerh→asıl bağı `eser.ust_eser_kimlik` (FK, döngü denetimli). `serh_eder` ilişki kenarı eserler arasında açılırsa bu bağla çelişemez (tetikleyici reddeder).
- `baski`: `tur` (nesir/serh/ceviri), `dil`, `lisans_sinifi`, ham dosya sha256. Üretilmiş `omurga_uygun` (= dil `ar` ve tür `ceviri` değil ve lisans `telifli` değil) ve `kasa_uygun` (= dil `ar` değil) sütunları metnin nereye girebileceğini belirler.
- `metin_birimi`: yalnız `omurga_uygun` baskıya bağlanır. `kok_dizisi`, `lemma_dizisi` `text[]` (GIN dizinli); `metin_normal` pg_trgm dizinli.
- `terim` (kök `text[]`) → `anlam` → `taniklik`. Anlam ekol/dönem taşımaz; ekol, dönem, müellif tanıklıkta durur.
- `iliski`: türlendirilmiş kenar; uçları `varlik_kayit` üzerinden herhangi bir omurga varlığına bağlanır; tür `iliski_turu` tablosundan (`ilgili`, `sarih_yorumu`, `yerine_gecen` dahil).
- `gomme_modeli` + `vektor`: türetilmiş veri. Model kaydı değişmez (ad, sürüm, boyut, ön işleme; ayar değişirse yeni model kaydı). Boyut tetikleyiciyle model kaydına karşı doğrulanır; `girdi_ozeti` bayatlık denetimi içindir.

**kasa** (kurum kasası, satır düzeyinde güvenlik): `kurum`, `turkce_birim` (Arapça dışı her metin: telifli çeviri, Türkçe şerh, Türkçe neşir), `cift` + `cift_uye` (1-n, n-1, n-m), `terim_karari`, `vektor`; görünümler `cift_eser`, `vektor_eser`.

**Kavram kayıtlarının ortak kalıbı** (`terim`, `anlam`, `taniklik`, `iliski`; `ornek_30.jsonl` v2 ile eşlenir)
| JSONL | Şema |
|---|---|
| `kimlik` (IST-...) | `dis_kimlik text UNIQUE` (kalıcı uuid `kimlik` ayrıdır; ayrıca `eser`, `baski`, `ekol`, `donem`) |
| `guven` yuksek/orta/dusuk, `gerekce`, `inceleme` | aynı adlı sütunlar (`terim` hariç); `dusuk` ise `gerekce` zorunlu ve `inceleme` insan/yapildi |
| `durum` taslak/onayli/geri_cekildi | `durum` CHECK; `geri_cekildi` gerekçe ister. `anlam`/`iliski` `onayli` olmak için baskıdan okunmuş **onaylı tanıklık** ister (tetikleyici); tanıklık `onayli` olmak için `metin_birimi_kimlik` ve `konum_dogrulama='dogrulandi'` ister |
| `degisiklik {kart, ozet, onceki, tarih, yapan}` | `degisiklik jsonb` (`kart` ve `ozet` anahtarları zorunlu, diğerleri serbest). Güncelleme, önceki değerden **farklı** bir `degisiklik` taşımak zorundadır; eski sürüm (kendi `degisiklik`'iyle) `surum_gecmisi.eski` içine gider, yani "neyi hangi kartla değiştirdik" geçmişte sürüm sürüm okunur |
| `cilt`, `sayfa` "doğrulanmadı" | `cilt`/`sayfa` NULL; `konum_dogrulama` dogrulanmadi/dogrulandi (dolu değer ancak `dogrulandi` ile) |
| `kok[]` | `text[]` |

Her tabloda `kimlik uuid` (PK, değişmez) ve `surum` (her UPDATE'te +1, elle yazılan değer yok sayılır). Eski satır `surum_gecmisi`'ne jsonb yazılır (omurga ve kasa ayrı). Silinen kimlik yeniden kullanılamaz (geçmişte varsa INSERT reddedilir; kasada denetim kurum görünürlüğü içindedir).

## İzolasyon
- Kasa tablolarının hepsi `ENABLE + FORCE ROW LEVEL SECURITY`; politika `kurum_kimlik = kasa.gecerli_kurum()` (oturum ayarı `heyet.kurum`). Ayar yoksa hiçbir satır görünmez/yazılmaz.
- Kasa içindeki tüm bağlar bileşik `(kurum_kimlik, kimlik)` FK'dir: bir kurum başka kurumun birimine/çiftine bağlanamaz; var olmayan ile başka kurumun kimliği aynı hatayı verir.
- **Türkçe/telifli metin omurgaya hiçbir yoldan giremez** ve bu `tur`'a değil dil+lisansa bağlıdır: `metin_birimi → baski` bileşik FK'si `omurga_uygun` bayrağını taşır; baskının dili/türü/lisansı sonradan bağlı birim varken değiştirilirse FK reddeder. `kasa.turkce_birim` yalnız `dil<>'ar'` baskıya bağlanır.
- Roller: omurga rolleri kasa şemasına erişemez; kasa yazarı omurgayı yalnız okur. `surum_gecmisi` (iki şema) ve `varlik_kayit` tablolarına hiçbir istemci rolü yazamaz (yalnız SELECT); yazan tetikleyici işlevler `SECURITY DEFINER` + sabit `search_path`, doğrudan çağrılamaz. Geçmiş `kullanici` sütunu `session_user`'dır.
- Süper kullanıcı RLS'yi atlar. `heyet.kurum` oturum beyanıdır (pilotta kalır; ikinci kurumdan önce kurum başına rol + `current_user` eşlemesi zorunlu, bkz. kararlar.md).

## Eser bazında dışarıda bırakma (şerhler dahil)
Elle yazılan eser etiketi yoktur; eser her zaman birimden türer:
`metin_birimi.eser_kimlik`, `kasa.turkce_birim.eser_kimlik` baskıdan; `omurga.vektor.eser_kimlik` hedef birimden; `kasa.cift_uye.eser_kimlik` üye biriminden türetilir (yanlış değer bileşik FK ile reddedilir). Çiftin eseri üyelerinden okunur (`kasa.cift_eser`), kasa vektörünün eseri `kasa.vektor_eser`'den. Bir çiftin üyeleri aynı şerh ağacından olmalıdır (asıl metin Arapça + şerhin Türkçesi).
```sql
-- test eseri :t ve şerhleri dışarıda; omurga vektörleri
SELECT v.* FROM omurga.vektor v WHERE v.eser_kimlik NOT IN (SELECT omurga.dislama_kumesi(:'t'));
-- hizalanmış çiftler (herhangi bir üyesi dışlama kümesindeyse çift çıkar)
SELECT c.* FROM kasa.cift c WHERE NOT EXISTS (
  SELECT 1 FROM kasa.cift_eser ce WHERE ce.cift_kimlik = c.kimlik
    AND ce.eser_kimlik IN (SELECT omurga.dislama_kumesi(:'t')));
```
`dislama_kumesi(test, agac := false)`: test eseri + tüm şerh/haşiye alt ağacı; `agac := true` kökten tüm ağacı (kardeş şerhler dahil) döndürür.

## Vektör dizini ve cast notu
Vektör sütunu boyutsuzdur (farklı modeller bir arada). ANN dizini model başına kısmi dizin olarak eklenir:
`CREATE INDEX v_hnsw ON omurga.vektor USING hnsw ((gomme::vector(1024)) vector_cosine_ops) WHERE model_kimlik = '...';`
Planlayıcı dizini **ancak** sorguda aynı `gomme::vector(1024)` ifadesi ve aynı `model_kimlik = '...'` koşulu yazılırsa kullanır (`ORDER BY (gomme::vector(1024)) <=> $1`). HNSW en çok 2000 boyut destekler.

## Bilinen sınırlar ve açık noktalar
- `omurga.anlam.tanim` ve `taniklik.alinti` serbest metindir; kasadaki `terim_karari.karsilik_tr` (çeviriden türeyen) buraya elle kopyalanamaz diye teknik engel yoktur. Girişi kural/inceleme sınırlar (`inceleme`, `durum`); omurgaya "serbest karşılık" yolu ayrı arındırma göçü ve hukukçu görüşü ister.
- **Açık karar (Reis):** `lisans_sinifi='telifli'` Arapça (muhakkik hakkı) baskı artık omurgaya **girmez** ve kasa tablosu da Arapça kabul etmez; böyle bir baskı gerekirse ya lisansı yeniden sınıflandırın ya da kasada Arapça birim tablosu açan bir göç gerekir.
- Onay kuralı onay anında denetlenir; onaylı tanıklık sonradan geri çekilirse bağlı onaylı anlam otomatik düşmez (inceleme işidir).
- Kimlik yeniden kullanım denetimi kasada yalnız çağıran kurumun görünürlüğü içindedir (uuid çakışması ayrıca birincil anahtarla engellenir).

## Denetim bulgularının yeniden denemesi (G-009 ve G-010 şema eşlemesi)
Geçici PG 16.15 + pgvector 0.6.0 kümesi (`/var/tmp/g002_pg`, yalnız soket, iş bitince silindi), boş veritabanında `000` + `001`, ardından denemeler (`u_om` omurga yazar, `u_ka` kasa yazar, `u_ok` kasa okur). Sonuçlar:

| Bulgu | Deneme | Sonuç |
|---|---|---|
| E1 | `tur=serh,dil=tr` baskıya omurga birimi; çeviri baskısı; `nesir,tr`; telifli Arapça | Hepsi reddedildi (dil/tür/lisans mesajıyla) |
| E1 | Sonradan baskı `tur→ceviri`, `lisans→telifli`, `dil→tr` (birim varken); birimi çeviri baskısına taşıma | Reddedildi (FK / tetikleyici) |
| E1 | `kasa.turkce_birim` Arapça baskıya; `tr` şerh baskısına | Arapça reddedildi; şerh kabul edildi (doğru) |
| E2 | `cift_uye`'ye elle yanlış `eser_kimlik` (e002) yazma | Değer türetmeyle düzeltildi (e001 yazıldı); sütun elle belirlenemez |
| E2 | `omurga.vektor` hedef e001 birimi, `eser_kimlik=e002` | Reddedildi (bileşik FK); boş bırakılınca e001 türedi |
| E2 | Tanıklık: eser e002, metin birimi e001'e ait | Reddedildi (bileşik FK) |
| E2 | Dışlama: test e001 → `dislama_kumesi` e001+Konuk(e003); Konuk Türkçe + Fusûs Arapça çifti dışlama sorgusundan | Çift dışlandı (0 satır kaldı); `agac=true` kardeşleri de getirdi |
| E2 | Farklı şerh ağacından üye ile çift; `ust_eser_kimlik` döngüsü | İkisi de reddedildi |
| E3 | A kurumu: B'nin birimine çift üyesi, `ust_birim`, B'nin çiftine üye, B çiftinden `terim_karari`, B birimine kasa vektörü | Hepsi reddedildi (bileşik FK/RLS) |
| E3 | Var olmayan çift kimliği ile B'ye ait çift kimliği | Aynı hata (varlık kâhini kapandı) |
| Ö2 | Aynı baskıda `sira=1` kök paragraf iki kez (omurga ve kasa) | Reddedildi (`NULLS NOT DISTINCT`) |
| Ö2 | B kurumu, A'nın bulunduğu baskıda başka `sira` ekler; aynı `sira` yalnız kendi içinde çakışır | Kurum dahil benzersizlik çalışıyor |
| Ö2 | `terim` aynı (lafız, kök NULL/dolu, dil) iki kez | Reddedildi |
| Ö3 | 001'i `t1` ve `t2`'ye yükle, `t1`'de down; `t2` ve roller | `t1` düştü, `t2` ayakta (13 satır), roller yerinde; ardından t1 up, ikisi down, `000` down temiz |
| Ö4 | Yazar rolleri `surum_gecmisi` DELETE/UPDATE, `varlik_kayit` INSERT (omurga ve kasa) | `permission denied` |
| Ö4 | Yazar güncellemesi geçmişe yazıyor (definer); tetikleyici işlevi doğrudan çağrı | Yazıyor / `permission denied` |
| K1 | Sil + aynı kimlikle yeniden ekle | Reddedildi (`kalici kimlik yeniden kullanilamaz`) |
| K2 | Vektör varken model boyutu değiştirme | Reddedildi (model kaydı değişmez); kısmi HNSW + cast ile `Index Scan using v_hnsw` |
| K3 | `ALTER DEFAULT PRIVILEGES` kaydı; down sonrası | 2 kayıt eklenir, down sonrası 0 |
| K5 | Up'ta `kayit_ekle` çıktısı | `DO`/`PERFORM` ile susturuldu; idempotent olmama README'de |
| G-010 şema | `anlam` ekol/dönem sütunu | Yok (`column does not exist`) |
| G-010 şema | `guven`+`gerekce`+`inceleme`: `dusuk` gerekçesiz; gerekçeli | Reddedildi; kabul edildi |
| G-010 şema | `durum` onayli: tanıklıksız anlam; onaylı tanıklıklı anlam; tanıklık konumsuz onayli; doğrulanmamış sayfa; `geri_cekildi` gerekçesiz; eski `reddedildi` değeri | Hepsi reddedildi; tanıklıklı kabul edildi |
| G-010 şema | `degisiklik`: bildirimsiz güncelleme; eksik anahtar; doğru bildirim | Reddedildi / reddedildi / kabul, eski bildirim `surum_gecmisi`'nde |
| G-010 şema | `iliski` onaylı tanıksız; `serh_eder` ust_eser ile çelişen; doğru; yeni 3 tür; `dis_kimlik` tekrarı | Reddedildi / reddedildi / kabul / var / reddedildi |
| Geçen (G-009) | Kurum yok → 0 satır; omurga rolü kasaya; kasa yazarı omurgaya; A, B'yi görmez/B adına yazmaz; okur yazamaz; 7/7 kasa tablosu ENABLE+FORCE; kimlik değişimi; elle `surum` | Hepsi önceki gibi doğru |
| Ö1 | `heyet.kurum` beyanı | Pilot kararıyla ertelendi (kararlar.md), değişmedi |
| Ö1 hariç özeti | | Engelleyici E1–E3 ve önemli Ö2–Ö4 kapandı; K1–K5 giderildi/belgelendi |
