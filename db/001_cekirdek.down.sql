-- 001_cekirdek.down.sql  —  001_cekirdek.sql'i geri alır (tüm veri silinir).
-- Yalnızca bu veritabanındaki şemaları düşürür; roller küme düzeyindedir (000_roller*.sql) ve dokunulmaz,
-- bu yüzden aynı kümedeki başka veritabanları bu dosyadan etkilenmez. Şemayla birlikte şemadaki hak ve
-- varsayılan hak kayıtları da gider. Eklentiler (pg_trgm, vector) bilerek bırakılır.
BEGIN;
DROP SCHEMA IF EXISTS kasa CASCADE;
DROP SCHEMA IF EXISTS omurga CASCADE;
COMMIT;
