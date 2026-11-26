# Denetim: G-005 gömme test setinin Arapça ve ıstılah gözden geçirmesi (G-014)

Denetleyen: Istılahçı (opus). Tarih: 2026-11-26. Denetlenen: `degerlendirme/gomme_testi.jsonl` sürüm 1
(1 meta, 69 belge, 50 sorgu). Dosya değiştirilmedi.

**Hüküm: ŞARTLI KULLANILABİLİR.** Arapça genel olarak doğru ve ıstılah tanımlarının çoğu Kâşânî/Cürcânî/Kayserî
çizgisiyle uyumlu. Uydurma ıstılah yok. Ancak 2 belgede ve 1 sorguda **anlam hatası** var (B25, B24 kısmen, Q31),
6 sorguda altın etiket (ilgili / zor_negatif) Ekberî kavram ilişkilerine göre yanlış ya da ekole bağlı.
Bunlar düzeltilmeden lafız/anlam ayrımı ölçen sonuçlar (özellikle `tuzak` oranı) karar dayanağı yapılmamalı.

**Kaynak uyarısı:** Depoda Fusûs, Fütûhât, Kâşânî, Cürcânî, Kayserî veya Konevî metni yok (`veri/` yalnızca
envanter içeriyor). Aşağıdaki **bütün kaynak karşılaştırmaları bellektendir**; hiçbiri baskıdan sayfa
kontrolüyle doğrulanmadı. Her bulguda güven derecesi verildi; `guven: dusuk/orta` olanlar baskıdan teyit
edilmeden kesin sayılmamalı.

Sınıflar: **ANLAM** = ıstılahın anlamı yanlış ya da Ekberî görüşe aykırı; **ETİKET** = altın cevap/ilgili/zor_negatif
yanlış; **DİL** = Arapça dil/rivayet hatası, anlamı bozmayan; **ÜSLUP** = tercih meselesi, hata sayılmaz;
**SIZINTI** = sızıntı seviyesi notu eksik/yanlış.

## 1. Anlam hataları (öncelikli)

| Kayıt | Bulgu | Öneri | Güven |
|---|---|---|---|
| GT-B25 | "النبوة والرسالة منقطعتان" mutlak söylenmiş. Fusûs Üzeyr fassında kesilen **teşrî nübüvveti ve risâlet**tir ("أعني نبوة التشريع"); İbnü'l-Arabî'ye göre âmm nübüvvet sürer. Belge, şeyhin açıkça reddettiği bir hükmü onun ağzından söylüyor. | "والنبوة والرسالة - أعني نبوة التشريع ورسالته - منقطعتان" | yüksek (bellekten) |
| GT-Q31 | Terimsiz tarif "رجل من أولياء آخر الزمان" diyor. İbnü'l-Arabî'de **âhir zamanda gelen** hatm, umûmî velâyetin hatmi olan Hz. Îsâ'dır; **Muhammedî velâyetin hatmi** ise "zamanımızda mevcut" Arap bir kişidir (Fütûhât). Mehdî de ayrı bir şahsiyettir. Sorgu iki hatmi (ve Mehdî tasavvurunu) karıştırıyor; anlamdan giden bir model B24'ü değil "âhir zaman" kümesini arar. | "رجل من أولياء هذه الأمة يُختم به ميراث المقام المحمدي، فلا يكون بعده من هو على قلب محمد في تمامه، وهو أعرف أهل زمانه بربه" | yüksek (bellekten) |
| GT-B24 | (a) "أعلم الخلق بالله في زمانه": Fütûhât'taki ifade hatmin kendi zamanında **ve sonrasında** ondan daha âlim olmayacağıdır; "في زمانه" kaydı anlamı daraltıyor. (b) İki hatm ayrımı yalnız "يُختم نوع منها" ile ima ediliyor; ölçüm açısından yeterli, ama kavram açısından Îsâ'nın umûmî hatm olduğu belgede yok. | "هو أعلم الخلق بالله، لا يكون في زمانه ولا بعده أعلم منه بالله ... وأما ختم الولاية العامة فعيسى عليه السلام" (ikinci cümle isteğe bağlı; eklenirse Q12/Q31 dengesine bakılmalı) | (a) orta, (b) yüksek (bellekten) |
| GT-B19 | Tarif ("رجوع العبد إلى شهود الخلق بعد الفناء ... فلا يحجبه أحدهما عن الآخر") Kâşânî'de **fark-ı sânî / zü'l-ayneyn** tarifidir; bekânın kendisi daha dar ("رؤية العبد قيام الله على كل شيء"). Bekâ ile fark-ı sânî bitişik makamlar olduğu için ağır hata değil, ıstılah kayması. Q24 bu belgeye bağlı olduğundan sorgu–belge tutarlı kalıyor. | Ya terim alanı "البقاء (الفرق الثاني)" yapılsın ya tarif "البقاء أن يرى العبد قيام الحق بكل شيء بعد فنائه ..." ile değiştirilsin. | orta (bellekten) |

