-- Tercüme Heyeti: ortak kayıt (durum, talimat, görev, rûznâme, rapor)
-- Tablolar ve iş mantığı "heyet" şemasında; dışarıya açık tek kapı public.heyet_api (anahtarlı).

create schema if not exists heyet;

create table heyet.ayar (ad text primary key, deger text not null);

create table heyet.uye (
  id text primary key, ad text not null, harf text not null, rol text not null,
  model text not null, ana boolean not null default false, sira int not null default 0
);

create table heyet.durum (
  uye text primary key, hal text not null default 'bosta' check (hal in ('calisiyor','bekliyor','bosta')),
  su_an text not null default '', gorev text, adimlar jsonb not null default '[]'::jsonb,
  guncellendi timestamptz
);

create table heyet.talimat (
  no bigint generated always as identity primary key,
  hedef text not null, kimden text not null default 'kullanici', metin text not null,
  durum text not null default 'bekliyor' check (durum in ('bekliyor','iletildi')),
  zaman timestamptz not null default now(), iletildi timestamptz
);
create index on heyet.talimat (hedef, durum);

create table heyet.gorev (
  id text primary key, baslik text not null, atanan text not null,
  durum text not null default 'sirada'
    check (durum in ('sirada','calisiyor','bekliyor','incelemede','iade','devredildi','tamam')),
  yurutucu text not null default 'claude', model text, govde text not null default '',
  teslim text, olusturuldu timestamptz not null default now(), guncellendi timestamptz not null default now()
);

create table heyet.ruzname (
  no bigint generated always as identity primary key,
  zaman timestamptz not null default now(), kim text not null, olay text not null, metin text not null default ''
);

create table heyet.rapor (id int primary key default 1 check (id = 1), metin text not null default '',
  guncellendi timestamptz not null default now());

alter table heyet.ayar enable row level security;
alter table heyet.uye enable row level security;
alter table heyet.durum enable row level security;
alter table heyet.talimat enable row level security;
alter table heyet.gorev enable row level security;
alter table heyet.ruzname enable row level security;
alter table heyet.rapor enable row level security;

revoke all on schema heyet from public, anon, authenticated;
revoke all on all tables in schema heyet from public, anon, authenticated;

-- ------------------------------------------------------------------ yardımcılar
create or replace function heyet.kisalt(t text, n int) returns text language sql immutable as $$
  select case when t is null then '' when length(t) <= n then t else left(t, n - 1) || '…' end $$;

create or replace function heyet.ruzname_ekle(p_kim text, p_olay text, p_metin text default '')
returns void language sql as $$
  insert into heyet.ruzname (kim, olay, metin) values (p_kim, p_olay, heyet.kisalt(coalesce(p_metin,''), 240)) $$;

create or replace function heyet.uye_mi(p text) returns boolean language sql stable as $$
  select exists (select 1 from heyet.uye where id = p) or p = 'antigravity' $$;

create or replace function heyet.kayit_ekle(p_govde text, p_satir text) returns text language sql as $$
  select (case when position(E'\n## Kayıt' in E'\n' || p_govde) = 0
               then rtrim(p_govde, E'\n') || E'\n\n## Kayıt\n' else rtrim(p_govde, E'\n') || E'\n' end)
         || '- ' || to_char(now() at time zone 'Europe/Istanbul', 'YYYY-MM-DD HH24:MI') || ' ' || p_satir || E'\n' $$;

-- ------------------------------------------------------------------ durum
create or replace function heyet.durum_yaz(p_uye text, p_hal text default null, p_su_an text default null,
  p_gorev text default null, p_adimlari_sifirla boolean default false)
returns void language plpgsql as $$
begin
  if not heyet.uye_mi(p_uye) then raise exception 'Bilinmeyen üye: %', p_uye; end if;
  insert into heyet.durum (uye) values (p_uye) on conflict do nothing;
  update heyet.durum set
    hal = coalesce(p_hal, hal),
    su_an = coalesce(heyet.kisalt(p_su_an, 200), su_an),
    gorev = coalesce(p_gorev, gorev),
    adimlar = case when p_adimlari_sifirla then '[]'::jsonb else adimlar end,
    guncellendi = now()
  where uye = p_uye;
