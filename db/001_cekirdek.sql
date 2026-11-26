-- 001_cekirdek.sql  (YUKARI göç)  —  geri alma: db/001_cekirdek.down.sql
-- Çekirdek şema: omurga (ortak) + kasa (kurum kasası, satır düzeyinde güvenlik).
-- Önkoşullar: PostgreSQL 15+ (NULLS NOT DISTINCT, security_invoker), eklentiler pg_trgm ve vector,
-- ve db/000_roller.sql'in (küme düzeyi roller) önceden çalıştırılmış olması. Bu dosya rol oluşturmaz/silmez.
-- İdempotent değildir (göç olarak bir kez uygulanır).
BEGIN;

DO $$ BEGIN
  IF (SELECT count(*) FROM pg_roles WHERE rolname IN
      ('heyet_omurga_okur','heyet_omurga_yazar','heyet_kasa_okur','heyet_kasa_yazar')) <> 4 THEN
    RAISE EXCEPTION 'heyet_* rolleri yok: once db/000_roller.sql calistirin';
  END IF;
END $$;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA omurga;
CREATE SCHEMA kasa;
REVOKE ALL ON SCHEMA omurga, kasa FROM PUBLIC;

------------------------------------------------------------------------------
-- Ortak işlevler. Yazan işlevler SECURITY DEFINER'dır: geçmiş/defter tablolarına yalnız onlar yazar,
-- istemci rolleri bu tablolara yazamaz. search_path sabitlenir; nesneler şema adıyla anılır.
------------------------------------------------------------------------------
CREATE TABLE omurga.surum_gecmisi (
  sira bigserial PRIMARY KEY,
  tablo text NOT NULL,
  kimlik uuid NOT NULL,
  surum integer NOT NULL,
  kurum_kimlik uuid,                      -- omurgada hep NULL
  eski jsonb NOT NULL,
  zaman timestamptz NOT NULL DEFAULT now(),
  kullanici text NOT NULL DEFAULT session_user,
  UNIQUE (tablo, kimlik, surum)
);

-- Her kayıtta: kimlik değişmez, sürüm her güncellemede 1 artar, eski hali geçmişe yazılır.
-- Kavram tablolarında (degisiklik sütunu olanlar) her güncelleme yeni bir degisiklik bildirimi taşımalıdır.
CREATE FUNCTION omurga.surum_izle() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF NEW.kimlik IS DISTINCT FROM OLD.kimlik THEN
      RAISE EXCEPTION 'kimlik degistirilemez (%.%)', TG_TABLE_SCHEMA, TG_TABLE_NAME;
    END IF;
    IF to_jsonb(NEW) ? 'degisiklik' AND (to_jsonb(NEW)->'degisiklik') IS NOT DISTINCT FROM (to_jsonb(OLD)->'degisiklik') THEN
      RAISE EXCEPTION 'guncelleme yeni bir degisiklik (kart, ozet) bildirimi tasimali (%.%)', TG_TABLE_SCHEMA, TG_TABLE_NAME;
    END IF;
    NEW.surum := OLD.surum + 1;
    NEW.guncellendi := now();
  END IF;
  EXECUTE format('INSERT INTO %I.surum_gecmisi(tablo, kimlik, surum, kurum_kimlik, eski) VALUES ($1,$2,$3,$4,$5)', TG_TABLE_SCHEMA)
    USING TG_TABLE_NAME, OLD.kimlik, OLD.surum,
          CASE WHEN TG_TABLE_SCHEMA='kasa' THEN (to_jsonb(OLD)->>'kurum_kimlik')::uuid END,
          to_jsonb(OLD);
  RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END $$;

-- Kalıcı kimlik yeniden kullanılmaz: geçmişte (silinmiş/eski) bu kimlik varsa INSERT reddedilir.
CREATE FUNCTION omurga.kimlik_tekrar_yasak() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE var boolean;
BEGIN
  EXECUTE format('SELECT EXISTS (SELECT 1 FROM %I.surum_gecmisi WHERE tablo=$1 AND kimlik=$2)', TG_TABLE_SCHEMA)
    INTO var USING TG_TABLE_NAME, NEW.kimlik;
  IF var THEN RAISE EXCEPTION 'kalici kimlik yeniden kullanilamaz (%.%)', TG_TABLE_SCHEMA, TG_TABLE_NAME; END IF;
  RETURN NEW;
END $$;

-- Varlık kayıt defteri: türlendirilmiş kenarların (iliski) iki ucu buraya bağlanır; böylece
-- çok biçimli kenarlarda bile referans bütünlüğü korunur. Yalnızca tetikleyici yazar.
CREATE TABLE omurga.varlik_kayit (
  kimlik uuid PRIMARY KEY,
  tur text NOT NULL
);
CREATE FUNCTION omurga.varlik_kaydet() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP='INSERT' THEN INSERT INTO omurga.varlik_kayit VALUES (NEW.kimlik, TG_TABLE_NAME);
  ELSE DELETE FROM omurga.varlik_kayit WHERE kimlik = OLD.kimlik; END IF;
  RETURN NULL;
END $$;

-- Her omurga/kasa tablosuna sürüm (+ isteğe bağlı varlık kaydı) tetikleyicilerini bağlar.
CREATE FUNCTION omurga.kayit_ekle(sema text, tablo text, varlik boolean) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION omurga.surum_izle()', tablo||'_surum', sema, tablo);
  EXECUTE format('CREATE TRIGGER %I BEFORE INSERT ON %I.%I FOR EACH ROW EXECUTE FUNCTION omurga.kimlik_tekrar_yasak()', tablo||'_kimlik_tekrar', sema, tablo);
  IF varlik THEN
    EXECUTE format('CREATE TRIGGER %I AFTER INSERT OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION omurga.varlik_kaydet()', tablo||'_varlik', sema, tablo);
  END IF;
