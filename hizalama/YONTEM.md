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

## hat-0.2 (G-027) değişiklikleri
- Girdi G-026 temiz.jsonl (satır içi Arapça artık doğru sırada; dipnot Arapçası dipnotta `{ar: ...}`).
- Satır içi Arapça birleştirme kuralı: tr + ar + tr üçlüsünde sonraki Türkçe küçük harf/`(`/`]` ile başlıyorsa ya da önceki Türkçe cümle bitmemişse (ve Arapça <= 6 blok) paragraf devam sayılır.
- Köşeli parantez = neşir heyeti ilavesi (G-025). Çiftin `tr` alanı parantezsizdir (köşeli parantez ve atıf parantezi "(Nisâ, 4/1)" düşer). **hat-0.2.1 (Reis kararı):** satır içi Arapça ibareler `tr` içinde yerinde kalır, aralıkları `tr_satir_ici_arapca` = [{metin, bas, son}] ile işaretlenir (satırda da); köşeli parantez içindeki Arapça ilaveyle birlikte düşer. `satir_ici_arapca` bayrağı `butunluk.bilgi`'ye taşındı, `ogretici_uygun`'u düşürmez; `bayraklar` yalnız kusurları içerir. Parantezli hâl `tr_parantezli`, ilaveler `nasir_ilavesi`, atıflar `atiflar`, satır içi Arapça `tr_satir_ici_arapca`. Cümle bölücü bu bölgelerin içinde bölmez, parantez iki satıra yayılmaz.
- Neşir varyantı: dipnot metnindeki Arapça (`ar_parcalari`) atıf numarasıyla pasaja bağlanır (`nasir_varyantlari`, dipnot kaydında `bagli_pasaj`, `tur: dipnot_varyant|dipnot_arapca`). Önceki "%60 örtüşme" varyant kuralı kaldırıldı; alıntı kayıtları artık `varyant` etiketi taşımaz.
- Bütünlük bayrağı `butunluk{durum: temiz|kontrol, bayraklar[]}`: `satir_ici_arapca`, `tire_belirsiz` (satır sonu tire birleştirmesi: iki yarı da cilt sözlüğünde varken birleşik biçim yok), `parantez_dengesiz|parantez_siniri`, `dil_etiketi_tutarsiz` (blok `dil` etiketi ile harf/işlev sözcüğü tespiti çelişiyor), `tr_icinde_arapca_harf`, `ar_icinde_latin_ya_da_bozuk`, `cumle_kurulamadi`. `ogretici_uygun` = inceleme hayır ve bayraksız.
- Kimlik koruma: `--onceki` dizinindeki önceki sürümden pasaj (Arapça başlangıcı), cümle (pasaj + Arapça başlangıcı) ve alıntı (Arapça başlangıcı) kimlikleri alınır; yeni birimler yeni numara alır. Önceki sürüm çıktıları `surum/hat-0.1/` altında.
- `duzey: cumle_kurulamadi` (K-3): cümle düzeyi kurulamayan pasaj satırı cümle tüketicilerine karışmaz. `dil` alanı alıntıda harf/işlev sözcüğü tespitidir, orijinal etiket `dil_etiketi` (K-4). `tr_izah_tamam` / `tr_izah_serhten_devam` îzâh kesikliğini gösterir (K-2). Cümle güvenindeki pasaj tavanı +0.05 -> +0.2 (K-5).