end $$;

create or replace function heyet.durum_oku(p_uye text) returns jsonb language sql stable as $$
  select coalesce((select to_jsonb(d) from heyet.durum d where uye = p_uye),
                  jsonb_build_object('uye', p_uye, 'hal', 'bosta', 'su_an', '', 'adimlar', '[]'::jsonb)) $$;

create or replace function heyet.adim_ekle(p_uye text, p_arac text, p_ozet text)
returns void language plpgsql as $$
declare a jsonb;
begin
  insert into heyet.durum (uye) values (p_uye) on conflict do nothing;
  select adimlar into a from heyet.durum where uye = p_uye;
  a := coalesce(a, '[]'::jsonb) || jsonb_build_array(jsonb_build_object(
         'zaman', now(), 'arac', p_arac, 'ozet', heyet.kisalt(p_ozet, 110)));
  if jsonb_array_length(a) > 25 then
    a := (select jsonb_agg(x order by i) from jsonb_array_elements(a) with ordinality t(x, i)
          where i > jsonb_array_length(a) - 25);
  end if;
  update heyet.durum set adimlar = a, guncellendi = now(),
    hal = case when hal = 'bosta' then 'calisiyor' else hal end
  where uye = p_uye;
end $$;

-- ------------------------------------------------------------------ talimat
create or replace function heyet.talimat_ekle(p_hedef text, p_metin text, p_kimden text default 'kullanici')
returns jsonb language plpgsql as $$
declare r heyet.talimat;
begin
  if not heyet.uye_mi(p_hedef) then raise exception 'Bilinmeyen üye: %', p_hedef; end if;
  if coalesce(trim(p_metin), '') = '' then raise exception 'Talimat boş olamaz'; end if;
  insert into heyet.talimat (hedef, kimden, metin) values (p_hedef, p_kimden, trim(p_metin)) returning * into r;
  perform heyet.ruzname_ekle(p_kimden, 'talimat', p_hedef || ': ' || trim(p_metin));
  return jsonb_build_object('id', 'T-' || lpad(r.no::text, 4, '0'), 'zaman', r.zaman, 'kimden', r.kimden,
                            'metin', r.metin, 'durum', r.durum);
end $$;

create or replace function heyet.talimat_ilet(p_uye text) returns jsonb language plpgsql as $$
declare sonuc jsonb;
begin
  with g as (
    update heyet.talimat set durum = 'iletildi', iletildi = now()
    where hedef = p_uye and durum = 'bekliyor' returning *)
  select coalesce(jsonb_agg(jsonb_build_object('id', 'T-' || lpad(no::text, 4, '0'), 'zaman', zaman,
           'kimden', kimden, 'metin', metin) order by no), '[]'::jsonb) into sonuc from g;
  if jsonb_array_length(sonuc) > 0 then
    perform heyet.ruzname_ekle(p_uye, 'talimat-iletildi',
      (select string_agg(x->>'id', ', ') from jsonb_array_elements(sonuc) x));
  end if;
  return sonuc;
end $$;

create or replace function heyet.talimat_bekleyen(p_uye text) returns int language sql stable as $$
  select count(*)::int from heyet.talimat where hedef = p_uye and durum = 'bekliyor' $$;

-- ------------------------------------------------------------------ görev
create or replace function heyet.gorev_yeni(p_baslik text, p_atanan text, p_govde text, p_model text default null)
returns text language plpgsql as $$
declare yeni text;
begin
  if not heyet.uye_mi(p_atanan) then raise exception 'Bilinmeyen üye: %', p_atanan; end if;
  perform pg_advisory_xact_lock(4317);
  select 'G-' || lpad((coalesce(max(substr(id, 3)::int), 0) + 1)::text, 3, '0') into yeni from heyet.gorev;
  insert into heyet.gorev (id, baslik, atanan, model, govde)
  values (yeni, p_baslik, p_atanan, coalesce(p_model, (select model from heyet.uye where id = p_atanan)),
          heyet.kayit_ekle(p_govde, 'Kart açıldı.'));
  perform heyet.ruzname_ekle('reis', 'gorev-yeni', yeni || ' ' || p_baslik || ' → ' || p_atanan);
  return yeni;
