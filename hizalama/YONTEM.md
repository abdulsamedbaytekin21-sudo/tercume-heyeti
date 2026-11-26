# Hizalama hattı hat-0.1 (G-003, Konuk Fusûs şerhi, fass-01)

Kod: `hizalama/hat.py`, test: `cd hizalama && python3 -m unittest`. Çıktı (telifli) yalnız `veri/kasa/hizalama/fusus-konuk/`.
Çalıştırma: `python3 hizalama/hat.py --fass 1` (girdi: `veri/kasa/metin/konuk1/temiz.jsonl`).

1. Çapa: Arapça başlık "فص حكمة ..." (sayfa > 40) -> sonraki fass başlığı. Sondaki İbtidâ/İntihâ kolofonu dışarıda.
2. Pasaj: Arapça blok serisi + hemen ardından gelen `terceme` serisi. "Ya'ni ..." paragrafı Konuk îzâhıdır (`tr_izah`), çifte girmez.
   "Tercüme:/Ya'ni:/Îzâhen" ile başlayan ya da Farsça işaretli seri, ayet/hadis/beyit alıntısıdır (`fass-NN.alinti.jsonl`, `egitim_cifti: false`).
   tr + Arapça + küçük harfle başlayan tr = satır içi Arapçanın böldüğü Türkçe paragraf; birleştirilir, Arapça `{ar: ...}` ve `tr_satir_ici_arapca` olarak işaretlenir.
   Pasaj Arapçasıyla >=%60 örtüşen, eşsiz kalmış Arapça ibare `tur: varyant` (nüsha farkı).
3. Mütercim ilavesi: Türkçe `[...]` -> `ilaveler`; `tr_ilavesiz` hizalamada kullanılır. Parantezli atıf/açıklamalar `parantezler`. Dipnotlar `fass-NN.dipnot.jsonl`, atıf `dipnot_ref`.
4. Cümle/öbek: Arapça '،؛.؟﴾', Türkçe ';' ve büyük harf öncesi '.?!' ile bölünür; monoton n-m DP (1-1, 1-2, 2-1, 2-2, 1-3, 3-1, 2-3, 3-2, atlama).
   Maliyet = Gale-Church uzunluk + bağlaç çapası + **leksik kök-iskelet örtüşmesi** (Arapça kök ünsüzleri ~ Osmanlıca Türkçedeki ünsüz iskeleti).
5. Güven: pasaj = yapı tabanı 0.92 x sözcük oranı sapması x leksik örtüşme (- kısalık/satır içi/Farsça cezaları). Cümle = 0.45 uzunluk + 0.55 leksik, tavan 0.9. < 0.60 -> `inceleme: insan`.
   DP eşleşmelerinin >%40'ı düşük güvenliyse cümle düzeyi kurulmaz, pasaj düzeyinde bırakılır.
6. Gömme modeli: bu ortamda LaBSE/BGE-M3 yok, ölçülmedi (`model: yok`). Leksik çapa ölçümü: fass-01'de doğru pasaj çiftlerinde ort. 0.61 (min 0.40), pasaj çaprazında 0.14 (p95 0.33); 1-1 cümlelerde doğru 0.55, komşuya kaydırılmış 0.09.
