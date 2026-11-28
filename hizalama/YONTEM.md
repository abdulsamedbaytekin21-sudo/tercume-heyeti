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

## hat-0.3 (G-032) değişiklikleri
- **Cilt/fass parametresi:** `--cilt N` (varsayılan 1) girdi `veri/kasa/metin/konukN/temiz.jsonl`, çıktı (cilt 1: `fusus-konuk`, N>=2: `fusus-konuk-cN`) ve kimlik önekini (`fusus-konuk-fNN`, N>=2: `fusus-konuk-cN-fNN`) seçer; `--fass` cilt içindeki sıradır. Fass başlığı sayfa alt sınırı cilt 1'de 40, diğer ciltlerde 0 (`fass_sinirlari(..., min_sayfa)`). `--onceki` verilmezse çıktı dizinindeki en yeni `surum/hat-X.Y` kullanılır (kimlik koruma).
- **Sahte pasaj (Y-1):** (a) "Sehl dedi:" gibi tanıtıcı ':' ile biten Türkçe + kısa (<=2 blok) satır içi Arapça + ardından gelen Türkçe, aynı Türkçe paragraftır (yalnız önceki seri bir Arapça Fusûs pasajının hemen ardındaysa, îzâh yoksa ve etiket ("Şiir:") değilse); (b) Arapça ardından gelen Türkçe `[...]` neşir mealiyle başlıyorsa (sayfa işareti hariç) ve Arapça <= 3 blok ise devam; (c) harfî tercümesi boş "pasaj" (şerhteki Arapça alıntı + "Ya'ni") ve Arapçası bir önceki pasajda geçen kısa pasaj `alinti`ya taşınır (`onceki_sahte_pasaj`, `onceki_pasaj_id`).
- **Ö-1 kısa artık:** Türkçe bölücü açık “ ” tırnağı içinde bölmez; "Tâ ki ..." öncekine, "Görmez misin?" gibi kısa hitap sonrakine bağlanır; atıf parantezinden sonra küçük harfli sözcük gelirse atıf cümle sonu değildir (K-B). DP sonrası `artik_oge_suphe` bayrağı (kusur): n-m satırda <=3 sözcüklük Türkçe (ya da <=4 sözcüklük, ayet/«» içermeyen Arapça) birimin kök örtüşmesi sıfır (katı eşleşme) ya da "İmdi/Binâenaleyh/Böyle olunca/Şu hâlde" birimi sayısı Arapça "فـ" sayısından fazla. Şüpheli satırın iki komşusu `komsu_suphe` ile öğretici dışı.
- **Ö-2:** `nasir_ilavesi` dolu ve `tr_satir_ici_arapca` boş satır `ilave_karsiliksiz` (kusur), öğretici dışı.
- **K-1:** Arapça köşeli parantez (neşir ilavesi) çıkarılır: `ar` temiz, `ar_parantezli` ham, pasajda `nasir_ilavesi_ar`.
- **Sözcük oranı sabit:** ln(TR/AR) ortalaması 0.24, sd0 0.12, sd(n)=max(0.12, sqrt(sd0^2 + 0.3/n)) (fass 1-14 havuzu, 347 pasaj). Pasaj puanı artık yalnız kendi metnine bağlı. Fass içi medyan yerine sabit parametre, çeviri üslubu daha uzun fasslarda (F5: oran 1.44) pasaj `insan` sayısını artırır; kısa pasajlar daha hoşgörülü değerlendirilir.
- **Kenar bandı:** 0.55 <= pasaj güveni < 0.60 `bant: kenar`; pasaj kaydı `insan` kalır, satırlar kendi güvenine (>= 0.60) göre karar verir. Tek birimli pasajda (1 Arapça ya da 1 Türkçe birim) kenar bandında satır güveni uzunluk + leksik ile hesaplanır.
- **Yapısal tamlık kontrolü** (`tamlik_kontrol`, her koşuda): pasaj/alıntı Arapçası kaynak bloklarla aynı; her Arapça blok bir pasaj/alıntı/başlık/satır içi Arapça kaydına bağlı; cümle satırları birleşince pasaj Arapçası ve Türkçesi çıkıyor. Hata `TAMLIK HATASI` olarak stderr'e yazılır, özet satırında `tamlık`.
- Kimlik koruma: cümle kimliği çok birimli eski satırın ilk birimiyle de eşleşir (önek karşılaştırması).

## hat-0.3, cilt 2 notları (G-034)
- `--cilt 2`: girdi `konuk2/temiz.jsonl`, çıktı `veri/kasa/hizalama/fusus-konuk-c2/`, kimlik `fusus-konuk-c2-fNN-pNNNN-cNN`; fass numarası cilt içi sıradır (1 = Fusûs 15. fass, Îsâ). Son fassın sonu `LUGATÇE|KAYNAKÇA|ÂYET İNDEKSİ` başlığında biter (`fass_sinirlari(..., son_baslik)`); Lugatçe, Kaynakça ve dizinler Fusûs metni değildir.
- Mûsâ fassı iki kez şerh edilmiştir (başlıkta `[2. Şerh]`, PDF s. 513); cilt-içi fass 11 ve 12 aynı Arapça fassın iki şerhidir. Fass 12 kayıtlarında `serh_no: 2`. Fass 12 pasajlarının yalnız 14/46'sı fass 11 ile aynı Arapçayla başlar (ikinci şerh Arapçayı farklı bölümlüyor); aynı Arapçanın iki Türkçesini eğitimde çift sayma kararı Reis'indir.
- Yankı kuralı: Türkçe paragraf, hemen önceki Fusûs Arapçasının parçalarını satır içi yeniden alıntılıyorsa (<=3 blok, Arapçası öncekinin içinde aynen geçiyor) yeni pasaj açılmaz. Cilt 1 çıktısı bu kuralla bayt bayt aynı kaldı.

## hat-0.3.1 (G-037)
- **Komşu bayrağı yönlü:** `artik_suphe` kaymanın yönünü döndürür (`kayma_yonu`: `onceki` | `sonraki` | `ikisi`): şüpheli birim satırın ilk birimiyse önceki, son birimiyse sonraki komşuya `komsu_suphe` konur (fazla "fe-" birimi sondaki birimdir). Çıktıda şüpheli satırda `kayma_yonu` alanı.
- **Farsça ye:** `farsca_mi` Farsça ye (ی, U+06CC) için en az 3 adet ve harflerin %3'ünü ister; Arapça metindeki tek `تعالی` artık `dil_etiketi_tutarsiz` doğurmaz. گ چ پ ژ ۀ ہ eskisi gibi %1 eşikli.
- **Tamlık kontrolü:** araya yalnız `isaret` / `baslik_sayfa` / `dipnot` giren ardışık Arapça bloklar farklı kayıtlara (pasaj/alıntı) düşerse `TAMLIK HATASI` (bölünmüş Fusûs Arapçası).
- **`dislama_birimi`:** aynı Arapça fass başlığını taşıyan şerhler (cilt 2 Mûsâ, iki şerh) aynı kimliği taşır; eser bazında dışarıda bırakmada tek birimdir. İki tercüme eğitimde kalır (G-035 kararı).
- Girdi G-036 çıkarımı (Arapça blokta rakam yok, `[25¹/47]` tek `isaret` bloğu; Arapça blokta isteğe bağlı `dipnot_ref` hizalamada kullanılmıyor, Arapça tarafa karışmaz).