end $$;

create or replace function heyet.gorev_durum(p_id text, p_durum text, p_not text default '')
returns void language plpgsql as $$
begin
  update heyet.gorev set durum = p_durum, guncellendi = now(),
    govde = heyet.kayit_ekle(govde, 'Durum: ' || p_durum || '.' || coalesce(' ' || nullif(p_not, ''), ''))
  where id = p_id;
  if not found then raise exception 'Görev bulunamadı: %', p_id; end if;
  perform heyet.ruzname_ekle('reis', 'gorev-durum', p_id || ' → ' || p_durum || coalesce(': ' || nullif(p_not, ''), ''));
end $$;

create or replace function heyet.gorev_teslim(p_id text, p_ozet text, p_yurutucu text default null)
returns void language plpgsql as $$
declare g heyet.gorev; kim text;
begin
  select * into g from heyet.gorev where id = p_id;
  if not found then raise exception 'Görev bulunamadı: %', p_id; end if;
  kim := coalesce(p_yurutucu, g.atanan);
  update heyet.gorev set durum = 'incelemede', guncellendi = now(), teslim = heyet.kisalt(p_ozet, 300),
    govde = heyet.kayit_ekle(govde, 'Teslim (' || kim || '): ' || p_ozet) where id = p_id;
  if heyet.uye_mi(kim) then perform heyet.durum_yaz(kim, 'bosta', p_id || ' teslim edildi', p_id); end if;
  perform heyet.ruzname_ekle(kim, 'teslim', p_id || ': ' || p_ozet);
  if p_yurutucu = 'antigravity' then
    perform heyet.talimat_ekle('reis', p_id || ' Antigravity tarafından teslim edildi. Teslimi denetle: '
                               || heyet.kisalt(p_ozet, 160), 'sistem');
  end if;
end $$;

create or replace function heyet.gorev_devret(p_id text) returns jsonb language plpgsql as $$
declare g heyet.gorev;
begin
  select * into g from heyet.gorev where id = p_id;
  if not found then raise exception 'Görev bulunamadı: %', p_id; end if;
  if g.durum = 'tamam' then raise exception '% zaten tamamlanmış', p_id; end if;
  update heyet.gorev set yurutucu = 'antigravity', durum = 'devredildi', guncellendi = now(),
    govde = heyet.kayit_ekle(govde, 'Kullanıcı görevi Antigravity''e devretti (önceki yürütücü: ' || g.atanan || ').')
  where id = p_id;
  perform heyet.durum_yaz('antigravity', 'bekliyor', p_id || ' devralınmayı bekliyor', p_id);
  perform heyet.ruzname_ekle('kullanici', 'devir', p_id || ' Antigravity''e devredildi');
  perform heyet.talimat_ekle('reis', 'Kullanıcı ' || p_id || ' görevini Antigravity''e devretti. Bu kartı yürütme; teslimi bekle.', 'sistem');
  if g.atanan <> 'reis' then
    perform heyet.talimat_ekle(g.atanan, p_id || ' Antigravity''e devredildi. Bu kart üzerinde çalışıyorsan dur; '
      || 'o ana kadar yaptığını kaydet ve kart kaydına not düş.', 'sistem');
  end if;
  return jsonb_build_object('gorev', p_id, 'istem',
    'Bu depodaki AGENTS.md kurallarına uy. Görevi okumak için: python3 ekip/bin/ekip.py gorev goster ' || p_id
    || ' — sonra görevi yürüt; başlarken ve bitirince AGENTS.md''deki durum komutlarını çalıştır.');
end $$;

create or replace function heyet.gorev_goster(p_id text) returns jsonb language sql stable as $$
  select to_jsonb(g) from heyet.gorev g where id = p_id $$;

-- ------------------------------------------------------------------ rapor ve özet
create or replace function heyet.rapor_yaz(p_metin text) returns void language sql as $$
  insert into heyet.rapor (id, metin, guncellendi) values (1, coalesce(p_metin, ''), now())
  on conflict (id) do update set metin = excluded.metin, guncellendi = now() $$;

