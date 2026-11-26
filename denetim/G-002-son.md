# Denetim G-020 — Şema son hali (G-002 düzeltmeleri + G-019 eki)

Denetçi: Mümeyyiz · Tarih: 2026-11-26 · Denetlenen: `db/` son değişikliği `243b61a` (çalışma ağacı `d965a91`, `001_cekirdek.sql` sha256 `680dd38dd285…`)
Önceki rapor: `denetim/G-002.md` (G-009). Bu kısa bir yeniden denetimdir: kapanış doğrulaması + G-019 eki, kapsam genişletilmedi.

## Hüküm: ŞARTLI KABUL

E1, E2, E3, Ö2 ve Ö4 kapandı; bunları bizzat yeniden denedim. G-019 eki (`kasa.arapca_birim`) yeni bir izolasyon açığı getirmiyor.
Şart iki ucuz düzeltme. İkisi de veri yüklenmeden önce `001` üzerinde yapılabilir:
- **Y1 (Önemli):** Lisansı `bilinmiyor` olan Arapça baskı (bu varsayılan değer) omurgaya giriyor. Sonradan telifli çıkarsa metni `omurga.surum_gecmisi`'nde kalıcı olarak kalıyor.
- **Y2 (Önemli):** `degisiklik` NULL'a çekilerek bildirimsiz güncelleme yapılabiliyor.

Yükleme kartları (G-016–G-018) Arapça baskı getirmeden önce Y1 kapanmalı. Kavram ağına ilk güncelleme yazılmadan önce de Y2 kapanmalı.
Düzeltmeden sonra yalnız Y1 ve Y2 denemelerinin yeniden koşulması yeter, tam denetim gerekmez.

## Ortam ve yöntem
- PostgreSQL 16.15, pgvector 0.6.0, pg_trgm kuruldu. Geçici küme `/var/tmp/g020_pg` üzerinde açıldı (port 55440, yalnız soket). İş bitince durduruldu ve silindi.
- Roller: `u_om` (omurga yazar), `u_ka` (kasa yazar), `u_ok` (kasa okur), hepsi LOGIN.
- Tohum veri: e001 Fusûs, e002 Nusûs, e003 Konuk (üst eseri e001). Baskılar: Arapça serbest b0a01/b0a02, Konuk `serh/tr/telifli` b0003, Nusûs telifli tahkik b0ee1 (`nesir/ar/telifli`), sonradan Nusûs `ceviri/tr` b0f02. Kurum A ve B; her kurumun 1 Türkçe birimi var, A'nın 1 Arapça kasa birimi var. Model boyutu 3.
- Her deneme kendi `BEGIN … ROLLBACK` işleminde ilgili rolle koşuldu. Kimlikler `00000000-0000-0000-0000-<onaltılık>` biçiminde kısaltıldı: @a0001, @bb001 vb.
- Göç: `000` → `001` up → down → up sırası `ON_ERROR_STOP=1` ile hatasız geçti. Aynı kümede ikinci VT'ye up yapıp ardından down yaptım; ilk VT 22 tabloyla ayakta kaldı. Ö3 de kapalı.

## Kapanış doğrulaması (bizzat koşuldu; bu tablo ile G-019 tablosu ve yeni bulgular birlikte yaklaşık 100 deneme)

