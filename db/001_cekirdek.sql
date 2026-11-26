-- 001_cekirdek.sql  (YUKARI göç)  —  geri alma: db/001_cekirdek.down.sql
-- Çekirdek şema: omurga (ortak) + kasa (kurum kasası, satır düzeyinde güvenlik).
-- Gerekli eklentiler: pg_trgm, vector (pgvector). Süper kullanıcı ya da eklenti hakkı gerekir.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA omurga;
CREATE SCHEMA kasa;
REVOKE ALL ON SCHEMA omurga, kasa FROM PUBLIC;

-- Roller (küme düzeyinde; down dosyası siler). Giriş yapamazlar; uygulama rolleri bunlara üye olur.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_omurga_okur')  THEN CREATE ROLE heyet_omurga_okur NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_omurga_yazar') THEN CREATE ROLE heyet_omurga_yazar NOLOGIN IN ROLE heyet_omurga_okur; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_kasa_okur')    THEN CREATE ROLE heyet_kasa_okur NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_kasa_yazar')   THEN CREATE ROLE heyet_kasa_yazar NOLOGIN IN ROLE heyet_kasa_okur; END IF;
END $$;

------------------------------------------------------------------------------
-- Ortak işlevler
------------------------------------------------------------------------------
-- Her kayıtta: kimlik değişmez, sürüm her güncellemede 1 artar, eski hali geçmişe yazılır.
CREATE FUNCTION omurga.surum_izle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF NEW.kimlik IS DISTINCT FROM OLD.kimlik THEN
      RAISE EXCEPTION 'kimlik degistirilemez (%.%)', TG_TABLE_SCHEMA, TG_TABLE_NAME;
    END IF;
    NEW.surum := OLD.surum + 1;
    NEW.guncellendi := now();
    EXECUTE format('INSERT INTO %I.surum_gecmisi(tablo, kimlik, surum, kurum_kimlik, eski) VALUES ($1,$2,$3,$4,$5)', TG_TABLE_SCHEMA)
      USING TG_TABLE_NAME, OLD.kimlik, OLD.surum,
            CASE WHEN TG_TABLE_SCHEMA='kasa' THEN (to_jsonb(OLD)->>'kurum_kimlik')::uuid END,
            to_jsonb(OLD);
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    EXECUTE format('INSERT INTO %I.surum_gecmisi(tablo, kimlik, surum, kurum_kimlik, eski) VALUES ($1,$2,$3,$4,$5)', TG_TABLE_SCHEMA)
      USING TG_TABLE_NAME, OLD.kimlik, OLD.surum,
            CASE WHEN TG_TABLE_SCHEMA='kasa' THEN (to_jsonb(OLD)->>'kurum_kimlik')::uuid END,
            to_jsonb(OLD);
    RETURN OLD;
  END IF;
  RETURN NEW;
END $$;

CREATE TABLE omurga.surum_gecmisi (
  sira bigserial PRIMARY KEY,
  tablo text NOT NULL,
  kimlik uuid NOT NULL,
  surum integer NOT NULL,
  kurum_kimlik uuid,                      -- omurgada hep NULL
  eski jsonb NOT NULL,
  zaman timestamptz NOT NULL DEFAULT now(),
  kullanici text NOT NULL DEFAULT current_user,
  UNIQUE (tablo, kimlik, surum)
);

-- Varlık kayıt defteri: türlendirilmiş kenarların (iliski) iki ucu da buraya bağlanır; böylece
-- çok biçimli kenarlarda bile referans bütünlüğü korunur.
CREATE TABLE omurga.varlik_kayit (
  kimlik uuid PRIMARY KEY,
  tur text NOT NULL
);
CREATE FUNCTION omurga.varlik_kaydet() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='INSERT' THEN INSERT INTO omurga.varlik_kayit VALUES (NEW.kimlik, TG_TABLE_NAME);
  ELSE DELETE FROM omurga.varlik_kayit WHERE kimlik = OLD.kimlik; END IF;
  RETURN NULL;