create or replace function heyet.ozet() returns jsonb language sql stable as $$
  select jsonb_build_object(
    'proje', (select deger from heyet.ayar where ad = 'proje'),
    'zaman', now(),
    'uyeler', (select coalesce(jsonb_agg(
        to_jsonb(u) || jsonb_build_object(
          'durum', heyet.durum_oku(u.id),
          'bekleyen', heyet.talimat_bekleyen(u.id),
          'talimatlar', (select coalesce(jsonb_agg(jsonb_build_object('id', 'T-' || lpad(t.no::text, 4, '0'),
                           'zaman', t.zaman, 'kimden', t.kimden, 'metin', t.metin, 'durum', t.durum) order by t.no), '[]')
                         from (select * from heyet.talimat where hedef = u.id order by no desc limit 12) t))
        order by u.sira), '[]') from heyet.uye u),
    'antigravity', heyet.durum_oku('antigravity'),
    'gorevler', (select coalesce(jsonb_agg(to_jsonb(g) order by g.id), '[]') from heyet.gorev g),
    'rapor', (select metin from heyet.rapor where id = 1),
    'ruzname', (select coalesce(jsonb_agg(to_jsonb(r) order by r.no), '[]')
                from (select zaman, kim, olay, metin, no from heyet.ruzname order by no desc limit 80) r)
  ) $$;

-- ------------------------------------------------------------------ dışa açık kapı (anahtarlı)
create or replace function public.heyet_api(p_anahtar text, p_islem text, p_args jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = heyet, pg_temp as $$
declare a jsonb := coalesce(p_args, '{}'::jsonb); sonuc jsonb;
begin
  if p_anahtar is null or p_anahtar <> (select deger from heyet.ayar where ad = 'anahtar') then
    raise exception 'Yetkisiz';
  end if;
  case p_islem
    when 'ozet' then sonuc := heyet.ozet();
    when 'durum_oku' then sonuc := heyet.durum_oku(a->>'uye');
    when 'durum_yaz' then perform heyet.durum_yaz(a->>'uye', a->>'hal', a->>'su_an', a->>'gorev',
                                                 coalesce((a->>'adimlari_sifirla')::boolean, false));
    when 'adim' then
      perform heyet.adim_ekle(a->>'uye', a->>'arac', a->>'ozet');
      sonuc := case when coalesce((a->>'ilet')::boolean, true) then heyet.talimat_ilet(a->>'uye') else '[]' end;
    when 'talimat_ekle' then sonuc := heyet.talimat_ekle(a->>'hedef', a->>'metin', coalesce(a->>'kimden', 'reis'));
    when 'talimat_ilet' then sonuc := heyet.talimat_ilet(a->>'uye');
    when 'talimat_bekleyen' then sonuc := to_jsonb(heyet.talimat_bekleyen(a->>'uye'));
    when 'gorev_yeni' then sonuc := to_jsonb(heyet.gorev_yeni(a->>'baslik', a->>'atanan', a->>'govde', a->>'model'));
    when 'gorev_durum' then perform heyet.gorev_durum(a->>'id', a->>'durum', coalesce(a->>'not', ''));
    when 'gorev_teslim' then perform heyet.gorev_teslim(a->>'id', a->>'ozet', a->>'yurutucu');
    when 'gorev_devret' then sonuc := heyet.gorev_devret(a->>'id');
    when 'gorev_goster' then sonuc := heyet.gorev_goster(a->>'id');
    when 'rapor_yaz' then perform heyet.rapor_yaz(a->>'metin');
    when 'ruzname_ekle' then perform heyet.ruzname_ekle(a->>'kim', a->>'olay', a->>'metin');
    else raise exception 'Bilinmeyen işlem: %', p_islem;
  end case;
  return coalesce(sonuc, '{"tamam": true}'::jsonb);
end $$;

revoke all on function public.heyet_api(text, text, jsonb) from public;
grant execute on function public.heyet_api(text, text, jsonb) to anon, authenticated;