| Bulgu | Deneme | Sonuç |
|---|---|---|
| E1 | Omurga birimi `serh/tr/telifli`, `nesir/tr/serbest`, `ceviri/ar/serbest`, `nesir/ar/telifli` baskıya bağlanmak istendi | 4/4 reddedildi (tetikleyici dil/tür/lisans mesajıyla) |
| E1 | Birim varken baskıda `tur→ceviri`, `lisans→telifli`, `dil→tr`, `eser_kimlik` değişimi denendi | 4/4 reddedildi (bileşik FK) |
| E1 | Birimi Türkçe baskıya taşıma ve `baski_omurga_uygun=false` yazma denendi | Reddedildi (tetikleyici / CHECK) |
| E1 | `turkce_birim` Arapça baskıya bağlanmak istendi; Türkçe şerhe bağlandı; kasa birimi varken baskıda `dil→ar` denendi | Arapça reddedildi, şerh kabul edildi (doğru), `dil→ar` reddedildi |
| E1 | Kasa yazarı omurgaya baskı yazmayı denedi | `permission denied` |
| E2 | `cift_uye`'ye elle `eser_kimlik=e002` yazıldı | Yok sayıldı, değer e001 olarak türedi |
| E2 | `omurga.vektor`'e yanlış eser yazıldı; eser boş bırakıldı | Yanlış eser reddedildi (FK); boş bırakılınca e001 türedi |
| E2 | `metin_birimi`/`turkce_birim` `eser_kimlik` UPDATE ile değiştirilmek istendi | Değer baskıdan yeniden türedi, değişmedi |
| E2 | Tanıklıkta eser e002 yazıldı, metin birimi e001'e ait | Reddedildi (FK) |
| E2 | Fusûs Arapça + Konuk Türkçe çifti kuruldu, test eseri e001 | `dislama_kumesi` = {e001, e003}; çift dışlandı, 0 satır kaldı |
| E2 | Farklı ağaçtan üye eklendi; aynı çiftte üye UPDATE ile başka ağaca taşındı; `ust_eser_kimlik` döngüsü kuruldu | 3/3 reddedildi |
| E3 | A oturumunda B'ye bağlanma denendi: B'nin birimine çift üyesi, `ust_birim`, B'nin çiftine üye, B çiftinden `terim_karari`, B birimine vektör | 5/5 reddedildi |
| E3 | A oturumunda var olmayan çift kimliği ile B'nin çift kimliği denendi (`kurum_kimlik=A`) | İkisi de aynı FK hatasını verdi; kâhin kapandı (istisna: aşağıda K-1) |
| E3 | A, B'nin satırlarını saydı | 0 |
| Ö2 | Omurgada, kasa Türkçe ve kasa Arapça tablolarda aynı `sira=1` kök birim tekrarlandı | 3/3 reddedildi (`NULLS NOT DISTINCT`) |
| Ö2 | B, A'nın baskısına kendi satırını ekledi: Türkçe `sira=2`, Arapça `sira=1` | Kabul edildi; kurum dahil benzersizlik doğru |
| Ö2 | `terim` aynı (lafız, kök NULL, dil) ile tekrarlandı | Reddedildi |
| Ö4 | Omurga ve kasa yazarlarıyla `surum_gecmisi` DELETE/UPDATE/INSERT, `varlik_kayit` INSERT, `surum_izle()` doğrudan çağrısı, `kayit_ekle`, TRUNCATE denendi | 8/8 `permission denied` |
| Ö4 | Yazar güncelleme yaptı (elle `surum=1` yazarak) | `surum`=2, geçmişte 1 satır, `kullanici=u_om`; kasa Arapça birim de geçmişe yazdı |
| degisiklik | Bildirimsiz güncelleme; `ozet` eksik bildirim; doğru bildirim; NULL ile girilmiş kaydı bildirimsiz güncelleme | Red / red (CHECK) / kabul, eski bildirim `surum_gecmisi.eski` içinde / red |
| degisiklik | Bildirim NULL'a çekildi; eski bildirim yeniden kullanıldı (A→B→A); `kart`/`ozet` boş bırakıldı | **3/3 kabul edildi** (Y2, K-2) |

## G-019 eki: `kasa.arapca_birim` (bizzat koşuldu)