END $$;

-- Her omurga tablosu: kimlik uuid PK (değişmez), surum, olusturuldu, guncellendi.
-- Bu kalıbı tek yerde uygulayan yardımcı:
CREATE FUNCTION omurga.kayit_ekle(sema text, tablo text, varlik boolean) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION omurga.surum_izle()', tablo||'_surum', sema, tablo);
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
  ad text NOT NULL,
  ust_ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  not_ text
);

------------------------------------------------------------------------------
-- OMURGA: eser, baski, metin_birimi
------------------------------------------------------------------------------
CREATE TABLE omurga.eser (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  baslik_ar text NOT NULL,
  baslik_tr text,
  muellif_ad text,
  muellif_vefat_h integer,
  ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  ust_eser_kimlik uuid REFERENCES omurga.eser(kimlik),   -- şerh/haşiye -> asıl eser vb. için hızlı bağ
  not_ text
);

CREATE TABLE omurga.baski (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
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
  not_ text
);
CREATE INDEX ON omurga.baski(eser_kimlik);

-- Metin birimi: baskı içindeki kalıcı kimlikli parça (bâb/fasl/sayfa/paragraf/cümle/öbek).
CREATE TABLE omurga.metin_birimi (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  baski_kimlik uuid NOT NULL REFERENCES omurga.baski(kimlik),
  ust_birim_kimlik uuid REFERENCES omurga.metin_birimi(kimlik),
  birim_turu text NOT NULL CHECK (birim_turu IN ('bolum','bab','fasl','sayfa','paragraf','cumle','obek','ayet','hadis','dipnot','ilave')),
  sira integer NOT NULL,
  cilt integer,
  sayfa text,
  metin text NOT NULL,                     -- baskıdaki haliyle
  metin_normal text NOT NULL,              -- harekesiz, normalleştirilmiş (arama için)
  lemma_dizisi text,
  kok_dizisi text,                         -- boşlukla ayrılmış kökler
  mutercim_ilavesi boolean NOT NULL DEFAULT false,
  UNIQUE (baski_kimlik, ust_birim_kimlik, birim_turu, sira)
);
CREATE INDEX ON omurga.metin_birimi(baski_kimlik, sira);
CREATE INDEX ON omurga.metin_birimi(ust_birim_kimlik);
CREATE INDEX metin_birimi_normal_trgm ON omurga.metin_birimi USING gin (metin_normal gin_trgm_ops);
CREATE INDEX metin_birimi_kok_trgm ON omurga.metin_birimi USING gin (kok_dizisi gin_trgm_ops);

-- Çeviri metni omurgaya girmez (kasa); omurgadaki metin birimi yalnızca çeviri olmayan baskıya bağlanır.
CREATE FUNCTION omurga.metin_birimi_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (SELECT tur FROM omurga.baski WHERE kimlik = NEW.baski_kimlik) = 'ceviri' THEN
    RAISE EXCEPTION 'ceviri baskisinin metni omurgaya yazilamaz; kasa.turkce_birim kullanin';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER metin_birimi_ceviri_yasak BEFORE INSERT OR UPDATE OF baski_kimlik ON omurga.metin_birimi
  FOR EACH ROW EXECUTE FUNCTION omurga.metin_birimi_denetle();

------------------------------------------------------------------------------
-- OMURGA: terim, anlam, tanıklık
------------------------------------------------------------------------------
CREATE TABLE omurga.terim (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  lafiz text NOT NULL,
  lafiz_normal text NOT NULL,              -- harekesiz
  kok text,
  lemma text,
  dil text NOT NULL DEFAULT 'ar',
  not_ text,
  UNIQUE (lafiz, kok, dil)
);
CREATE INDEX ON omurga.terim(kok);
CREATE INDEX ON omurga.terim(lemma);
CREATE INDEX terim_normal_trgm ON omurga.terim USING gin (lafiz_normal gin_trgm_ops);