## 2. Altın etiket sorunları (sorgu bazında)

Ölçüm betiği `tuzak`ı "en iyi zor_negatif en iyi doğrudan yukarıda mı" diye hesaplıyor ve zor_negatif'e nDCG'de 0 derece
veriyor. Bu yüzden kavramca iç içe bir belgeyi zor_negatif saymak, doğru kavramsal komşuluğu yakalayan modeli
cezalandırır. Set bu konuda kendi içinde tutarsız: Q12'de "aynı alan, farklı ıstılah → ilgili, tuzak değil" deniyor,
benzer durumlar başka sorgularda tuzak yapılmış.

**Altın cevabı (doğru/ilgili/zor_negatif) yanlış ya da savunulamaz olan sorgular:**

| Sorgu | Sorun | Öneri | Güven |
|---|---|---|---|
| GT-Q31 | Sorgu metni anlam hatalı (yukarıda). Mevcut lafızla B24 "doğru" savunulamaz; sorgu düzeltilince B24 doğru kalır. | Sorguyu düzelt. | yüksek |
| GT-Q16 | B04 (ehadiyye) zor_negatif. **Ekole bağlı:** Konevî–Fergânî çizgisinde taayyün-i evvel ehadiyye ile vâhidiyyeyi cem eden berzahtır (B43 bunu izliyor); Kayserî/Kâşânî'de ise ehadiyye mertebesi taayyün-i evvel ile örtüşür, vâhidiyye taayyün-i sânî sayılır. Kayserî çizgisini kodlayan bir model B04'ü üste koyunca "tuzak" yemiş sayılıyor. | B04 → ilgili. Gerekçeye "ekol farkı: Konevî vs Kayserî" notu. | orta (bellekten) |
| GT-Q06, GT-Q17 | B08 ↔ B07 karşılıklı zor_negatif. Ekberî öğretide insan-ı kâmilin hakikati hakikat-i Muhammediyyedir; ikisi aynı kavramın iki mertebesi, "farklı ıstılah, karışma riski" değil. | Q06'da B08, Q17'de B07 → ilgili. | yüksek |
| GT-Q29 | B13 (hayal) "saf lafız tuzağı" denmiş. Oysa Fusûs Yûsuf fassında âlemin **gölge** oluşu ile **hayal** oluşu aynı bahiste, aynı iddia olarak işlenir; B13'ün "ne mevcut ne madum" hükmü de sorgunun "kendi başına kaimiyeti yok" hükmüne kavramca yakın. Ayrıca "خيال = gölge" sözlük iddiası kısmen doğru (Lisân'da خيال الشيء ~ şeyin hayaleti/gölgesi; "خيال الظل" gölge oyunu) ama "saf lafız" nitelemesi yanlış. | B13 → ilgili; gerekçe düzeltilsin. | orta (bellekten) |
| GT-Q34 | B33 (tenzih/teşbih) zor_negatif. Nûh fassında hayret, tenzih ile teşbihin cem'inden doğar; kavramca bağımlı. Q12 ölçütüne göre ilgili olmalı. | B33 → ilgili, ya da tuzak kalacaksa gerekçede "kasıtlı sert komşu" diye açıkça belirtilsin. | orta |
| GT-Q13, GT-Q14 | Hebâ ↔ amâ karşılıklı zor_negatif. Fütûhât kozmolojisinde ikisi hiyerarşik komşu (amâ küllî "ilk zarf"/nefes, hebâ cisimler âleminin heyûlâsı); minimal çift değil. Ağır hata değil. | Tercihen nötr bırak (hiçbir listede yok) ya da ilgili; zor_negatif kalacaksa gerekçede "hiyerarşik komşu" diye yazılsın. | düşük–orta |
| GT-Q19 | Gerekçe "Y08 'العلم تابع للمعلوم' içerdiği için ilgili" diyor; **Y08 bu ifadeyi içermiyor** (o ifade Q42 sorgusunda ve B14'te var). Y08'in ilgili sayılması ancak "şer kâbile nispet edilir" bağıyla savunulabilir. | Gerekçeyi düzelt ("hüküm kâbile döner" bağı) ya da Y08'i ilgiliden çıkar. | yüksek (dosya içi kontrol) |
| GT-Q01 | B14 (sırr-ı kader) zor_negatif, B15 ilgili; ikisi de a'yân-ı sâbiteye aynı derecede bağlı. Hafif tutarsızlık. | B14 → ilgili ya da gerekçe ayrımı açıklasın. | düşük |

Doğrudan "doğru" belgesi yanlış atanmış sorgu **yok**; sorunlar ilgili/zor_negatif derecelerinde ve Q31'in sorgu metninde.

## 3. Ekol kümesi (B04, B05, B08, B27, B43): kavram ağı modeli açısından

Bu beş belge, anlamın tanıklığa (ekol) bağlı olduğu tipik kümedir; tek bir "doğru tanım" yok:
- B43 taayyün-i evvel = ehadiyye/vâhidiyye berzahı: Konevî, Fergânî (guven orta).
- B08 "حقيقة الحقائق" = hakikat-i Muhammediyye: Kayserî bu adı ehadiyye mertebesine de verir; B27 amâyı da
  "bazılarına göre" ehadiyye sayar (Kâşânî'nin Istılâhât'ta amâyı kendi görüşü olarak ehadiyye, "denildi ki" ile vâhidiyye
  sayması, bellekten, guven orta). Yani B04/B08/B27/B43 arasında adlandırmalar ekole göre kayar.
- B08 ayrıca hakikat-i Muhammediyyeyi "akl-ı evvel / kalem-i a'lâ" ile de özdeşleştiriyor; Konevî çizgisinde akl-ı evvel
  hakikatin değil **rûh-ı Muhammedî**nin mertebesidir. "باعتبارات مختلفة" kaydı hatayı yumuşatıyor ama tabaka karışık.
  Öneri: "وروحه هو العقل الأول والقلم الأعلى". Guven orta.

Öneri: bu kümedeki sorgularda (Q04, Q05, Q16, Q17, Q14) zor_negatif yerine ilgili kullanılsın; ölçüm raporunda bu
sorgular "ekole duyarlı" diye ayrı kırılımda gösterilsin.

## 4. Dil hataları (anlamı bozmayan)

| Kayıt | Bulgu | Öneri | Güven |
|---|---|---|---|
| GT-B27 | Hadis sırası: Tirmizî/İbn Mâce rivayetinde "ما تحته هواء وما فوقه هواء"; belgede ters ("ما فوقه ... وما تحته"). | Rivayet sırasına çevir. | orta (bellekten) |
| GT-B14 | "فما حكم على أحد إلا هو بنفسه" zamir belirsiz (hüküm vereni mi hüküm verileni mi gösteriyor). | "فما حكم على أحد إلا عينُه" ya da "فلا يحكم عليه إلا ما هو عليه". | yüksek |
| GT-Q41 | "أي ليس مثل مثله شيء، **فالكاف** زائدة عند قوم": verilen "أي" açıklaması kâfın asliyye okumasıdır; ardından gelen "ف" sebep bildiremez. | "...أي ليس مثلَ مثلِه شيء على أن الكاف أصلية، وهي زائدة عند قوم..." ya da "ف" → "و". | yüksek |
| GT-B04 | "اعتبار الذات **من حيث هي** مع إسقاط جميع النسب": "min haysü hiye" teknik olarak lâ bi-şart (mutlak zât), "isnadların iskâtı" bi-şart-ı lâ'dır; iki itibar yan yana. Kâşânî'nin tarifi yalnız "مع إسقاط الجميع". | "من حيث هي" çıkarılsın. | orta |

## 5. Üslup ve küçük içerik notları (hata sayılmaz)

- GT-Q27: "الشوق إلى أن يُدرك جماله" kenz hadisinin "أن أُعرف" (bilinme) vurgusunu cemâle kaydırıyor; "المحبة لأن يُعرف" daha sadık
  ama B28 ile lafız ortaklığını artırır. Tercih meselesi.
- GT-Q34: "اضطراب" hayrete olumsuz bir ton katıyor; "تردد" daha yakın (ama B34'te geçtiği için kaçınılmış olabilir). Üslup.
- GT-Q15 sorgu_tr: "İtikad edilen ilah" → "İtikatlardaki ilah (ilâhu'l-mu'tekadât)" daha yerleşik. GT-Q12: "Velâyetin hatmi" →
  "Hatm-i velâyet". GT-Q08: "Âlem-i misâl" yerleşik karşılık. Üslup.
- GT-Y11: "Hakk'ı eşyada gören bakiyye-i hicâbdadır" hükmü kurgu; Ekberî çizgide kâmil "zü'l-ayneyn" iki görüşü cem eder
  (B19 ile gerilim). Yapısal belge olduğu için kabul edilebilir; kavram ağına kaynak yapılmamalı.
- GT-Q43: Herevî'nin Menâzil sırasında tevbeden önce "yakaza" gelir; "أول مراتب السلوك التوبة" küçük içerik sapması. Yapısal sorgu, etkisiz.
- GT-T03: "صفات المعاني سبع عند المتكلمين" → "عند الأشاعرة" (Mâtürîdîler tekvînle sekiz sayar). Dış alan belgesi, etkisiz.
- GT-B12: rüyayı misal âlemine bağlamak yaygın, ama Kayserî'de rüya çoğunlukla muttasıl hayale (mukayyed misal) aittir; B13 ile sınır bulanık. Etkisiz.
- GT-T02: "الواحد ليس بعدد بل هو مبدأ العدد" İbnü'l-Arabî'nin de görüşü; Q38'de zor_negatif olarak tabaka tanımına ("aynı konu, farklı yapı") uygun, sorun yok.

## 6. Sızıntı notları

| Kayıt | Bulgu | Öneri |
|---|---|---|
| GT-Q44 | Velî'nin iki etimolojisi Kuşeyrî Risâle'deki tarife neredeyse lafzen yakın; "orta" doğru, not Kuşeyrî'yi anmalı. | Not ekle. |
| GT-Q46 | Keşf-i sûrî / ma'nevî ayrımı Kayserî Mukaddime (keşf faslı) yankısı; "yuksek" verilmiş ama notta Fusûs/Fütûhât/Konevî deniyor. Kayserî şerhi test eseri olursa önemli. | Notu Kayserî olarak düzelt. |
| GT-B45 | Renkli cam temsili Fusûs'ta da geçer (fass yerini bellekten kesinleştiremedim); "orta" yerine "yuksek" olabilir. | Baskıdan kontrol; guven düşük. |
| GT-Q38 | "الواحد يتكرر في مراتب العدد" Fusûs'taki (Hârûn/İlyâs bölgesi?, bellekten emin değilim) sayı–vahdet temsiline yakın; "dusuk" iyimser. | "orta" ve not; guven düşük. |
| GT-Q43 | Herevî Menâzil sırası yankısı; "orta" uygun, not Herevî'yi anmalı. | Not ekle. |
| GT-B22, B30, B09 | Cürcânî Ta'rîfât'a neredeyse lafzen yakın; seviye "orta" doğru. | — |

## 7. Kayıt bazında gözden geçirme listesi (kabul ölçütü: her kayıt en az bir kez)

Belgeler (69). "Temiz" = Arapça ve ıstılah doğru, bulgu yok.

- B01 temiz (Kâşânî çizgisi). B02 temiz. B03 temiz ("وجودي" Kâşânî'deki "أسمائي" yerine; kabul edilebilir). B04 DİL (§4).
  B05 temiz. B06 temiz (Kayserî'nin beş hazret tasnifiyle uyumlu). B07 temiz. B08 ANLAM-düşük (§3). B09 temiz (Cürcânî + "tecellîde tekrar yok").
  B10 temiz. B11 temiz (harekeli "نفَس" doğru kullanılmış). B12 temiz (§5 not). B13 temiz (Fütûhât hayal formülü).
  B14 DİL (§4). B15 temiz. B16 temiz. B17 temiz. B18 temiz. B19 ANLAM-kayma (§1). B20 temiz (nevâfilde kul fâil, Hak âlet: Kâşânî/Kayserî formülü).
  B21 temiz. B22 temiz. B23 temiz. **B24 ANLAM (§1).** **B25 ANLAM (§1).** B26 temiz (hebâ/heyûlâ/ankâ eşleşmeleri doğru).
  **B27** DİL (§4) + ekol notu (§3); "عند الشيخ هو النفس الرحماني" bellekten doğru görünüyor (guven orta). B28 temiz.
  B29 temiz. B30 temiz. B31 temiz. B32 temiz. B33 temiz. B34 temiz. B35 temiz (Tüsterî sözü). B36 temiz. B37 temiz.
  B38 temiz. B39 temiz. B40 temiz. B41 temiz. B42 temiz. **B43** temiz, ekole bağlı (§3). B44 temiz. B45 temiz (§6).
  B46 temiz. B47 temiz. B48 temiz.
- Y01 temiz. Y02 temiz. Y03 temiz. Y04 temiz. Y05 temiz. Y06 temiz. Y07 temiz (zamirin Allah'a dönmesi Ekberî okumayla uyumlu).
  Y08 temiz. Y09 temiz (kalem, levh, tabîat, hebâ, cism-i küll sırası Fütûhât'la uyumlu, bellekten). Y10 temiz.
  Y11 üslup/içerik notu (§5). Y12 temiz. Y13 temiz.
- T01 temiz (Cürcânî). T02 temiz. T03 küçük not (§5). T04–T08 temiz.

Sorgular (50).

- Doğrudan terim: Q01 ETİKET-düşük. Q02, Q03 temiz (iyi minimal çift). Q04 ekol notu (§3). Q05 temiz. Q06 ETİKET. Q07 temiz (nefes/nefs harekesiz tuzağı geçerli).
  Q08 temiz. Q09, Q10 temiz (yön çifti geçerli). Q11 temiz. Q12 temiz (§5 üslup). Q13, Q14 ETİKET-düşük. Q15 temiz (§5 üslup).
  **Q16 ETİKET (ekol).** Q17 ETİKET.
- Terimsiz tarif: Q18 temiz (yasak lafız sızmıyor). **Q19 gerekçe hatası.** Q20 temiz. Q21 temiz. Q22 temiz (hadis yönü doğru: nevâfil).
  Q23, Q24 temiz. Q25 temiz. Q26 temiz. Q27 üslup. Q28 temiz. **Q29 ETİKET.** Q30 temiz. **Q31 ANLAM.** Q32 temiz ("عطف" eşanlamlısı yerinde).
  Q33 temiz. Q34 ETİKET + üslup.
- Yapısal benzerlik: Q35–Q40 temiz (yapı eşleşmeleri doğru; Q40'taki "halkı Hak ile gören kesreti vahdette görür" dağılımı kabul edilebilir).
  Q41 DİL. Q42 temiz. Q43 sızıntı/üslup notu. Q44 sızıntı notu. Q45 temiz. Q46 sızıntı notu. Q47–Q50 temiz.

## 8. Özet ve sonraki adım

- Anlam hatası: B25, Q31 (yüksek güven); B24, B19 (orta). Düzeltilmeden kullanılmamalı.
- Etiket: Q06, Q17, Q16, Q29, Q34, Q19 (gerekçe) zorunlu; Q01, Q13, Q14 isteğe bağlı.
- Dil: B27, B14, Q41, B04. Üslup ve sızıntı notları isteğe bağlı.
- Düzeltmeler Mümeyyiz'e (setin sahibi) sürüm 2 olarak işletilmeli; kimlikler korunmalı. Sorgu/belge metni değişen
  kayıtlarda Arapça yeniden Istılahçı onayından geçmeli.
- Bellekten yapılan kaynak karşılaştırmaları (özellikle B24 "في زمانه", B27 hadis sırası ve "nefes" özdeşliği, Kâşânî'nin
  amâ tarifi, B45/Q38 Fusûs yeri) baskı metinleri depoya girince teyit edilmeli.