END $$;

------------------------------------------------------------------------------
-- OMURGA: sınıflandırma (dönem, ekol)
------------------------------------------------------------------------------
CREATE TABLE omurga.donem (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- kalıcı metin kimliği (ör. donem:h14)
  ad text NOT NULL,
  ust_donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  hicri_baslangic integer,
  hicri_bitis integer,
  not_ text,
  CHECK (hicri_bitis IS NULL OR hicri_baslangic IS NULL OR hicri_bitis >= hicri_baslangic)
);
CREATE TABLE omurga.ekol (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- ör. ekol:ekberi
  ad text NOT NULL,
  ust_ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  not_ text
);

------------------------------------------------------------------------------
-- OMURGA: eser, baski, metin_birimi
------------------------------------------------------------------------------
-- Asıl metin ve şerh AYRI eserdir. Şerh/haşiye -> asıl bağı ust_eser_kimlik ile kurulur (tek doğruluk kaynağı,
-- FK + döngü denetimi). 'serh_eder' ilişki kenarı istenirse açılabilir ama bu bağla çelişemez (iliski tetikleyicisi).
-- Eser bazında dışarıda bırakma bu bağı izler: omurga.dislama_kumesi().
CREATE TABLE omurga.eser (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- envanter kimliği (ör. E-001)
  baslik_ar text NOT NULL,
  baslik_tr text,
  muellif_ad text,
  muellif_vefat_h integer,
  ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  ust_eser_kimlik uuid REFERENCES omurga.eser(kimlik),   -- şerh/haşiye -> asıl eser
  not_ text,
  CHECK (ust_eser_kimlik IS DISTINCT FROM kimlik)
);
CREATE INDEX ON omurga.eser(ust_eser_kimlik);

CREATE FUNCTION omurga.eser_dongu_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.ust_eser_kimlik IS NOT NULL AND EXISTS (
    WITH RECURSIVE yukari AS (
      SELECT kimlik, ust_eser_kimlik FROM omurga.eser WHERE kimlik = NEW.ust_eser_kimlik
      UNION
      SELECT e.kimlik, e.ust_eser_kimlik FROM omurga.eser e JOIN yukari y ON e.kimlik = y.ust_eser_kimlik)
    SELECT 1 FROM yukari WHERE kimlik = NEW.kimlik) THEN
    RAISE EXCEPTION 'ust_eser_kimlik dongu olusturur';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER eser_dongu BEFORE INSERT OR UPDATE OF ust_eser_kimlik ON omurga.eser
  FOR EACH ROW EXECUTE FUNCTION omurga.eser_dongu_denetle();

-- Bir eserin şerh ağacındaki kökü.
CREATE FUNCTION omurga.eser_koku(e uuid) RETURNS uuid LANGUAGE sql STABLE AS $$
  WITH RECURSIVE yukari AS (
    SELECT kimlik, ust_eser_kimlik FROM omurga.eser WHERE kimlik = e
    UNION
    SELECT x.kimlik, x.ust_eser_kimlik FROM omurga.eser x JOIN yukari y ON x.kimlik = y.ust_eser_kimlik)
  SELECT kimlik FROM yukari WHERE ust_eser_kimlik IS NULL LIMIT 1
$$;

-- Dışarıda bırakma kümesi: test eseri + tüm şerh/haşiyeleri (alt ağaç). agac=true ise kökten başlayıp tüm ağaç.
CREATE FUNCTION omurga.dislama_kumesi(test_eser uuid, agac boolean DEFAULT false) RETURNS SETOF uuid
  LANGUAGE sql STABLE AS $$
  WITH RECURSIVE alt AS (
    SELECT CASE WHEN agac THEN omurga.eser_koku(test_eser) ELSE test_eser END AS kimlik
    UNION
    SELECT e.kimlik FROM omurga.eser e JOIN alt a ON e.ust_eser_kimlik = a.kimlik)
  SELECT kimlik FROM alt WHERE kimlik IS NOT NULL
$$;

CREATE TABLE omurga.baski (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),
  tur text NOT NULL CHECK (tur IN ('nesir','serh','ceviri')),
  dil text NOT NULL,                       -- ISO 639-1: ar, tr...
  yayinevi text,
  yil integer,
  muhakkik_veya_mutercim text,
  cilt_sayisi integer,
  kunye text,                              -- tam baskı künyesi
  ham_dosya_yolu text,                     -- ham kaynak deposu göstergesi (değiştirilmez)
  ham_sha256 text CHECK (ham_sha256 IS NULL OR ham_sha256 ~ '^[0-9a-f]{64}$'),
  lisans_sinifi text NOT NULL DEFAULT 'bilinmiyor' CHECK (lisans_sinifi IN ('serbest','telifli','bilinmiyor')),
  not_ text,
  -- Metnin nereye girebileceği DİL ve LİSANSA bağlıdır (tür ne olursa olsun). Üretilmiş sütunlar, aşağıdaki
  -- bileşik FK'lerle birimlere bağlanır: baskı sonradan değişip uygunluğu bozarsa, bağlı birim varken reddedilir.
  omurga_uygun boolean GENERATED ALWAYS AS (dil = 'ar' AND tur <> 'ceviri' AND lisans_sinifi <> 'telifli') STORED,
  kasa_uygun boolean GENERATED ALWAYS AS (dil <> 'ar') STORED,
  UNIQUE (kimlik, eser_kimlik),
  UNIQUE (kimlik, eser_kimlik, omurga_uygun),
  UNIQUE (kimlik, eser_kimlik, kasa_uygun)
);
CREATE INDEX ON omurga.baski(eser_kimlik);