CREATE TABLE omurga.anlam (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  terim_kimlik uuid NOT NULL REFERENCES omurga.terim(kimlik),
  tanim text NOT NULL,
  tanim_dili text NOT NULL DEFAULT 'tr',
  ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),      -- anlamın geçerli olduğu ekol/dönem (varsa)
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','reddedildi')),
  not_ text
);
CREATE INDEX ON omurga.anlam(terim_kimlik);

CREATE TABLE omurga.taniklik (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  anlam_kimlik uuid NOT NULL REFERENCES omurga.anlam(kimlik),
  metin_birimi_kimlik uuid REFERENCES omurga.metin_birimi(kimlik),
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),
  cilt integer,
  sayfa text,
  muellif_ad text,
  ekol_kimlik uuid REFERENCES omurga.ekol(kimlik),
  donem_kimlik uuid REFERENCES omurga.donem(kimlik),
  alinti text,                             -- kısa Arapça alıntı
  not_ text
);
CREATE INDEX ON omurga.taniklik(anlam_kimlik);
CREATE INDEX ON omurga.taniklik(eser_kimlik);

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
  ('kullanir','kullanilir','Eser/ekol -> terim');

CREATE TABLE omurga.iliski (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kaynak_kimlik uuid NOT NULL REFERENCES omurga.varlik_kayit(kimlik),
  hedef_kimlik uuid NOT NULL REFERENCES omurga.varlik_kayit(kimlik),
  iliski_turu text NOT NULL REFERENCES omurga.iliski_turu(kod),
  guc numeric(4,3) CHECK (guc BETWEEN 0 AND 1),
  taniklik_kimlik uuid REFERENCES omurga.taniklik(kimlik),   -- kenarı dayandıran tanıklık
  durum text NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak','onayli','reddedildi')),
  not_ text,
  CHECK (kaynak_kimlik <> hedef_kimlik),
  UNIQUE (kaynak_kimlik, hedef_kimlik, iliski_turu)
);
CREATE INDEX ON omurga.iliski(hedef_kimlik, iliski_turu);

------------------------------------------------------------------------------
-- OMURGA: vektör (türetilmiş veri)
------------------------------------------------------------------------------
CREATE TABLE omurga.gomme_modeli (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  ad text NOT NULL,                        -- örn. bge-m3
  model_surumu text NOT NULL,
  boyut integer NOT NULL CHECK (boyut > 0),
  on_isleme text,                          -- normalleştirme/kesme ayarları
  UNIQUE (ad, model_surumu, on_isleme)
);
-- Vektör sütunu boyutsuz: farklı modeller bir arada durabilir. Boyut, model kaydıyla tetikleyicide denetlenir.
-- ANN dizini model başına kısmi dizin olarak sonradan eklenir (README'ye bakın).
CREATE TABLE omurga.vektor (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  hedef_kimlik uuid NOT NULL REFERENCES omurga.metin_birimi(kimlik),
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),   -- eser bazında dışarıda bırakma için
  model_kimlik uuid NOT NULL REFERENCES omurga.gomme_modeli(kimlik),
  girdi_ozeti text NOT NULL,               -- vektörlenen metnin sha256'sı (bayatlık denetimi)
  gomme vector NOT NULL,
  UNIQUE (hedef_kimlik, model_kimlik)
);
CREATE INDEX ON omurga.vektor(eser_kimlik, model_kimlik);

CREATE FUNCTION omurga.vektor_boyut_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE b integer;
BEGIN
  SELECT boyut INTO b FROM omurga.gomme_modeli WHERE kimlik = NEW.model_kimlik;
  IF vector_dims(NEW.gomme) <> b THEN
    RAISE EXCEPTION 'vektor boyutu % modelin boyutu % ile uyusmuyor', vector_dims(NEW.gomme), b;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER vektor_boyut BEFORE INSERT OR UPDATE OF gomme, model_kimlik ON omurga.vektor
  FOR EACH ROW EXECUTE FUNCTION omurga.vektor_boyut_denetle();

