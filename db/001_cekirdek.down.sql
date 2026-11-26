-- 001_cekirdek.down.sql  —  001_cekirdek.sql'i geri alır (tüm veri silinir).
BEGIN;
DROP SCHEMA IF EXISTS kasa CASCADE;
DROP SCHEMA IF EXISTS omurga CASCADE;
DROP OWNED BY heyet_omurga_yazar, heyet_omurga_okur, heyet_kasa_yazar, heyet_kasa_okur;
DROP ROLE IF EXISTS heyet_omurga_yazar;
DROP ROLE IF EXISTS heyet_omurga_okur;
DROP ROLE IF EXISTS heyet_kasa_yazar;
DROP ROLE IF EXISTS heyet_kasa_okur;
-- pg_trgm ve vector eklentileri başka şemalarca kullanılıyor olabilir; bilerek bırakılır.
COMMIT;
