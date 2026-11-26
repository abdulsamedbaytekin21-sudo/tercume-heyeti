# Istılah kayıt protokolü (G-006, sürüm 1)

Sorumlu: Istılahçı. Tarih: 2026-11-26. Durum: geçici biçim; Mimar'ın şeması (G-002) gelince alan adları ona eşlenecek,
anlam ve kimlik kuralları değişmez.

## 1. Model

```
terim (lafız, kök)  1──n  anlam  1──n  tanıklık (eser, baskı, cilt, sayfa, yer, müellif, ekol, dönem)
                                   n──n  ilişki (türlendirilmiş kenar: anlam↔anlam, anlam↔ekol ...)
karşılık (Türkçe ifade) ──► tanıklık + hizalanmış çift kimliği
```

- **Terim** yalnızca lafızdır: Arapça yazım (harekeli ve harekesiz), kök(ler), dilbilgisel tür. Anlam taşımaz.
- **Anlam** bir terimin bir kullanımda taşıdığı kavramdır. Tanımı Türkçe yazılır. Anlam ekol veya dönem taşımaz.
- **Tanıklık** bir anlamın belirli bir eserde, belirli bir yerde kullanıldığının kaydıdır. **Ekol, dönem ve müellif
  yalnızca tanıklıkta durur.** "Bu anlam Ekberîdir" denmez; "bu anlamın Fusûs'ta (Ekberî, 7./13. yy) tanığı vardır" denir.
  Aynı anlamın başka ekolde tanığı bulunursa yeni anlam açılmaz, yeni tanıklık eklenir.
- **Karşılık** ("bu ıstılah burada şu Türkçe ifadeyle verilmiş") bir karardır ve ancak hizalanmış bir çiftten çıkar.
  Kaynak çift kimliği (`cift_id`) olmayan karşılık kaydı yazılmaz. Istılahçının kendi önerisi karşılık değildir;
  gerekirse anlamın `tanim` alanına girer.
- **İlişki** türlendirilmiş kenardır (`karsit`, `ust_kavram`, `ilgili`, `sarih_yorumu` ...). Yeni tür eklemek şemayı kırmaz.

## 2. Kimlik ve sürüm

| Kayıt | Biçim | Örnek |
|---|---|---|
| terim | `IST-T-nnnn` | `IST-T-0010` |
| anlam | `IST-A-nnnn-k` (terim no + anlam sırası) | `IST-A-0010-1` |
| tanıklık | `IST-N-nnnn-k-m` | `IST-N-0010-1-1` |
| karşılık | `IST-K-nnnnnn` | (henüz yok) |
| ilişki | `IST-I-nnnn` | `IST-I-0001` |

- Kimlik kalıcıdır; silinen kaydın kimliği yeniden kullanılmaz. Silme yerine `durum: geri_cekildi` ve gerekçe.
- Her kayıtta `surum` (tamsayı) ve `degisiklik` (tarih, yapan, kart) bulunur. İçerik değişince sürüm artar,
  önceki sürüm geçmiş dosyasında kalır.
- Anlam bölünür ya da birleşirse eski anlam geri çekilir, yenileri `ilgili` değil `yerine_gecen` ilişkisiyle bağlanır.

## 3. Alanlar (geçici)

Her satır bir JSON nesnesidir; `tur` alanı kayıt türünü söyler: `terim`, `anlam`, `taniklik`, `iliski`, `karsilik`.

- terim: `kimlik, surum, lafiz, lafiz_harekesiz, okunus, kok[], dil_turu, not`
- anlam: `kimlik, surum, terim, sira, tanim, guven, gerekce, inceleme`
- taniklik: `kimlik, surum, anlam, eser, eser_not, baski, cilt, sayfa, yer, alinti, muellif, muellif_vefat,
  ekol, donem, cift_id, guven, gerekce, inceleme`
- iliski: `kimlik, surum, tur_kenar, kaynak, hedef, guven, gerekce`
- karsilik: `kimlik, surum, anlam, taniklik, cift_id (zorunlu), turkce, turkce_eser, guven, gerekce`

`harekesiz` yazım `metin/normallestir.py` kurallarıyla üretilir (hareke ve tatvil kalkar, أ إ آ ٱ → ا, ى → ي, ة korunur).
Ekol ve dönem şimdilik kısa kimliktir (`ekol:ekberi`, `donem:h7`); Mimar'ın ekol/dönem tablolarına eşlenecek.

## 4. Güven

Üç düzey: `yuksek`, `orta`, `dusuk`. `dusuk` olan her kayıtta `gerekce` zorunludur ve `inceleme: insan` işaretlenir.