-- Metin birimi: baskı içindeki kalıcı kimlikli parça. YALNIZCA Arapça, çeviri olmayan, telifli olmayan baskıya bağlanır.
-- eser_kimlik elle girilmez: baskıdan türetilir (boş bırakılırsa tetikleyici doldurur; yanlışsa FK reddeder).
CREATE TABLE omurga.metin_birimi (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  baski_kimlik uuid NOT NULL,
  eser_kimlik uuid NOT NULL,               -- türetilmiş (baski.eser_kimlik)
  baski_omurga_uygun boolean NOT NULL DEFAULT true CHECK (baski_omurga_uygun),
  ust_birim_kimlik uuid,
  birim_turu text NOT NULL CHECK (birim_turu IN ('bolum','bab','fasl','sayfa','paragraf','cumle','obek','ayet','hadis','dipnot','ilave')),
  sira integer NOT NULL,
  cilt integer,
  sayfa text,
  metin text NOT NULL,                     -- baskıdaki haliyle
  metin_normal text NOT NULL,              -- harekesiz, normalleştirilmiş (arama için)
  lemma_dizisi text[],
  kok_dizisi text[],                       -- kök dizisi (çok köklü tamlamalarda birden çok eleman)
  mutercim_ilavesi boolean NOT NULL DEFAULT false,
  UNIQUE (kimlik, eser_kimlik),
  UNIQUE (baski_kimlik, kimlik),
  UNIQUE NULLS NOT DISTINCT (baski_kimlik, ust_birim_kimlik, birim_turu, sira),
  FOREIGN KEY (baski_kimlik, eser_kimlik, baski_omurga_uygun) REFERENCES omurga.baski(kimlik, eser_kimlik, omurga_uygun),
  FOREIGN KEY (baski_kimlik, ust_birim_kimlik) REFERENCES omurga.metin_birimi(baski_kimlik, kimlik)
);
CREATE INDEX ON omurga.metin_birimi(baski_kimlik, sira);
CREATE INDEX ON omurga.metin_birimi(ust_birim_kimlik);
CREATE INDEX metin_birimi_normal_trgm ON omurga.metin_birimi USING gin (metin_normal gin_trgm_ops);
CREATE INDEX metin_birimi_kok ON omurga.metin_birimi USING gin (kok_dizisi);

CREATE FUNCTION omurga.metin_birimi_doldur() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE b omurga.baski%ROWTYPE;
BEGIN
  SELECT * INTO b FROM omurga.baski WHERE kimlik = NEW.baski_kimlik;
  IF FOUND THEN
    IF NOT b.omurga_uygun THEN
      RAISE EXCEPTION 'bu baskinin metni omurgaya yazilamaz (dil=%, tur=%, lisans=%); Turkce/telifli/ceviri metin kasadadir',
        b.dil, b.tur, b.lisans_sinifi;
    END IF;
    NEW.eser_kimlik := b.eser_kimlik;       -- elle girilen değer yok sayılır
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER metin_birimi_a_doldur BEFORE INSERT OR UPDATE OF baski_kimlik, eser_kimlik ON omurga.metin_birimi
  FOR EACH ROW EXECUTE FUNCTION omurga.metin_birimi_doldur();

------------------------------------------------------------------------------
-- OMURGA: terim, anlam, tanıklık
-- Güven alanları (guven/gerekce/inceleme), durum ve degisiklik bildirimi kavram kayıtlarının ortak kalıbıdır:
--   guven yuksek|orta|dusuk;  dusuk ise gerekce zorunlu ve inceleme insan|yapildi;
--   durum taslak|onayli|geri_cekildi (silme yerine geri çekme, gerekçeli);
--   degisiklik jsonb {kart, ozet, ...}: kaydı bu sürüme getiren değişiklik; önceki sürümler surum_gecmisi'nde.
------------------------------------------------------------------------------
CREATE TABLE omurga.terim (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- IST-T-0001
  lafiz text NOT NULL,
  lafiz_normal text NOT NULL,              -- harekesiz
  kok text[],                              -- kök dizisi
  lemma text,
  dil text NOT NULL DEFAULT 'ar',
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','geri_cekildi')),
  gerekce text,
  degisiklik jsonb CHECK (degisiklik IS NULL OR (jsonb_typeof(degisiklik)='object' AND degisiklik ?& ARRAY['kart','ozet'])),
  not_ text,
  CHECK (durum <> 'geri_cekildi' OR gerekce IS NOT NULL),
  UNIQUE NULLS NOT DISTINCT (lafiz, kok, dil)
);
CREATE INDEX terim_kok ON omurga.terim USING gin (kok);
CREATE INDEX ON omurga.terim(lemma);
CREATE INDEX terim_normal_trgm ON omurga.terim USING gin (lafiz_normal gin_trgm_ops);