------------------------------------------------------------------------------
-- KASA: kurum kasası. Her tabloda kurum_kimlik; FORCE RLS; oturum 'heyet.kurum' ile kurum seçer.
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
  kullanici text NOT NULL DEFAULT current_user,
  UNIQUE (tablo, kimlik, surum)
);

CREATE TABLE kasa.turkce_birim (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  baski_kimlik uuid NOT NULL REFERENCES omurga.baski(kimlik),   -- tur='ceviri' baskı
  ust_birim_kimlik uuid REFERENCES kasa.turkce_birim(kimlik),
  birim_turu text NOT NULL CHECK (birim_turu IN ('bolum','sayfa','paragraf','cumle','obek','dipnot','ilave')),
  sira integer NOT NULL,
  sayfa text,
  metin text NOT NULL,
  mutercim_ilavesi boolean NOT NULL DEFAULT false,
  UNIQUE (baski_kimlik, ust_birim_kimlik, birim_turu, sira)
);
CREATE INDEX ON kasa.turkce_birim(kurum_kimlik, baski_kimlik, sira);

-- Hizalanmış çift: 1-n, n-1, n-m için cift + cift_uye.
CREATE TABLE kasa.cift (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),      -- eser bazında dışarıda bırakma
  duzey text NOT NULL CHECK (duzey IN ('paragraf','cumle','obek')),
  hizalama_guveni numeric(4,3) NOT NULL CHECK (hizalama_guveni BETWEEN 0 AND 1),
  durum text NOT NULL DEFAULT 'otomatik' CHECK (durum IN ('otomatik','inceleme_bekliyor','onayli','reddedildi')),
  inceleyen text,
  not_ text
);
CREATE INDEX ON kasa.cift(kurum_kimlik, eser_kimlik, durum);

CREATE TABLE kasa.cift_uye (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  cift_kimlik uuid NOT NULL REFERENCES kasa.cift(kimlik),
  taraf text NOT NULL CHECK (taraf IN ('ar','tr')),
  arapca_birim_kimlik uuid REFERENCES omurga.metin_birimi(kimlik),
  turkce_birim_kimlik uuid REFERENCES kasa.turkce_birim(kimlik),
  sira integer NOT NULL DEFAULT 0,
  CHECK ((taraf='ar' AND arapca_birim_kimlik IS NOT NULL AND turkce_birim_kimlik IS NULL)
      OR (taraf='tr' AND turkce_birim_kimlik IS NOT NULL AND arapca_birim_kimlik IS NULL))
);
CREATE INDEX ON kasa.cift_uye(cift_kimlik);
CREATE INDEX ON kasa.cift_uye(arapca_birim_kimlik);

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
  kaynak_cift_kimlik uuid NOT NULL REFERENCES kasa.cift(kimlik),
  kapsam_eser_kimlik uuid REFERENCES omurga.eser(kimlik),        -- NULL = genel
  durum text NOT NULL DEFAULT 'oneri' CHECK (durum IN ('oneri','onayli','reddedildi')),
  karar_veren text,
  gerekce text
);
CREATE INDEX ON kasa.terim_karari(kurum_kimlik, terim_kimlik, durum);

-- Kasa kaynaklı vektörler (Türkçe taraf ve çiftlerden türeyenler).
CREATE TABLE kasa.vektor (
  kimlik uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  surum integer NOT NULL DEFAULT 1,
  olusturuldu timestamptz NOT NULL DEFAULT now(),
  guncellendi timestamptz NOT NULL DEFAULT now(),
  kurum_kimlik uuid NOT NULL REFERENCES kasa.kurum(kimlik),
  cift_kimlik uuid REFERENCES kasa.cift(kimlik),
  turkce_birim_kimlik uuid REFERENCES kasa.turkce_birim(kimlik),
  eser_kimlik uuid NOT NULL REFERENCES omurga.eser(kimlik),
  model_kimlik uuid NOT NULL REFERENCES omurga.gomme_modeli(kimlik),
  girdi_ozeti text NOT NULL,
  gomme vector NOT NULL,
  CHECK ((cift_kimlik IS NOT NULL)::int + (turkce_birim_kimlik IS NOT NULL)::int = 1)
);
CREATE INDEX ON kasa.vektor(kurum_kimlik, eser_kimlik, model_kimlik);
CREATE FUNCTION kasa.vektor_boyut_denetle() RETURNS trigger LANGUAGE plpgsql AS $$
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

