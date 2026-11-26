-- 000_roller.down.sql  —  Rolleri siler. ÖNCE kümedeki her veritabanında 001_cekirdek.down.sql çalıştırılmış olmalı.
-- Roller hâlâ bir veritabanında nesne/hak taşıyorsa DROP ROLE açık bir hata verir (bilerek); o veritabanında önce
-- `DROP OWNED BY heyet_omurga_yazar, heyet_omurga_okur, heyet_kasa_yazar, heyet_kasa_okur;` çalıştırın.
DROP ROLE IF EXISTS heyet_omurga_yazar;
DROP ROLE IF EXISTS heyet_omurga_okur;
DROP ROLE IF EXISTS heyet_kasa_yazar;
DROP ROLE IF EXISTS heyet_kasa_okur;