-- Anlam ekol/dönem taşımaz (kararlar.md): bunlar yalnızca tanıklıkta durur.
CREATE TABLE omurga.anlam (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- IST-A-0001-1
  terim_kimlik uuid NOT NULL REFERENCES omurga.terim(kimlik),
  sira integer,
  tanim text NOT NULL,                     -- Türkçe açıklama; kasadaki çeviri karşılığından kopyalanmaz (README)
  tanim_dili text NOT NULL DEFAULT 'tr',
  guven text NOT NULL CHECK (guven IN ('yuksek','orta','dusuk')),
  gerekce text,
  inceleme text CHECK (inceleme IN ('insan','yapildi')),
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','geri_cekildi')),
  degisiklik jsonb CHECK (degisiklik IS NULL OR (jsonb_typeof(degisiklik)='object' AND degisiklik ?& ARRAY['kart','ozet'])),
  not_ text,
  CHECK (guven <> 'dusuk' OR (gerekce IS NOT NULL AND inceleme IS NOT NULL)),
  CHECK (durum <> 'geri_cekildi' OR gerekce IS NOT NULL),
  UNIQUE (terim_kimlik, sira)
);
CREATE INDEX ON omurga.anlam(terim_kimlik);

CREATE TABLE omurga.taniklik (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,                  -- IST-N-0001-1-1
  anlam_kimlik uuid NOT NULL REFERENCES omurga.anlam(kimlik),
  metin_birimi_kimlik uuid,                -- baskıdan okunmuş yer; NULL = henüz okunmadı
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),
  -- Konum değerleri yalnız doğrulandığında yazılır; "doğrulanmadı" gibi gözcü dizgiler değil NULL + bu alan.
  cilt integer,
  sayfa text,
  konum_dogrulama text NOT NULL DEFAULT 'dogrulanmadi' CHECK (konum_dogrulama IN ('dogrulanmadi','dogrulandi')),
  muellif_ad text,
  ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  alinti text,                             -- kısa Arapça alıntı; yalnız baskıdan okunduktan sonra
  guven text NOT NULL CHECK (guven IN ('yuksek','orta','dusuk')),
  gerekce text,
  inceleme text CHECK (inceleme IN ('insan','yapildi')),
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','geri_cekildi')),
  degisiklik jsonb CHECK (degisiklik IS NULL OR (jsonb_typeof(degisiklik)='object' AND degisiklik ?& ARRAY['kart','ozet'])),
  not_ text,
  CHECK (guven <> 'dusuk' OR (gerekce IS NOT NULL AND inceleme IS NOT NULL)),
  CHECK (durum <> 'geri_cekildi' OR gerekce IS NOT NULL),
  CHECK (konum_dogrulama = 'dogrulandi' OR (cilt IS NULL AND sayfa IS NULL)),
  CHECK (durum <> 'onayli' OR (metin_birimi_kimlik IS NOT NULL AND konum_dogrulama = 'dogrulandi')),
  -- tanıklığın eseri, işaret ettiği metin biriminin gerçek eseriyle aynı olmak zorunda
  FOREIGN KEY (metin_birimi_kimlik, eser_kimlik) REFERENCES omurga.metin_birimi(kimlik, eser_kimlik)
);
CREATE INDEX ON omurga.taniklik(anlam_kimlik);
CREATE INDEX ON omurga.taniklik(eser_kimlik);

-- Baskıdan okunmuş tanıklığı olmayan anlam 'onayli' olamaz.
CREATE FUNCTION omurga.anlam_onay_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.durum = 'onayli' AND NOT EXISTS (
      SELECT 1 FROM omurga.taniklik t WHERE t.anlam_kimlik = NEW.kimlik AND t.durum = 'onayli') THEN
    RAISE EXCEPTION 'anlam onayli olabilmek icin baskidan okunmus onayli en az bir taniklik gerekir';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER anlam_onay BEFORE INSERT OR UPDATE OF durum ON omurga.anlam
  FOR EACH ROW EXECUTE FUNCTION omurga.anlam_onay_denetle();

------------------------------------------------------------------------------
-- OMURGA: ilişki (türlendirilmiş kenar)
------------------------------------------------------------------------------
CREATE TABLE omurga.iliski_turu (
  kod text PRIMARY KEY,
  ters_kod text,
  aciklama text
);
INSERT INTO omurga.iliski_turu(kod, ters_kod, aciklama) VALUES
  ('serh_eder','serhi_vardir','Şerh/haşiye -> asıl'),
  ('ekole_mensup','ekol_mensubu','Eser/kişi/terim -> ekol'),
  ('donemde','donem_icerir','Varlık -> dönem'),
  ('ayni_kok','ayni_kok','Aynı kökten terimler'),
  ('esanlamli','esanlamli','Terim/anlam eş anlamlı'),
  ('zit_anlamli','zit_anlamli','Zıt'),
  ('daha_genel','daha_ozel','Kavram genişliği'),
  ('etkiler','etkilenir','Ekol/eser/kavram etkisi'),
  ('atif_yapar','atif_alir','Eser -> eser/birim atfı'),
  ('kullanir','kullanilir','Eser/ekol -> terim'),
  ('ilgili','ilgili','Aynı alanda ilgili, türü belirsiz/serbest bağ'),
  ('sarih_yorumu','sarih_yorumu_olan','Anlam/terim -> şerhin yorumu olduğu ana metin anlamı'),
  ('yerine_gecen','yerine_gecilen','Bir kayıt başka bir kaydın yerine geçer');

