#!/usr/bin/env python3
"""G-005 — Gömme modeli ölçüm betiği.

degerlendirme/gomme_testi.jsonl içindeki belge havuzu (tur=belge) üzerinde sorguları
(tur=sorgu) çalıştırır; tabaka, dil ve sızıntı seviyesine göre ayrı ayrı raporlar.

Kodlayıcılar
  sahte          : karakter 3-gram özet vektörü. İndirme yok, bağımlılık yok. Hattı sınamak için.
  lafiz          : normalleştirilmiş kelime BM25. Temel çalıştırma (projede birincil erişim lafızdır);
                   her gömme modeli buna göre fark (delta) ile raporlanır.
  st:<model>     : sentence-transformers modeli, ör. st:BAAI/bge-m3, st:sentence-transformers/LaBSE,
                   st:intfloat/multilingual-e5-large (e5 için --sorgu-oneki "query: " --belge-oneki "passage: ").

Ölçütler (sorgu başına, sonra ortalama)
  R@1, R@5, R@10 : ilk k içinde en az bir 'dogru' belge var mı
  MRR            : ilk 'dogru' belgenin ters sırası
  nDCG@10        : derece dogru=2, ilgili=1
  tuzak          : en iyi 'zor_negatif' en iyi 'dogru' belgeden yukarıda mı (oran; düşük iyidir)
  MRR için tohumlu bootstrap %95 güven aralığı verilir (50 sorgu küçüktür; farkları buna göre okuyun).

Kullanım
  python3 degerlendirme/gomme_olc.py --kontrol                 # yalnız veri doğrulama
  python3 degerlendirme/gomme_olc.py --oz-test                 # sahte veriyle betiğin kendi sınaması
  python3 degerlendirme/gomme_olc.py --model sahte --model lafiz
  python3 degerlendirme/gomme_olc.py --model lafiz --model st:BAAI/bge-m3 --dil ar --dil tr --cikti sonuc.json
  python3 degerlendirme/gomme_olc.py --hafiza veri/hafiza.jsonl   # sızıntı denetimi (8-gram örtüşme)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

VARSAYILAN_VERI = Path(__file__).resolve().parent / "gomme_testi.jsonl"
TABAKALAR = ("dogrudan_terim", "terimsiz_tarif", "yapisal_benzerlik")
SEVIYELER = ("dusuk", "orta", "yuksek")

# ------------------------------------------------------------------ Arapça normalleştirme
_HAREKE = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_ELIF = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"})
_NOKTALAMA = re.compile(r"[^\w\s]", re.UNICODE)


def normallestir(metin: str) -> str:
    """Harekesiz, elif/yâ/tâ-merbûta birleştirilmiş, noktalamasız, küçük harf."""
    m = unicodedata.normalize("NFKC", metin)
    m = _HAREKE.sub("", m).translate(_ELIF)
    m = _NOKTALAMA.sub(" ", m).lower()
    return re.sub(r"\s+", " ", m).strip()


def kelimeler(metin: str) -> list[str]:
    return normallestir(metin).split()


def _ek_soy(k: str) -> str:
    """Kaba önek ayıklama (ال، و، ف، ب، ل، ك). Lafız temeli ve yasak lafız denetimi için yeter."""
    for on in ("وال", "فال", "بال", "كال", "لل", "ال"):
        if k.startswith(on) and len(k) - len(on) >= 2:
            return k[len(on):]
    if k[:1] in "وفبلك" and len(k) >= 4:
        return k[1:]
    return k


# ------------------------------------------------------------------ veri
class VeriHatasi(Exception):
    pass


def yukle(yol: Path):
    meta, belgeler, sorgular = None, [], []
    with open(yol, encoding="utf-8") as f:
        for no, satir in enumerate(f, 1):
            satir = satir.strip()
            if not satir:
                continue
            try:
                r = json.loads(satir)
            except json.JSONDecodeError as e:
                raise VeriHatasi(f"{yol}:{no}: JSON hatası: {e}") from e
            tur = r.get("tur")
            if tur == "meta":
                meta = r
            elif tur == "belge":
                belgeler.append(r)
            elif tur == "sorgu":
                sorgular.append(r)
            else:
                raise VeriHatasi(f"{yol}:{no}: bilinmeyen tur {tur!r}")
    return meta, belgeler, sorgular


def dogrula(belgeler, sorgular, beklenen_sorgu: int | None = 50) -> list[str]:
    """Kabul ölçütünü mekanik olarak denetler. Hata listesi döner (boşsa geçerli)."""
    h: list[str] = []
    kimlikler = Counter(r["id"] for r in belgeler + sorgular)
    h += [f"yinelenen kimlik: {k}" for k, n in kimlikler.items() if n > 1]
    bids = {b["id"] for b in belgeler}
    for b in belgeler:
        for alan in ("id", "surum", "metin"):
            if not b.get(alan) and b.get(alan) != 0:
                h.append(f"{b.get('id')}: '{alan}' eksik")
    for s in sorgular:
        sid = s.get("id", "?")
        for alan in ("surum", "sorgu", "tabaka", "dogru", "gerekce", "sizinti"):
            if not s.get(alan):
                h.append(f"{sid}: '{alan}' eksik")
        if s.get("tabaka") not in TABAKALAR:
            h.append(f"{sid}: geçersiz tabaka {s.get('tabaka')!r}")
        if (s.get("sizinti") or {}).get("seviye") not in SEVIYELER:
            h.append(f"{sid}: sizinti.seviye geçersiz")
        if not (s.get("sizinti") or {}).get("not"):
            h.append(f"{sid}: sizinti.not eksik")
        dog = set(s.get("dogru", []))
        for alan in ("dogru", "ilgili", "zor_negatif"):
            for x in s.get(alan, []):
                if x not in bids:
                    h.append(f"{sid}: {alan} içindeki {x} belge havuzunda yok")
        for alan in ("ilgili", "zor_negatif"):
            kes = dog & set(s.get(alan, []))
            if kes:
                h.append(f"{sid}: {sorted(kes)} hem dogru hem {alan}")
        if set(s.get("ilgili", [])) & set(s.get("zor_negatif", [])):
            h.append(f"{sid}: ilgili ve zor_negatif kesişiyor")
        if s.get("tabaka") == "terimsiz_tarif":
            yasak = s.get("yasak_lafiz") or []
            if not yasak:
                h.append(f"{sid}: terimsiz_tarif için yasak_lafiz tanımlı değil")
            sk = {_ek_soy(k) for k in kelimeler(s.get("sorgu", ""))}
            for y in yasak:
                yn = _ek_soy(normallestir(y))
                if yn in sk:
                    h.append(f"{sid}: terimsiz sorguda yasak lafız geçiyor: {y}")
    if beklenen_sorgu is not None and len(sorgular) != beklenen_sorgu:
        h.append(f"sorgu sayısı {len(sorgular)} (beklenen {beklenen_sorgu})")
    say = Counter(s.get("tabaka") for s in sorgular)
    for t in TABAKALAR:
        if say[t] < 10 and beklenen_sorgu:
            h.append(f"tabaka {t} yalnız {say[t]} sorgu (en az 10 beklenir)")
    return h


# ------------------------------------------------------------------ kodlayıcılar
def _norm_vek(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


class SahteKodlayici:
    """Karakter 3-gram karma vektörü (boyut 512). Deterministik; anlam bilmez."""

    ad = "sahte"

    def __init__(self, boyut: int = 512):
        self.boyut = boyut

    def kodla(self, metinler, tur):
        cikti = []
        for m in metinler:
            v = [0.0] * self.boyut
            t = " " + normallestir(m) + " "
            for i in range(len(t) - 2):
                g = t[i:i + 3]
                k = int(hashlib.md5(g.encode("utf-8")).hexdigest()[:8], 16)
                v[k % self.boyut] += 1.0
            cikti.append(_norm_vek(v))
        return cikti


class LafizBM25:
    """Kelime düzeyinde BM25; gömme değil, karşılaştırma temeli."""

    ad = "lafiz"

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b

    def hazirla(self, belge_metinleri):
        self.belgeler = [[_ek_soy(k) for k in kelimeler(m)] for m in belge_metinleri]
        self.ort = sum(map(len, self.belgeler)) / max(1, len(self.belgeler))
        df = Counter(k for d in self.belgeler for k in set(d))
        n = len(self.belgeler)
        self.idf = {k: math.log(1 + (n - v + 0.5) / (v + 0.5)) for k, v in df.items()}
        self.tf = [Counter(d) for d in self.belgeler]

    def skorla(self, sorgu):
        q = [_ek_soy(k) for k in kelimeler(sorgu)]
        skor = []
        for tf, d in zip(self.tf, self.belgeler):
            s = 0.0
            for k in q:
                if k in tf:
                    f = tf[k]
                    s += self.idf[k] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.ort))
            skor.append(s)
        return skor


class STKodlayici:
    """sentence-transformers sarmalayıcı; yalnız kullanılırsa içe aktarılır."""

    def __init__(self, model_adi, sorgu_oneki="", belge_oneki="", toplu=16):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:  # pragma: no cover
            raise SystemExit("sentence-transformers kurulu değil: pip install sentence-transformers") from e
        self.ad = "st:" + model_adi
        self.model = SentenceTransformer(model_adi)
        self.on = {"sorgu": sorgu_oneki, "belge": belge_oneki}
        self.toplu = toplu

    def kodla(self, metinler, tur):
        v = self.model.encode([self.on[tur] + m for m in metinler], batch_size=self.toplu,
                              normalize_embeddings=True, show_progress_bar=False)
        return [list(map(float, x)) for x in v]


def kodlayici_kur(ad, args):
    if ad == "sahte":
        return SahteKodlayici()
    if ad == "lafiz":
        return LafizBM25()
    if ad.startswith("st:"):
        return STKodlayici(ad[3:], args.sorgu_oneki, args.belge_oneki, args.toplu)
    raise SystemExit(f"bilinmeyen model: {ad}")


def _carp(a, b):
    return sum(x * y for x, y in zip(a, b))


def sirala(kodlayici, belgeler, sorgu_metinleri):
    """Her sorgu için belge kimliklerinin skora göre sıralı listesini döner."""
    bids = [b["id"] for b in belgeler]
    metin = [b["metin"] for b in belgeler]
    if isinstance(kodlayici, LafizBM25):
        kodlayici.hazirla(metin)
        skorlar = [kodlayici.skorla(q) for q in sorgu_metinleri]
    else:
        bv = kodlayici.kodla(metin, "belge")
        qv = kodlayici.kodla(sorgu_metinleri, "sorgu")
        try:
            import numpy as np
            skorlar = (np.asarray(qv) @ np.asarray(bv).T).tolist()
        except ImportError:
            skorlar = [[_carp(q, d) for d in bv] for q in qv]
    # Eşitlikte (ör. hiç ortak kelime yok) kimlik sırası altın belgeleri kayırmasın diye
    # sorgu+kimlik özetine göre sabit ama yansız sıra: tekrarlanabilir, şans düzeyinde.
    def kirici(q, b):
        return hashlib.md5((q + "|" + b).encode("utf-8")).hexdigest()

    return [[bids[i] for i in sorted(range(len(bids)), key=lambda i: (-round(s[i], 9), kirici(q, bids[i])))]
            for q, s in zip(sorgu_metinleri, skorlar)]


# ------------------------------------------------------------------ ölçütler
def sorgu_olc(sira, dogru, ilgili, zor):
    dogru, ilgili, zor = set(dogru), set(ilgili), set(zor)
    konum = {b: i for i, b in enumerate(sira)}
    ilk = min((konum[d] for d in dogru if d in konum), default=None)
    sonuc = {f"R@{k}": float(ilk is not None and ilk < k) for k in (1, 5, 10)}
    sonuc["MRR"] = 0.0 if ilk is None else 1.0 / (ilk + 1)
    derece = {**{b: 1 for b in ilgili}, **{b: 2 for b in dogru}}
    dcg = sum((2 ** derece.get(b, 0) - 1) / math.log2(i + 2) for i, b in enumerate(sira[:10]))
    ideal = sorted(derece.values(), reverse=True)[:10]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal)) or 1.0
    sonuc["nDCG@10"] = dcg / idcg
    if zor:
        en_iyi_zor = min(konum[z] for z in zor if z in konum)
        sonuc["tuzak"] = float(ilk is None or en_iyi_zor < ilk)
    return sonuc


OLCUTLER = ("R@1", "R@5", "R@10", "MRR", "nDCG@10", "tuzak")


def ortala(satirlar):
    out = {}
    for o in OLCUTLER:
        v = [s[o] for s in satirlar if o in s]
        if v:
            out[o] = sum(v) / len(v)
    out["n"] = len(satirlar)
    return out


def bootstrap_gu(degerler, tekrar=2000, tohum=5):
    if not degerler:
        return (float("nan"), float("nan"))
    rnd = random.Random(tohum)
    n = len(degerler)
    ort = sorted(sum(rnd.choice(degerler) for _ in range(n)) / n for _ in range(tekrar))
    return (ort[int(0.025 * tekrar)], ort[int(0.975 * tekrar) - 1])


def degerlendir(kodlayici, belgeler, sorgular, dil="ar"):
    alan = "sorgu" if dil == "ar" else "sorgu_tr"
    secili = [s for s in sorgular if s.get(alan)]
    siralar = sirala(kodlayici, belgeler, [s[alan] for s in secili])
    satirlar = []
    for s, sira in zip(secili, siralar):
        m = sorgu_olc(sira, s["dogru"], s.get("ilgili", []), s.get("zor_negatif", []))
        m.update(id=s["id"], tabaka=s["tabaka"], seviye=s["sizinti"]["seviye"], ilk5=sira[:5])
        satirlar.append(m)
    rapor = {"model": kodlayici.ad, "dil": dil, "genel": ortala(satirlar),
             "MRR_gu95": bootstrap_gu([s["MRR"] for s in satirlar])}
    rapor["tabaka"] = {t: ortala([s for s in satirlar if s["tabaka"] == t]) for t in TABAKALAR
                       if any(s["tabaka"] == t for s in satirlar)}
    rapor["sizinti"] = {v: ortala([s for s in satirlar if s["seviye"] == v]) for v in SEVIYELER
                        if any(s["seviye"] == v for s in satirlar)}
    rapor["sorgular"] = satirlar
    return rapor


# ------------------------------------------------------------------ sızıntı denetimi
def ngramlar(metin, n=8):
    t = normallestir(metin).replace(" ", "")
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def hafiza_sizintisi(belgeler, sorgular, hafiza_yolu: Path, n=8, esik=0.3):
    """Test metinlerinin hafıza/örnek havuzu metinleriyle karakter n-gram örtüşmesi.
    Hafıza dosyası: .jsonl (her satırda 'metin' / 'arapca' / 'ar' alanı) ya da düz metin."""
    hafiza = set()
    with open(hafiza_yolu, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if not satir:
                continue
            metin = satir
            if hafiza_yolu.suffix == ".jsonl":
                r = json.loads(satir)
                metin = next((r[k] for k in ("metin", "arapca", "ar") if r.get(k)), "")
            hafiza |= ngramlar(metin, n)
    bulgular = []
    for r, alan in [(b, "metin") for b in belgeler] + [(s, "sorgu") for s in sorgular]:
        g = ngramlar(r[alan], n)
        if g:
            oran = len(g & hafiza) / len(g)
            if oran >= esik:
                bulgular.append((r["id"], round(oran, 3)))
    return bulgular


# ------------------------------------------------------------------ yazdırma
def tablo_yaz(raporlar, temel_ad="lafiz"):
    def satir(etiket, m, temel=None):
        p = [f"{etiket:<34}"]
        for o in OLCUTLER:
            if o in m:
                d = ""
                if temel and o in temel and o != "tuzak":
                    d = f"({m[o] - temel[o]:+.2f})"
                p.append(f"{o}={m[o]:.2f}{d}")
        p.append(f"n={m['n']}")
        return "  ".join(p)

    temeller = {r["dil"]: r for r in raporlar if r["model"] == temel_ad}
    for r in raporlar:
        t = temeller.get(r["dil"]) if r["model"] != temel_ad else None
        lo, hi = r["MRR_gu95"]
        print(f"\n== {r['model']}  [dil={r['dil']}]  MRR %95 GA: {lo:.2f}–{hi:.2f}"
              + (f"  (parantez: {temel_ad} temeline fark)" if t else ""))
        print(satir("genel", r["genel"], t and t["genel"]))
        for k, m in r["tabaka"].items():
            print(satir("  tabaka:" + k, m, t and t["tabaka"].get(k)))
        for k, m in r["sizinti"].items():
            print(satir("  sızıntı:" + k, m, t and t["sizinti"].get(k)))
    if any(r["sizinti"].get("yuksek") and r["sizinti"].get("dusuk") for r in raporlar):
        print("\nNot: sızıntı:yuksek ile sızıntı:dusuk arasındaki fark ezber göstergesidir, kanıt değildir;"
              " düşük seviyeli sorgular çoğunlukla yapısal tabakadadır, tabakayla birlikte okuyun.")


# ------------------------------------------------------------------ öz sınama
def oz_test():
    """İndirme yapmadan betiğin mantığını küçük sahte veriyle sınar."""
    # 1) ölçüt hesapları
    m = sorgu_olc(["a", "b", "c"], ["a"], [], ["b"])
    assert m["R@1"] == 1 and m["MRR"] == 1 and m["tuzak"] == 0 and abs(m["nDCG@10"] - 1) < 1e-9, m
    m = sorgu_olc(["b", "c", "a"], ["a"], ["c"], ["b"])
    assert m["R@1"] == 0 and m["R@5"] == 1 and abs(m["MRR"] - 1 / 3) < 1e-9 and m["tuzak"] == 1, m
    assert 0 < m["nDCG@10"] < 1
    m = sorgu_olc(["x", "y"], ["a"], [], [])
    assert m["MRR"] == 0 and m["R@10"] == 0 and "tuzak" not in m
    # 2) normalleştirme
    assert normallestir("الأَعْيَانُ الثَّابِتَة،") == "الاعيان الثابته"
    assert _ek_soy("والفناء") == "فناء"
    # 3) uçtan uca sahte veri
    belgeler = [
        {"id": "D1", "surum": 1, "metin": "الفناء سقوط رؤية العبد لفعله"},
        {"id": "D2", "surum": 1, "metin": "البقاء رجوع العبد إلى شهود الخلق"},
        {"id": "D3", "surum": 1, "metin": "العدد كمية منفصلة"},
    ]
    sorgular = [
        {"id": "S1", "surum": 1, "tabaka": "dogrudan_terim", "sorgu": "الفناء", "sorgu_tr": "fenâ",
         "dogru": ["D1"], "ilgili": [], "zor_negatif": ["D2"], "gerekce": "sınama",
         "sizinti": {"seviye": "dusuk", "not": "sahte"}},
        {"id": "S2", "surum": 1, "tabaka": "terimsiz_tarif", "sorgu": "رجوع العبد إلى الخلق",
         "dogru": ["D2"], "ilgili": [], "zor_negatif": ["D1"], "yasak_lafiz": ["البقاء"],
         "gerekce": "sınama", "sizinti": {"seviye": "yuksek", "not": "sahte"}},
        {"id": "S3", "surum": 1, "tabaka": "yapisal_benzerlik", "sorgu": "كمية منفصلة",
         "dogru": ["D3"], "ilgili": [], "zor_negatif": [], "gerekce": "sınama",
         "sizinti": {"seviye": "orta", "not": "sahte"}},
    ]
    assert dogrula(belgeler, sorgular, beklenen_sorgu=None) == []
    bozuk = [dict(sorgular[1], sorgu="البقاء رجوع")]
    assert any("yasak lafız" in h for h in dogrula(belgeler, bozuk, beklenen_sorgu=None))
    bozuk = [dict(sorgular[0], dogru=["YOK"])]
    assert any("havuzunda yok" in h for h in dogrula(belgeler, bozuk, beklenen_sorgu=None))
    for k in (SahteKodlayici(), LafizBM25()):
        r = degerlendir(k, belgeler, sorgular, "ar")
        assert r["genel"]["n"] == 3 and r["genel"]["MRR"] == 1.0, (k.ad, r["genel"])
        assert set(r["tabaka"]) == set(TABAKALAR)
        rt = degerlendir(k, belgeler, sorgular, "tr")
        assert rt["genel"]["n"] == 1
    lo, hi = bootstrap_gu([0.0, 1.0] * 10)
    assert 0 <= lo <= 0.5 <= hi <= 1
    # 4) sızıntı denetimi
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(json.dumps({"metin": "الفناء سقوط رؤية العبد لفعله ووصفه"}, ensure_ascii=False) + "\n")
    bul = hafiza_sizintisi(belgeler, sorgular, Path(f.name))
    Path(f.name).unlink()
    assert ("D1", 1.0) in bul and all(b[0] != "D3" for b in bul), bul
    print("öz-test: tamam")


# ------------------------------------------------------------------ ana
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--veri", type=Path, default=VARSAYILAN_VERI)
    ap.add_argument("--model", action="append", default=[], help="sahte | lafiz | st:<hf-model> (yinelenebilir)")
    ap.add_argument("--dil", action="append", choices=("ar", "tr"), default=[],
                    help="ar: Arapça sorgu; tr: Türkçe sorgu → Arapça belge (yalnız sorgu_tr olanlar)")
    ap.add_argument("--temel", default="lafiz", help="farkların hesaplanacağı temel model (varsayılan lafiz)")
    ap.add_argument("--sorgu-oneki", default="")
    ap.add_argument("--belge-oneki", default="")
    ap.add_argument("--toplu", type=int, default=16)
    ap.add_argument("--cikti", type=Path, help="tüm sonuçları JSON olarak yaz")
    ap.add_argument("--kontrol", action="store_true", help="yalnız veri doğrulaması")
    ap.add_argument("--oz-test", action="store_true", help="sahte veriyle öz sınama")
    ap.add_argument("--hafiza", type=Path, help="hafıza/örnek havuzu dosyası: sızıntı denetimi")
    ap.add_argument("--esik", type=float, default=0.3, help="sızıntı için 8-gram örtüşme eşiği")
    args = ap.parse_args(argv)

    if args.oz_test:
        oz_test()
        return 0

    _, belgeler, sorgular = yukle(args.veri)
    hatalar = dogrula(belgeler, sorgular)
    say = Counter(s["tabaka"] for s in sorgular)
    sev = Counter(s["sizinti"]["seviye"] for s in sorgular)
    print(f"veri: {len(belgeler)} belge, {len(sorgular)} sorgu; tabaka {dict(say)}; sızıntı {dict(sev)}")
    if hatalar:
        print("DOĞRULAMA HATALARI:\n  " + "\n  ".join(hatalar))
        return 1
    print("doğrulama: geçti")
    if args.kontrol:
        return 0

    sonuc = {}
    if args.hafiza:
        bul = hafiza_sizintisi(belgeler, sorgular, args.hafiza, esik=args.esik)
        sonuc["hafiza_sizintisi"] = bul
        if bul:
            print(f"SIZINTI: {len(bul)} kayıt hafızayla örtüşüyor (eşik {args.esik}): {bul}")
        else:
            print("sızıntı: hafızayla örtüşme yok")

    modeller = args.model or []
    if modeller and args.temel not in modeller:
        modeller = [args.temel] + modeller  # her zaman temel çalıştırmayla karşılaştır
    raporlar = []
    for ad in modeller:
        k = kodlayici_kur(ad, args)
        for dil in args.dil or ["ar"]:
            raporlar.append(degerlendir(k, belgeler, sorgular, dil))
    if raporlar:
        tablo_yaz(raporlar, args.temel)
    sonuc["raporlar"] = raporlar
    if args.cikti:
        args.cikti.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nyazıldı: {args.cikti}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