------------------------------------------------------------------------------
-- Sürüm tetikleyicileri
------------------------------------------------------------------------------
SELECT omurga.kayit_ekle('omurga', t, t IN ('donem','ekol','eser','baski','metin_birimi','terim','anlam','taniklik','iliski','vektor'))
  FROM unnest(ARRAY['donem','ekol','eser','baski','metin_birimi','terim','anlam','taniklik','iliski','gomme_modeli','vektor']) t;
SELECT omurga.kayit_ekle('kasa', t, false)
  FROM unnest(ARRAY['kurum','turkce_birim','cift','cift_uye','terim_karari','vektor']) t;

-- surum_gecmisi tablosu kasada kurum bazlı; kurum tablosunun kendisi kurum_kimlik taşımaz: özel durum.
-- (kasa.kurum için surum_izle kurum_kimlik'i NULL yazar; kasa.surum_gecmisi.kurum_kimlik NOT NULL olduğundan kurumu kendi kimliğiyle doldur.)
DROP TRIGGER kurum_surum ON kasa.kurum;
CREATE FUNCTION kasa.kurum_surum() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP='UPDATE' THEN
    IF NEW.kimlik IS DISTINCT FROM OLD.kimlik THEN RAISE EXCEPTION 'kimlik degistirilemez'; END IF;
    NEW.surum := OLD.surum + 1; NEW.guncellendi := now();
  END IF;
  INSERT INTO kasa.surum_gecmisi(tablo,kimlik,surum,kurum_kimlik,eski) VALUES ('kurum',OLD.kimlik,OLD.surum,OLD.kimlik,to_jsonb(OLD));
  RETURN CASE WHEN TG_OP='DELETE' THEN OLD ELSE NEW END;
END $$;
CREATE TRIGGER kurum_surum BEFORE UPDATE OR DELETE ON kasa.kurum FOR EACH ROW EXECUTE FUNCTION kasa.kurum_surum();

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
-- Yetkiler
------------------------------------------------------------------------------
GRANT USAGE ON SCHEMA omurga TO heyet_omurga_okur;
GRANT SELECT ON ALL TABLES IN SCHEMA omurga TO heyet_omurga_okur;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA omurga TO heyet_omurga_yazar;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA omurga TO heyet_omurga_yazar;
-- Not: kasa kimlik/gecmis yazan tetikleyiciler çağıranın yetkisiyle çalışır; yazarlara geçmiş tablosu yazma hakkı verilir.

GRANT USAGE ON SCHEMA kasa TO heyet_kasa_okur;
GRANT SELECT ON ALL TABLES IN SCHEMA kasa TO heyet_kasa_okur;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA kasa TO heyet_kasa_yazar;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA kasa TO heyet_kasa_yazar;
-- Kasa yazarı omurga referanslarını görmek zorunda (FK, hizalama): salt okuma.
GRANT USAGE ON SCHEMA omurga TO heyet_kasa_okur;
GRANT SELECT ON ALL TABLES IN SCHEMA omurga TO heyet_kasa_okur;
-- Omurga okuyucuları kasa şemasına erişemez (USAGE verilmedi). Kasa yazarı omurgaya yazamaz.
-- FK denetimi için kasa yazarına referans verilen omurga tablolarında REFERENCES/SELECT yeterlidir.
-- Omurga yazarları kasa şemasında hiçbir hakka sahip değildir.

COMMIT;