CREATE TABLE omurga.iliski (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  dis_kimlik text UNIQUE,
  kaynak_kimlik uuid NOT NULL REFERENCES omurga.varlik_kayit(kimlik),
  hedef_kimlik uuid NOT NULL REFERENCES omurga.varlik_kayit(kimlik),
  iliski_turu text NOT NULL REFERENCES omurga.iliski_turu(kod),
  guc numeric(4,3) CHECK (guc BETWEEN 0 AND 1),
  taniklik_kimlik uuid REFERENCES omurga.taniklik(kimlik),   -- kenarı dayandıran tanıklık
  guven text NOT NULL CHECK (guven IN ('yuksek','orta','dusuk')),
  gerekce text,
  inceleme text CHECK (inceleme IN ('insan','yapildi')),
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','geri_cekildi')),
  degisiklik jsonb CHECK (degisiklik IS NULL OR (jsonb_typeof(degisiklik)='object' AND degisiklik ?& ARRAY['kart','ozet'])),
  not_ text,
  CHECK (kaynak_kimlik <> hedef_kimlik),
  CHECK (guven <> 'dusuk' OR (gerekce IS NOT NULL AND inceleme IS NOT NULL)),
  CHECK (durum <> 'geri_cekildi' OR gerekce IS NOT NULL),
  UNIQUE (kaynak_kimlik, hedef_kimlik, iliski_turu)
);
CREATE INDEX ON omurga.iliski(hedef_kimlik, iliski_turu);

CREATE FUNCTION omurga.iliski_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE k omurga.eser%ROWTYPE; h omurga.eser%ROWTYPE;
BEGIN
  -- Baskıdan okunmuş tanıklığa dayanmayan kenar 'onayli' olamaz.
  IF NEW.durum = 'onayli' AND NOT EXISTS (
      SELECT 1 FROM omurga.taniklik t WHERE t.kimlik = NEW.taniklik_kimlik AND t.durum = 'onayli') THEN
    RAISE EXCEPTION 'iliski onayli olabilmek icin baskidan okunmus onayli bir taniklik (taniklik_kimlik) gerekir';
  END IF;
  -- serh_eder kenarı eserler arasındaysa eser.ust_eser_kimlik ile çelişemez.
  IF NEW.iliski_turu = 'serh_eder' THEN
    SELECT * INTO k FROM omurga.eser WHERE kimlik = NEW.kaynak_kimlik;
    SELECT * INTO h FROM omurga.eser WHERE kimlik = NEW.hedef_kimlik;
    IF (k.kimlik IS NOT NULL OR h.kimlik IS NOT NULL) AND NOT (k.kimlik IS NOT NULL AND h.kimlik IS NOT NULL AND k.ust_eser_kimlik = h.kimlik) THEN
      RAISE EXCEPTION 'serh_eder kenari eser.ust_eser_kimlik ile uyusmuyor';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER iliski_denetle BEFORE INSERT OR UPDATE ON omurga.iliski
  FOR EACH ROW EXECUTE FUNCTION omurga.iliski_denetle();

------------------------------------------------------------------------------
-- OMURGA: vektör (türetilmiş veri)
------------------------------------------------------------------------------
-- Gömme modeli kaydı değişmez (ad, sürüm, boyut, ön işleme): farklı bir ayar yeni model kaydıdır.
CREATE TABLE omurga.gomme_modeli (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  ad text NOT NULL,                        -- örn. bge-m3
  model_surumu text NOT NULL,
  boyut integer NOT NULL CHECK (boyut > 0),
  on_isleme text,                          -- normalleştirme/kesme ayarları
  UNIQUE NULLS NOT DISTINCT (ad, model_surumu, on_isleme)
);
CREATE FUNCTION omurga.gomme_modeli_degismez() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.ad IS DISTINCT FROM OLD.ad OR NEW.model_surumu IS DISTINCT FROM OLD.model_surumu
     OR NEW.boyut IS DISTINCT FROM OLD.boyut OR NEW.on_isleme IS DISTINCT FROM OLD.on_isleme THEN
    RAISE EXCEPTION 'gomme_modeli ad/model_surumu/boyut/on_isleme degistirilemez; yeni model kaydi acin';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER gomme_modeli_a_degismez BEFORE UPDATE ON omurga.gomme_modeli
  FOR EACH ROW EXECUTE FUNCTION omurga.gomme_modeli_degismez();

-- Vektör sütunu boyutsuz: farklı modeller bir arada durabilir. Boyut, model kaydıyla tetikleyicide denetlenir.
-- eser_kimlik hedef birimden türetilir (elle girilen yanlış değeri bileşik FK reddeder).
CREATE TABLE omurga.vektor (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  hedef_kimlik uuid NOT NULL,
  eser_kimlik uuid NOT NULL,               -- türetilmiş; eser bazında dışarıda bırakma için
  model_kimlik uuid NOT NULL REFERENCES omurga.gomme_modeli(kimlik),
  girdi_ozeti text NOT NULL,               -- vektörlenen metnin sha256'sı (bayatlık denetimi)
  gomme vector NOT NULL,
  UNIQUE (hedef_kimlik, model_kimlik),
  FOREIGN KEY (hedef_kimlik, eser_kimlik) REFERENCES omurga.metin_birimi(kimlik, eser_kimlik)
);
CREATE INDEX ON omurga.vektor(eser_kimlik, model_kimlik);

CREATE FUNCTION omurga.vektor_doldur_denetle() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE b integer;
BEGIN
  IF NEW.eser_kimlik IS NULL THEN
    SELECT eser_kimlik INTO NEW.eser_kimlik FROM omurga.metin_birimi WHERE kimlik = NEW.hedef_kimlik;
  END IF;
  SELECT boyut INTO b FROM omurga.gomme_modeli WHERE kimlik = NEW.model_kimlik;
  IF vector_dims(NEW.gomme) <> b THEN
    RAISE EXCEPTION 'vektor boyutu % modelin boyutu % ile uyusmuyor', vector_dims(NEW.gomme), b;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vektor_a_doldur BEFORE INSERT OR UPDATE OF gomme, model_kimlik, hedef_kimlik, eser_kimlik ON omurga.vektor
  FOR EACH ROW EXECUTE FUNCTION omurga.vektor_doldur_denetle();

