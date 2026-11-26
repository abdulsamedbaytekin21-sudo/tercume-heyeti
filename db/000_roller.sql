-- 000_roller.sql  —  KÜME DÜZEYİ rol kurulumu (veritabanı göçü değildir). Geri alma: db/000_roller.down.sql
-- Süper kullanıcı (ya da CREATEROLE) ile bir kez çalıştırılır; birden fazla kez çalıştırılabilir (idempotent).
-- Roller NOLOGIN'dir: uygulama/oturum rolleri bunlara üye yapılır (GRANT heyet_kasa_yazar TO <uygulama_rolu>).
-- 001_cekirdek.sql bu rollerin var olduğunu varsayar ve hak verir; rolleri oluşturmaz, silmez.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_omurga_okur')  THEN CREATE ROLE heyet_omurga_okur  NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_omurga_yazar') THEN CREATE ROLE heyet_omurga_yazar NOLOGIN IN ROLE heyet_omurga_okur; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_kasa_okur')    THEN CREATE ROLE heyet_kasa_okur    NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='heyet_kasa_yazar')   THEN CREATE ROLE heyet_kasa_yazar   NOLOGIN IN ROLE heyet_kasa_okur; END IF;
END $$;
