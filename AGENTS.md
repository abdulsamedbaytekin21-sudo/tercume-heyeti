# Antigravity için çalışma kuralları — Tercüme Heyeti

Bu depo, Claude Code'da çalışan bir ajan heyeti tarafından yönetiliyor. Kullanıcı bazı görevleri heyetten alıp
sana (Antigravity) devredebilir. Bu dosya senin heyetle uyumlu çalışman için kuralları içerir.

## Sana devredilen görev
- Devredilen görevi şu komutla oku: `python3 ekip/bin/ekip.py gorev goster G-xxx`. Yalnızca o kartı yürüt.
- Komutun ortak kayda ulaşması için depo kökünde `.heyet-anahtar` dosyası (ya da `HEYET_ANAHTAR` ortam değişkeni) bulunmalıdır.
- Proje bağlamı: `proje/mimari.md` ve `proje/kararlar.md`. Kararlara aykırı iş yapma; aykırılık gerekiyorsa teslim notunda gerekçelendir.
- Başka kartlara, `.claude/` klasörüne ve `CLAUDE.md`'ye dokunma.

## Durum bildirimi
Heyetin panelinde görünmek için şu komutları kullan:

```
python3 ekip/bin/ekip.py durum antigravity "Ne yaptığın, tek cümle" --gorev G-xxx
python3 ekip/bin/ekip.py gorev teslim G-xxx --yurutucu antigravity --ozet "Ne yapıldı, nerede, açık kalan ne"
```

Teslimden sonra görev `incelemede` durumuna geçer; heyetin Reis'i ve Mümeyyiz'i teslimi kabul ölçütüne göre denetler.

## Değişmez ilkeler
- Arapça metin, Türkçe çevirinin dayandığı baskıdan alınır.
- Telifli çeviriler ve türevleri `veri/kasa/` altında kalır; başka yere kopyalanmaz.
- Orijinal metin dosyaları değiştirilmez; her dönüşüm ayrı dosyaya yazılır.
- Emin olmadığın bilgiyi kesinmiş gibi yazma; "doğrulanmadı" diye işaretle.