------------------------------------------------------------------------------
-- KASA: kurum kasası. Her tabloda kurum_kimlik; FORCE RLS; oturum 'heyet.kurum' ile kurum seçer.
-- Kasa içi tüm bağlar BİLEŞİK (kurum_kimlik, kimlik) FK'dir: bir kurum başka kurumun kaydına bağlanamaz.
------------------------------------------------------------------------------
CREATE TABLE kasa.kurum (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  ad text NOT NULL UNIQUE
);
CREATE FUNCTION kasa.gecerli_kurum() RETURNS uuid LANGUAGE sql STABLE AS
  $$ SELECT nullif(current_setting('heyet.kurum', true), '')::uuid $$;

CREATE TABLE kasa.surum_gecmisi (
  sira bigserial PRIMARY KEY,
  tablo text NOT NULL,
  kimlik uuid NOT NULL,
  surum integer NOT NULL,
  kurum_kimlik uuid NOT NULL,
  eski jsonb NOT NULL,
  zaman timestamptz NOT NULL DEFAULT now(),
  kullanici text NOT NULL DEFAULT session_user,
  UNIQUE (tablo, kimlik, surum)
);

-- Türkçe (ve Arapça dışı) birim: telifli çeviri, şerh ya da neşir metni burada durur. Baskı dil<>'ar' olmalıdır.
CREATE TABLE kasa.turkce_birim (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  baski_kimlik uuid NOT NULL,
  eser_kimlik uuid NOT NULL,               -- türetilmiş (baski.eser_kimlik)
  baski_kasa_uygun boolean NOT NULL DEFAULT true CHECK (baski_kasa_uygun),
  ust_birim_kimlik uuid,
  birim_turu text NOT NULL CHECK (birim_turu IN ('bolum','sayfa','paragraf','cumle','obek','dipnot','ilave')),
  sira integer NOT NULL,
  sayfa text,
  metin text NOT NULL,
  mutercim_ilavesi boolean NOT NULL DEFAULT false,
  UNIQUE (kurum_kimlik, kimlik),
  UNIQUE (kurum_kimlik, kimlik, eser_kimlik),
  UNIQUE NULLS NOT DISTINCT (kurum_kimlik, baski_kimlik, ust_birim_kimlik, birim_turu, sira),
  FOREIGN KEY (baski_kimlik, eser_kimlik, baski_kasa_uygun) REFERENCES omurga.baski(kimlik, eser_kimlik, kasa_uygun),
  FOREIGN KEY (kurum_kimlik, ust_birim_kimlik) REFERENCES kasa.turkce_birim(kurum_kimlik, kimlik)
);
CREATE INDEX ON kasa.turkce_birim(kurum_kimlik, baski_kimlik, sira);

CREATE FUNCTION kasa.turkce_birim_doldur() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE b omurga.baski%ROWTYPE;
BEGIN
  SELECT * INTO b FROM omurga.baski WHERE kimlik = NEW.baski_kimlik;
  IF FOUND THEN
    IF NOT b.kasa_uygun THEN
      RAISE EXCEPTION 'kasa.turkce_birim yalniz Arapca disi (dil<>ar) baskiya baglanir (dil=%)', b.dil;
    END IF;
    NEW.eser_kimlik := b.eser_kimlik;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER turkce_birim_a_doldur BEFORE INSERT OR UPDATE OF baski_kimlik, eser_kimlik ON kasa.turkce_birim
  FOR EACH ROW EXECUTE FUNCTION kasa.turkce_birim_doldur();

-- Hizalanmış çift: 1-n, n-1, n-m için cift + cift_uye. Çiftin eseri üyelerinden türer (cift_eser görünümü);
-- elle yazılan eser sütunu yoktur. Bir çiftin tüm üyeleri aynı şerh ağacından olmalıdır (asıl metin + şerhi).
CREATE TABLE kasa.cift (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  duzey text NOT NULL CHECK (duzey IN ('paragraf','cumle','obek')),
  hizalama_guveni numeric(4,3) NOT NULL CHECK (hizalama_guveni BETWEEN 0 AND 1),
  durum text NOT NULL DEFAULT 'otomatik' CHECK (durum IN ('otomatik','inceleme_bekliyor','onayli','reddedildi')),
  inceleyen text,
  not_ text,
  UNIQUE (kurum_kimlik, kimlik)
);
CREATE INDEX ON kasa.cift(kurum_kimlik, durum);

CREATE TABLE kasa.cift_uye (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL,
  cift_kimlik uuid NOT NULL,
  taraf text NOT NULL CHECK (taraf IN ('ar','tr')),
  arapca_birim_kimlik uuid,
  turkce_birim_kimlik uuid,
  eser_kimlik uuid NOT NULL,               -- türetilmiş: üyenin birimi hangi eserden ise o
  sira integer NOT NULL DEFAULT 0,
  CHECK ((taraf='ar' AND arapca_birim_kimlik IS NOT NULL AND turkce_birim_kimlik IS NULL)
      OR (taraf='tr' AND turkce_birim_kimlik IS NOT NULL AND arapca_birim_kimlik IS NULL)),
  FOREIGN KEY (kurum_kimlik) REFERENCES kasa.kurum(kimlik),
  FOREIGN KEY (kurum_kimlik, cift_kimlik) REFERENCES kasa.cift(kurum_kimlik, kimlik),
  FOREIGN KEY (arapca_birim_kimlik, eser_kimlik) REFERENCES omurga.metin_birimi(kimlik, eser_kimlik),
  FOREIGN KEY (kurum_kimlik, turkce_birim_kimlik, eser_kimlik) REFERENCES kasa.turkce_birim(kurum_kimlik, kimlik, eser_kimlik)
);
CREATE INDEX ON kasa.cift_uye(cift_kimlik);
CREATE INDEX ON kasa.cift_uye(arapca_birim_kimlik);
CREATE INDEX ON kasa.cift_uye(eser_kimlik);