| Deneme | Sonuç |
|---|---|
| Telifli Arapça baskıya birim eklendi (elle `eser_kimlik=e001` yazılarak) | Kabul edildi; eser e002 olarak türedi, sürüm 1 |
| Serbest Arapça baskıya / Türkçe baskıya birim eklenmek istendi; birim UPDATE ile serbest baskıya taşınmak istendi; `baski_kasa_arapca_uygun=false` yazıldı | 4/4 reddedildi |
| Kasa birimi varken baskıda `lisans→serbest` ve `lisans→bilinmiyor`, `dil→tr`, `eser_kimlik` değişimi denendi | 4/4 reddedildi (bileşik FK) |
| Telifli baskıya omurga birimi eklenmek istendi; telifli kasa birimine omurga tanıklığı bağlanmak istendi | İkisi de reddedildi |
| Çift üyesi `kasa_arapca_birim_kimlik` + Türkçe üye (aynı ağaç) eklendi; ar üyede iki Arapça kimlik birden verildi; hiçbiri verilmedi | Kabul (eser türedi) / CHECK reddi / tetikleyici reddi |
| Kasa vektörü Arapça birime bağlandı; iki hedef birden verildi; yanlış boyut verildi | Kabul (`vektor_eser` e002) / CHECK reddi / boyut reddi |
| Dışlama: test e002 ile Arapça birim/çift/vektör sayıldı; test e001 ile sayıldı | e002: 0/0/0; e001: 1/1/2 (doğru) |
| B oturumu: A birimini görme, `ust_birim`, çift üyesi, vektör, A adına yazma, kurum değiştirme denendi | 0 satır; 5/5 reddedildi |
| Kurum ayarsız okuma; okur yazma; omurga rolü okuma denendi | 0 satır; `permission denied`; `permission denied for schema kasa` |
| ENABLE+FORCE RLS; haklar: okur SELECT, yazar INSERT, omurga yazarı SELECT, yazar TRUNCATE kontrol edildi | RLS açık; t/t/f/f |
| Kimlik değiştirme; silinen kimlikle yeniden ekleme denendi | Reddedildi |

## Yeni bulgular

