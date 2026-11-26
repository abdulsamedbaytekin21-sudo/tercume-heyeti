# Metin hazırlama akışı (G-004)

Sorumlu: Musahhih. Kod: `metin/normallestir.py`, testler: `metin/test_normallestir.py`
(`cd metin && python3 -m unittest`).

## Katmanlar ve dizin düzeni

Her baskı için `veri/metin/<eser>/<baski>/` altında ayrı dosyalar:

| Dosya | İçerik | Değişir mi |
|---|---|---|
| `ham_ocr.txt` | OCR çıktısı, olduğu gibi | Hayır, asla |
| `tashihli.txt` | İşaretli, elle düzeltilmiş metin (özgün yazım, harekeli ise harekeli) | Yalnız tashih ile; sürüm artar |
| `normal.txt` | `tashihli.txt`'ten betikle üretilir | Elle düzenlenmez, yeniden üretilir |
| `tashih_raporu.md` | Örnekleme sonucu hata oranı | Her tashih turunda eklenir |

Her dosyanın ilk satırı HTML yorumu başlığıdır:
`<!-- kaynak: <eser>, <baskı: yayıncı/yer/yıl/cilt>; sayfalar: 1-40; katman: tashihli; sürüm: 1 -->`
(`#` ile başlayan satırlar başlık sayılır; bu yüzden başlık yorum biçimindedir, ayrıştırıcı atlar.)

## Akış

1. **OCR**: tarama -> `ham_ocr.txt`. Dokunulmaz.
2. **Tashih**: `ham_ocr.txt` kopyalanıp `tashihli.txt` olarak taranmış sayfaya karşı düzeltilir, aşağıdaki işaretler eklenir. Okunamayan yer `⟨?⟩`; tahmin yazılmaz.
3. **Örnekleme**: tashihli metinden rastgele satırlar (en az 50 satır ya da %5) ham ile karşılaştırılır; `sample_errors` ile `n, hatalı, oran` raporlanır.
4. **Normalleştirme**: `normallestir.py` gövdeyi (başlık/dipnot/ilave hariç) sadeleştirir: hareke, tatvil kaldırılır; أ إ آ ٱ -> ا; ى -> ي. `ة -> ه` varsayılan kapalıdır (bilgi kaybı). `⟨?⟩` ve sayfa numaraları korunur.
5. Normal metin ancak bundan sonra Mukabeleci'ye (hizalama) gider.

## İşaretleme kuralları

| Öğe | Biçim | Not |
|---|---|---|
| Sayfa | `[s. 23]` ayrı satırda | Sonraki satırlar bu sayfaya aittir |
| Başlık | `## fass: ...`, `## bâb: ...`, `## fasıl: ...`, `## mukaddime: ...`, `## başlık: ...` | `#` sayısı seviye (1-3) |
| Dipnot atfı | `[^1]` gövdede | Ayrıştırmada gövdeden silinir |
| Dipnot metni | `[^1]: ...` ayrı satırda, sayfa sonunda | Ana metne karışmaz |
| Mütercim/muhakkık ilavesi | `[...]` (köşeli parantez) | `[s. N]` ve `[^n]` hariç; ayrı katmana çıkar |
| Okunamayan | `⟨?⟩` | Tahmin yok |

Sınır: Baskının kendi köşeli parantezleri (muhakkık eklemeleri) de aynı biçimdedir; hangi baskıda ne anlama geldiği baskı notunda belirtilir. Kapsama alınmış ilave içinde iç içe `[ ]` desteklenmez.

## Örnek sayfa

Kaynak notu: Arapça kısım Fusûs el-Hikem'in başındaki besmele ve hamdele cümlesinden kısa bir parçadır (telifsiz, klasik metin). Hamdele parçası bellekten yazılmıştır ve **hiçbir baskıyla mukabele edilmemiştir**; gerçek baskı geldiğinde doğrulanacak. Türkçe satır, bu belgeyi göstermek için Musahhih'in yazdığı **örnek**tir, bir yayımlanmış çeviri değildir. Dipnot ve ilave örnek amaçlı uydurmadır; sayfa numaraları da öyle.

```
<!-- kaynak: ÖRNEK (Fusûs el-Hikem mukaddimesi parçası, baskı yok); sayfalar: 1-2; katman: tashihli; sürüm: 0 -->
[s. 1]
## mukaddime: Fusûs el-Hikem
بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ[^1]
الْحَمْدُ لِلَّهِ [ilave: örnek] ⟨?⟩ الْحِكَمِ
[^1]: (örnek dipnot) Besmele bazı nüshalarda yoktur.
[s. 2]
## fass: Örnek başlık
...
```

Türkçe örnek (ayrı dosyada tutulur, Arapçayla hizalama Mukabeleci'nindir): `Rahman ve Rahîm olan Allah'ın adıyla.`

Normalleştirme çıktısı (ilk satır): `بسم الله الرحمن الرحيم`; ikinci satırda `[ilave...]` ve `[^1]` çıkarılır, `⟨?⟩` yerinde kalır.

## Test sonucu

`python3 -m unittest` (metin/): 7 test, hepsi geçti (hareke/elif/yâ, ة seçeneği, ⟨?⟩ korunumu, katman ayrımı, sayfa işareti ilave sayılmaz, girdi değişmezliği, hata oranı).

## Açık / eskalasyon

- Baskı gelince: baskıya özgü köşeli parantez anlamı, fass başlık kalıpları ve hareke/ة politikası Istılahçı ve Mukabeleci ile teyit edilmeli.
- `ة -> ه` ve `ى -> ي` politikası hizalama doğruluğuna göre sonra ayarlanabilir.