CREATE FUNCTION kasa.cift_uye_doldur() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF NEW.taraf = 'ar' THEN
    SELECT eser_kimlik INTO NEW.eser_kimlik FROM omurga.metin_birimi WHERE kimlik = NEW.arapca_birim_kimlik;
  ELSE   -- RLS: yalnız kendi kurumunun birimi görünür
    SELECT eser_kimlik INTO NEW.eser_kimlik FROM kasa.turkce_birim
      WHERE kimlik = NEW.turkce_birim_kimlik AND kurum_kimlik = NEW.kurum_kimlik;
  END IF;
  IF NEW.eser_kimlik IS NULL THEN
    RAISE EXCEPTION 'cift uyesinin birimi bulunamadi';
  END IF;
  IF EXISTS (SELECT 1 FROM kasa.cift_uye u
              WHERE u.cift_kimlik = NEW.cift_kimlik AND u.kimlik <> NEW.kimlik
                AND omurga.eser_koku(u.eser_kimlik) IS DISTINCT FROM omurga.eser_koku(NEW.eser_kimlik)) THEN
    RAISE EXCEPTION 'cift uyeleri ayni asil metin/serh agacindan olmalidir';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER cift_uye_a_doldur BEFORE INSERT OR UPDATE ON kasa.cift_uye
  FOR EACH ROW EXECUTE FUNCTION kasa.cift_uye_doldur();

-- Terim kararı: hizalamadan çıkan "bu ıstılah burada şu karşılıkla"; kaynak çift kimliğiyle.
-- Türkçe karşılık çeviriden türediği için kasada tutulur.
CREATE TABLE kasa.terim_karari (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  terim_kimlik uuid NOT NULL REFERENCES omurga.terim(kimlik),
  anlam_kimlik uuid REFERENCES omurga.anlam(kimlik),
  karsilik_tr text NOT NULL,
  kaynak_cift_kimlik uuid NOT NULL,
  kapsam_eser_kimlik uuid REFERENCES omurga.eser(kimlik),        -- NULL = genel
  durum text NOT NULL DEFAULT 'oneri' CHECK (durum IN ('oneri','onayli','reddedildi')),
  karar_veren text,
  gerekce text,
  FOREIGN KEY (kurum_kimlik, kaynak_cift_kimlik) REFERENCES kasa.cift(kurum_kimlik, kimlik)
);
CREATE INDEX ON kasa.terim_karari(kurum_kimlik, terim_kimlik, durum);

-- Kasa kaynaklı vektörler (Türkçe taraf ve çiftlerden türeyenler). Eser sütunu yok: kasa.vektor_eser görünümü.
CREATE TABLE kasa.vektor (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  cift_kimlik uuid,
  turkce_birim_kimlik uuid,
  model_kimlik uuid NOT NULL REFERENCES omurga.gomme_modeli(kimlik),
  girdi_ozeti text NOT NULL,
  gomme vector NOT NULL,
  CHECK ((cift_kimlik IS NOT NULL)::int + (turkce_birim_kimlik IS NOT NULL)::int = 1),
  FOREIGN KEY (kurum_kimlik, cift_kimlik) REFERENCES kasa.cift(kurum_kimlik, kimlik),
  FOREIGN KEY (kurum_kimlik, turkce_birim_kimlik) REFERENCES kasa.turkce_birim(kurum_kimlik, kimlik)
);
CREATE INDEX ON kasa.vektor(kurum_kimlik, model_kimlik);
CREATE FUNCTION kasa.vektor_boyut_denetle() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
DECLARE b integer;
BEGIN
  SELECT boyut INTO b FROM omurga.gomme_modeli WHERE kimlik = NEW.model_kimlik;
  IF vector_dims(NEW.gomme) <> b THEN
    RAISE EXCEPTION 'vektor boyutu % modelin boyutu % ile uyusmuyor', vector_dims(NEW.gomme), b;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vektor_boyut BEFORE INSERT OR UPDATE OF gomme, model_kimlik ON kasa.vektor
  FOR EACH ROW EXECUTE FUNCTION kasa.vektor_boyut_denetle();

-- Dışarıda bırakma görünümleri (çağıranın hakkıyla, yani RLS altında çalışır).
CREATE VIEW kasa.cift_eser WITH (security_invoker = true) AS
  SELECT DISTINCT kurum_kimlik, cift_kimlik, eser_kimlik FROM kasa.cift_uye;
CREATE VIEW kasa.vektor_eser WITH (security_invoker = true) AS
  SELECT v.kimlik AS vektor_kimlik, v.kurum_kimlik, tb.eser_kimlik
    FROM kasa.vektor v JOIN kasa.turkce_birim tb ON tb.kurum_kimlik = v.kurum_kimlik AND tb.kimlik = v.turkce_birim_kimlik
  UNION ALL
  SELECT v.kimlik, v.kurum_kimlik, ce.eser_kimlik
    FROM kasa.vektor v JOIN kasa.cift_eser ce ON ce.kurum_kimlik = v.kurum_kimlik AND ce.cift_kimlik = v.cift_kimlik;

