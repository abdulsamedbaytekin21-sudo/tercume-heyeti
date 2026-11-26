# Tercüme Heyeti

Arapça klasik metinler için kaynaklı ve güven notlu çeviri sistemi. Pilot kapsamı Ekberî gelenek.
Proje bir Claude Code ajan heyeti tarafından yürütülür: siz yalnızca **Reis** ile muhatap olursunuz.

- Mimari: `proje/mimari.md`
- Kararlar: `proje/kararlar.md`
- Reis'in talimatnamesi: `CLAUDE.md`
- Üyeler: `.claude/agents/`
- Antigravity kuralları: `AGENTS.md`

## Panel

Panel bir Claude sayfasıdır; telefondaki Claude uygulamasından da açılır ve bilgisayar kapalıyken de çalışır:
https://claude.ai/artifact/VMVGm7mxQpDUS5ugj1me6T

İlk açılışta Supabase bağlantısını kullanma izni ister. Kayıtlar Supabase'deki `tercume-heyeti` projesinin
`heyet` şemasında durur; sayfa bunlara sizin bağlı Supabase hesabınız üzerinden erişir, sayfada anahtar yoktur.

## Ekibi çalıştırmak

### Telefondan ya da bilgisayar kapalıyken (Claude Code bulut oturumu)

1. claude.ai/code (ya da Claude uygulamasında Code) üzerinden bu depoyla yeni bir oturum açın.
2. Ortam ayarlarında bir kez şunları yapın:
   - **Ağ erişimi:** `*.supabase.co` alan adına izin verin (ya da tam erişim seçin).
   - **Ortam değişkeni:** `HEYET_ANAHTAR` = size ayrıca verilen erişim anahtarı.
3. Oturumda Reis'e "Heyeti çalıştır" ya da "Bekleyen talimatları işle" demeniz yeterli.

### Bilgisayarda (Claude Code)

1. Depo kökünde `.heyet-anahtar` adlı bir dosyaya erişim anahtarını yazın (bu dosya git dışında tutulur).
2. Depo klasöründe `claude` komutuyla Claude Code'u açın. Yönetici her zaman Opus'tur (`.claude/settings.json`).

### Antigravity'e görev devretmek

Panelde bir görev kartını açıp **Antigravity'e devret**'e iki kez basın. Panel, Antigravity'e yapıştırılacak
kısa istemi gösterir. Antigravity bu depoyu açtığında `AGENTS.md` kurallarına uyar ve teslimi panele düşer.

## Komut satırı

```
python3 ekip/bin/ekip.py gorev liste
python3 ekip/bin/ekip.py gorev goster G-001
python3 ekip/bin/ekip.py talimat mimar "..." --kimden kullanici
python3 ekip/bin/ekip.py ozet
```

Erişim anahtarı yoksa araç yerel dosyalarla (`ekip/durum`, `ekip/talimat`, `ekip/gorevler`) çalışır ve
yerel panel `python3 ekip/panel/sunucu.py` ile http://127.0.0.1:4317 adresinde açılır.

## Veritabanı

`ekip/sql/001_heyet.sql` ortak kayıt şemasını kurar. Dışarıya açık tek kapı `public.heyet_api` işlevidir ve
erişim anahtarı olmadan hiçbir şey yazmaz. Ücretsiz Supabase projeleri bir hafta hiç kullanılmazsa duraklatılır;
Supabase panelinden tek tıkla yeniden başlatılabilir.