**Y1 — Önemli: `lisans_sinifi='bilinmiyor'` (varsayılan değer) omurgaya açılıyor ve geri dönüşü kirli.**
`omurga_uygun = dil='ar' AND tur<>'ceviri' AND lisans_sinifi<>'telifli'` tanımı bilinmeyeni serbest sayıyor. `kasa_arapca_uygun` da `bilinmiyor`'u dışarıda bırakıyor.
Bu yüzden lisansı belirsiz Arapça baskının gidebileceği tek yer omurga. Envanterde bu durum somut olarak var: Afîfî neşri (Kahire 1946, tahkikli), muhakkik hakkı belirsiz.
```sql
-- u_om
INSERT INTO omurga.baski(kimlik,eser_kimlik,tur,dil) VALUES (@b0b11,@e002,'nesir','ar');          -- lisans verilmedi → bilinmiyor
INSERT INTO omurga.metin_birimi(kimlik,baski_kimlik,...,metin,...) VALUES (@a0b01,@b0b11,...,'TAHKIK METNI',...);  -- KABUL; omurga_uygun=t
DELETE FROM omurga.metin_birimi WHERE kimlik=@a0b01;                                           -- telifli çıktı, temizleme
UPDATE omurga.baski SET lisans_sinifi='telifli' WHERE kimlik=@b0b11;                           -- KABUL
SELECT count(*) FROM omurga.surum_gecmisi WHERE eski->>'metin'='TAHKIK METNI';                 -- 1 (silme de, düzeltme UPDATE'i de bırakıyor)
```
Bu kalıntıyı hiçbir istemci rolü silemez (Ö4'ün doğru sonucu). Omurga okurları ve kasa okurları ise okuyabilir. Yani telifli metin ortak omurgada kalıcı olarak kalıyor.
Öneri: `omurga_uygun` yalnız `lisans_sinifi='serbest'` olsun. `bilinmiyor` Arapça baskı ya kasaya gitsin (`kasa_arapca_uygun` buna genişletilir) ya da hiçbir yere yazılmasın.
Önerdiğim varsayılan, bilinmeyenin kasaya gitmesi. Bu "telifli Arapça kasada" kararıyla da tutarlı. Gerekirse omurgadan arındırma için süper kullanıcıya bağlı, belgelenmiş bir `surum_gecmisi` temizleme işlemi tanımlansın.
Karar Reis'in, `kararlar.md`'ye yazılmalı.

**Y2 — Önemli: `degisiklik` bildirimi NULL'a çekilerek atlanabiliyor.**
`surum_izle` yalnızca "önceki değerden farklı mı" diye bakıyor. CHECK ise `degisiklik IS NULL` değerine izin veriyor.
```sql
UPDATE omurga.terim SET lemma='x', degisiklik=NULL WHERE kimlik=@cc001;   -- KABUL, sürüm 2, bildirim yok
```
Böylece README'deki "güncelleme farklı bir `degisiklik` taşımak zorundadır" güvencesi tek satırla delinebiliyor.
Öneri: UPDATE'te `NEW.degisiklik IS NOT NULL` zorunlu olsun. INSERT'te NULL kalabilir.

## Küçük
- **K-1 — Kurumlar arası varlık kâhini (Ö1'e bağlı).** BEFORE tetikleyicisi `cift_uye_doldur` süper kullanıcı sahipli bir SECURITY DEFINER işlevi, bu yüzden RLS'yi atlıyor. RLS `WITH CHECK` ise tetikleyiciden sonra çalışıyor.
  A oturumu `kurum_kimlik=B` yazınca hata mesajı farklılaşıyor: B'nin var olan birimi için "row-level security", var olmayan için "birimi bulunamadi" dönüyor (K-a/K-b).
  B çiftine farklı ağaçtan üye denenince "ayni agac" hatası dönüyor; bu da B'nin çiftinin hangi ağaca ait olduğunu sızdırıyor (K-c).
  Ö1 açıkken B zaten okunabildiği için ek risk küçük. Yine de tetikleyicinin başına `IF NEW.kurum_kimlik IS DISTINCT FROM kasa.gecerli_kurum() THEN RAISE …` eklemek tek satırlık bir iş.
  `turkce_birim_doldur`/`arapca_birim_doldur` yalnız omurgayı okuduğu için bu sorunu taşımıyor.
- **K-2 — Bildirim niteliği.** Eski bildirimin yeniden kullanımı (A→B→A) ve boş `kart`/`ozet` kabul ediliyor. Mevcut ölçüt aynı `kart`/`ozet` ile yalnız ek bir anahtar taşıyan bildirimi de "yeni" sayıyor.
  Öneri: `kart ~ '^G-[0-9]{3,}$'` ve `ozet` boş olmasın. Ayrıca kavram kayıtlarında DELETE hakkı açık ve bildirimsiz (eski hal geçmişe gidiyor); `geri_cekildi` ilkesiyle tutarlılık için yazarın DELETE hakkı kaldırılabilir.
- **K-3 — Eser bağı sonradan değişince çift değişmezi bozuluyor.** Konuk–Fusûs çifti varken `UPDATE eser SET ust_eser_kimlik=e002` (ya da NULL) kabul ediliyor; mevcut çiftin üyeleri artık farklı köklerde.
  Dışlama bu durumda bile çifti Arapça üyesi üzerinden yakalıyor. Ama `ust_eser_kimlik` NULL'a çekilirse Konuk'un Türkçe kasa vektörleri (`vektor_eser` e003) Fusûs dışlamasından kaçar.
  Öneri: bağlı kasa/omurga birimi olan eserde `ust_eser_kimlik` değişimi reddedilsin ya da `degisiklik` benzeri bir bildirim zorunlu olsun.
- **K-4 — README sapması.** README "kimlik yeniden kullanım denetimi kasada yalnız çağıran kurumun görünürlüğü içindedir" diyor. Oysa definer işlev RLS'yi atladığı için denetim global: A, B'nin silinmiş kimliğini kullanamadı (KT). Bu davranış daha güvenli; README düzeltilsin.

## Değişmeyen (kapsam dışı, bilgi)
- Ö1 (`heyet.kurum` beyanı) pilot kararıyla açık: A oturumu ayarı B'ye çekince `B KONUK TR` okunuyor. Karar `kararlar.md`'de, ikinci kurumdan önce kapanacak.
- Telifli Arapça metnin `anlam.tanim`/`taniklik.alinti` alanlarına elle kopyalanması teknik olarak mümkün (AB32 kabul edildi). README'de belirtilmiş; kural/inceleme sınırı geçerli.

## Örneklem ve sınır
Tam kapsam değil, kapanış odaklı bir denetim. G-009'un engelleyici ve önemli maddeleri ile G-019 ekinin bütün yüzeyi denendi.
Yeniden denenmedi: G-010 şema maddeleri (onay kuralları, `iliski`), K2/K3/K5 ve V1 HNSW. Bunlar Mimar'ın README tablosunda raporlanmış ve bu turda dokunulan kodla ilişkili değil.