| Kayıt | yuksek | orta | dusuk |
|---|---|---|---|
| anlam | Metinde açıkça işlenen, şârihler arasında tartışmasız anlam | Anlam belirgin ama tanımı şârih sistematiğine dayanıyor | Anlam ayrımı tartışmalı, lafzın o metinde geçtiği teyitsiz ya da tanım tek yoruma dayanıyor |
| tanıklık | Baskı, cilt, sayfa ve alıntı baskıdan okunmuş | Baskı ve sayfa okunmuş, alıntı kısmi | Cilt/sayfa ya da baskı doğrulanmamış |
| karşılık | Çift onaylı, ıstılah tutarlı karşılanmış | Çift onaylı, karşılık bağlama göre esnek | Çift düşük hizalama puanlı ya da karşılık açıklama/şerh içine dağılmış |

Kurallar:
1. **Uydurma yok.** Cilt, sayfa, baskı ya da alıntı baskıdan okunmadıysa alan `"doğrulanmadı"` (alıntı için `null`) yazılır
   ve tanıklık `guven: dusuk` olur. Bellekten Arapça alıntı yazılmaz.
2. Anlamın güveni, tanıklıklarının en yükseğini geçemez demiyoruz; anlam güveni kavramsal yargıdır, tanıklık güveni
   kaynak yargısıdır. İkisi ayrı tutulur. Ancak tanıklığı olmayan anlam kaydedilmez.
3. Bir anlam ayrımından (aynı lafzın iki anlamı) emin değilsem her iki anlam da `dusuk` olur ve gerekçede ayrımın neden
   tartışmalı olduğu yazılır.
4. Şârihin sistematize ettiği ama ana metinde açıkça tanımlanmayan anlamlarda tanıklık mümkünse şerhe bağlanır
   (şârihin ekolü ve dönemiyle) ve ana metin tanıklığından ayrı tutulur.

## 5. Kaynak sıralaması

1. Hizalanmış çift (Arapça birim + Türkçe birim, `cift_id`). Karşılık kararı yalnız buradan.
2. Arapça ana metin, Türkçe çevirinin dayandığı baskıdan (proje/kararlar.md). OpenITI tanıklık kaynağı değildir.
3. Şerh (Konuk, E-001; ileride Kâşânî, Kayserî vb.) — ayrı tanıklık, şârihin ekol/dönemiyle.
4. Istılah sözlükleri (Kâşânî, Istılâhâtü's-sûfiyye; Hakîm, el-Mu'cemü's-sûfî) — tanım desteği; tanıklık yerine geçmez.

Telifli çevirilerden (Demirli, E-002) alınan Türkçe alıntılar ve onlardan çıkan karşılık kayıtları `veri/kasa/` altında
tutulur; ortak `veri/kavram/` dosyasında yalnızca kimlik ve `cift_id` görünür, metin görünmez.

## 6. İş akışı

1. Mukabeleci terim adaylarını çiftlerden çıkarır (betik; Kâtip'e verilebilir).
2. Istılahçı adayları mevcut terimlere bağlar, yeni anlam açılıp açılmayacağına karar verir, karşılık kaydı yazar.
3. `dusuk` kayıtlar insan inceleme kuyruğuna; kavram ağına giden her toplu teslim Mümeyyiz denetiminden geçer.

## 7. Bu sürümün sınırları (ornek_30.jsonl)

- Henüz hizalanmış çift yok (G-003 beklemede), bu yüzden **karşılık kaydı yoktur**; `cift_id` her yerde `null`.
- Dayanılan Arapça baskı belirlenmedi (G-001: "doğrulanmadı"). Tüm tanıklıklarda baskı, cilt, sayfa `"doğrulanmadı"`,
  alıntı `null`, `guven: dusuk`. `yer` alanı yalnızca fass adını verir; fass ataması bilgiye dayanır, baskıdan okunmamıştır.
- Fass başlıklarındaki hikmet sıfatları için nüsha farkı olabilir (ör. Şîs fassı: nefsiyye / nefsiyye-nefesiyye / nefsiyye-nefthiyye okuması).
- Müellif vefat tarihleri G-001 envanteriyle aynı biçimde "doğrulanmadı" notludur.
- "Vahdet-i vücûd" bilerek listeye alınmadı: lafız Fusûs'ta ıstılah olarak geçmez; sonraki dönem tanıklığı (Konevî sonrası)
  olmadan kayıt açılmaz.
- `lafiz` alanı bu sürümde harekesiz yazıldı; harekeli yazım baskıdan alınacak (bellekten hareke yazılmaz).
- Üretim: 37 anlam, 40 tanıklık, 10 ilişki. Anlam güveni: 19 yüksek, 12 orta, 6 düşük; bütün tanıklıklar düşük.