------------------------------------------------------------------------------
-- Sürüm tetikleyicileri
------------------------------------------------------------------------------
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['donem','ekol','eser','baski','metin_birimi','terim','anlam','taniklik','iliski','gomme_modeli','vektor'] LOOP
    PERFORM omurga.kayit_ekle('omurga', t, t <> 'gomme_modeli');
  END LOOP;
  FOREACH t IN ARRAY ARRAY['turkce_birim','cift','cift_uye','terim_karari','vektor'] LOOP
    PERFORM omurga.kayit_ekle('kasa', t, false);
  END LOOP;
END $$;

-- kasa.kurum özel: kurum_kimlik sütunu yok, geçmişe kendi kimliğiyle yazılır.
CREATE FUNCTION kasa.kurum_surum() RETURNS trigger LANGUAGE plpgsql
  SECURITY DEFINER SET search_path = pg_catalog, public AS $$
BEGIN
  IF TG_OP='UPDATE' THEN
    IF NEW.kimlik IS DISTINCT FROM OLD.kimlik THEN RAISE EXCEPTION 'kimlik degistirilemez'; END IF;
    NEW.surum := OLD.surum + 1; NEW.guncellendi := now();
  END IF;
  INSERT INTO kasa.surum_gecmisi(tablo,kimlik,surum,kurum_kimlik,eski) VALUES ('kurum',OLD.kimlik,OLD.surum,OLD.kimlik,to_jsonb(OLD));
  RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END $$;
CREATE TRIGGER kurum_surum BEFORE UPDATE OR DELETE ON kasa.kurum FOR EACH ROW EXECUTE FUNCTION kasa.kurum_surum();
CREATE TRIGGER kurum_kimlik_tekrar BEFORE INSERT ON kasa.kurum FOR EACH ROW EXECUTE FUNCTION omurga.kimlik_tekrar_yasak();

-- Yazan işlevler yalnız tetikleyici olarak çalışır; doğrudan çağrılamaz.
REVOKE EXECUTE ON FUNCTION omurga.surum_izle(), omurga.kimlik_tekrar_yasak(), omurga.varlik_kaydet(),
  omurga.vektor_doldur_denetle(), kasa.turkce_birim_doldur(), kasa.cift_uye_doldur(),
  kasa.vektor_boyut_denetle(), kasa.kurum_surum() FROM PUBLIC;

------------------------------------------------------------------------------
-- Satır düzeyinde güvenlik (kasa)
------------------------------------------------------------------------------
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['turkce_birim','cift','cift_uye','terim_karari','vektor','surum_gecmisi'] LOOP
    EXECUTE format('ALTER TABLE kasa.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE kasa.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY kurum_izolasyonu ON kasa.%I USING (kurum_kimlik = kasa.gecerli_kurum()) WITH CHECK (kurum_kimlik = kasa.gecerli_kurum())', t);
  END LOOP;
  ALTER TABLE kasa.kurum ENABLE ROW LEVEL SECURITY;
  ALTER TABLE kasa.kurum FORCE ROW LEVEL SECURITY;
  CREATE POLICY kurum_izolasyonu ON kasa.kurum USING (kimlik = kasa.gecerli_kurum()) WITH CHECK (kimlik = kasa.gecerli_kurum());
END $$;

------------------------------------------------------------------------------
-- Yetkiler. surum_gecmisi ve varlik_kayit tablolarına yazarlar DAHİL kimse doğrudan yazamaz (yalnız SELECT);
-- yazmayı SECURITY DEFINER tetikleyiciler yapar.
------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA omurga TO heyet_omurga_okur, heyet_kasa_okur;
GRANT SELECT ON ALL TABLES IN SCHEMA omurga TO heyet_omurga_okur, heyet_kasa_okur;
GRANT EXECUTE ON FUNCTION omurga.eser_koku(uuid), omurga.dislama_kumesi(uuid, boolean) TO heyet_omurga_okur, heyet_kasa_okur;
-- Yazılabilir tablolar (kayıt/defter tabloları hariç) açıkça sayılır.
DO $$
DECLARE t text;
BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='omurga' AND tablename NOT IN ('surum_gecmisi','varlik_kayit') LOOP
    EXECUTE format('GRANT INSERT, UPDATE, DELETE ON omurga.%I TO heyet_omurga_yazar', t);
  END LOOP;
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='kasa' AND tablename NOT IN ('surum_gecmisi') LOOP
    EXECUTE format('GRANT INSERT, UPDATE, DELETE ON kasa.%I TO heyet_kasa_yazar', t);
  END LOOP;
END $$;

GRANT USAGE ON SCHEMA kasa TO heyet_kasa_okur;
GRANT SELECT ON ALL TABLES IN SCHEMA kasa TO heyet_kasa_okur;
-- Omurga rolleri kasa şemasına erişemez (USAGE yok). Kasa yazarı omurgaya yazamaz, yalnız okur.

-- Sonraki göçlerde eklenen tablolar için okuma hakkı otomatik (yazma hakkı her göçte açıkça verilir).
-- Not: varsayılan haklar bu betiği çalıştıran rolün oluşturacağı nesneler içindir.
ALTER DEFAULT PRIVILEGES IN SCHEMA omurga GRANT SELECT ON TABLES TO heyet_omurga_okur, heyet_kasa_okur;
ALTER DEFAULT PRIVILEGES IN SCHEMA kasa GRANT SELECT ON TABLES TO heyet_kasa_okur;

COMMIT;
