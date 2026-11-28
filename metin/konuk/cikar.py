#!/usr/bin/env python3
"""G-022 Musahhih: Konuk 1. cilt PDF'inden Arapça/Türkçe blokları çıkarır.

Bulgular (metin/konuk/CIKARIM.md):
  * Arapça (Scheherazade) harfler PDF'te görsel (soldan sağa) sırada gelir;
    mantıksal sıra için her satır parçası (run) harf harf tersine çevrilir.
  * Hemzeli elif (أ إ آ) iki glif olarak gelir: elif tabanı U+FFFD + hemze
    işaretli harf aynı x'te. Aynı x'teki U+FFFD atılır; yalnız duran U+FFFD
    elif (ا) sayılır.
  * Türkçe metin mantıksal sırada gelir.

Kullanım:
  cikar.py PDF CIKTI_DIZINI [--ilk N] [--son M]
Çıktı: CIKTI_DIZINI/ham.jsonl (akış sırası, olduğu gibi) ve temiz.jsonl.
Telifli çıktı yalnız veri/kasa/ altına yazılmalıdır (betik bunu zorlamaz, kullanan sorumludur).
"""
import argparse
import json
import re
import sys
import unicodedata

AR_FONTS = ("Scheherazade", "Suleymaniye", "TraditionalNaskh")   # TraditionalNaskh: 2. cilt dizinleri (s. 777-782, 858)
HAMZA_ALEF = "أإآٱ"
FFFD = "�"
TATWEEL = "ـ"
PERSIAN = set("پچژگکیھہۀ")
SUP_MAX = 8.0          # üst indis boyu (altı = dipnot çağrısı)
BODY_MIN = 10.4        # gövde Türkçe boyu (Garamond 11.5, Nimbus 10.6)
HEADER_TOP = 70
SEP_MIN_TOP = 400      # dipnot ayracı en az bu yükseklikte (2. cilt: dipnotu sayfanın çoğunu kaplayan sayfalarda ayraç s. 394'te top=117; --sep-min ile)
INDEKS = False         # dizin sayfaları: üst indis rakamlar dipnot çağrısı değil, sayfa göndermesidir
UST_INDIS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


# Scheherazade alt kümesinde أَ ve أُ tek glif (CID) olup metin katmanında yalnız U+0623 görünür.
# CID, pdfminer kancasıyla yazı tipi adına "#<cid>" olarak eklenir (hook_cid).
# Eşleme sayfa görüntüsünde doğrulandı: s. 84'te 1110 = أَ, 1111 = أُ, 913 = harekesiz أ.
CID_HAMZA = {1110: "\u064e", 1111: "\u064f"}
BILINEN_ALEF_CID = {913, 1110, 1111, 914, 912, 198}   # 198 = آ (Suleymaniye, 2. cilt s. 596'da görüntüyle doğrulandı)
BILINMEYEN = "⟨?⟩"   # metin katmanında karşılığı olmayan glif ((cid:N), İbrani harf yer tutucuları)
GORULEN_CID = {}


def hook_cid():
    """pdfminer'in LTChar'ına CID'yi fontname sonuna '#cid' olarak ekler (pdfplumber'dan önce çağrılmalı)."""
    from pdfminer import layout, pdffont
    if getattr(layout.LTChar, "_cid_hook", False):
        return
    son = {}
    orig = pdffont.PDFCIDFont.to_unichr

    def tu(self, cid):
        son["cid"] = cid
        return orig(self, cid)
    pdffont.PDFCIDFont.to_unichr = tu
    oi = layout.LTChar.__init__

    def ni(self, *a, **k):
        oi(self, *a, **k)
        self.fontname = "%s#%d" % (self.fontname, son.get("cid", -1))
    layout.LTChar.__init__ = ni
    layout.LTChar._cid_hook = True


def cid_of(c):
    fn = c["fontname"]
    return int(fn.rsplit("#", 1)[1]) if "#" in fn else None


def is_ar(c):
    return any(f in c["fontname"] for f in AR_FONTS)


def is_mark(t):
    return bool(t) and all(unicodedata.category(x) == "Mn" for x in t)


def split_runs(chars):
    """Akış sırasındaki harfleri Arapça/Türkçe ardışık parçalara ayırır.

    Arapçada ayrıca: satır (taban harf top'u) değişince, x geri sıçrayınca
    (>10pt) ya da ileri büyük boşlukta (>20pt, beyit hemistişleri) böler.
    Türkçede: satır değişince / x geri sıçrayınca.
    """
    runs, cur, mode, last, lastb = [], [], None, None, None
    for c in chars:
        m = "ar" if is_ar(c) else "tr"
        brk = False
        if cur and m != mode:
            brk = True
        elif cur and last is not None:
            if m == "ar":
                if is_mark(c["text"]):
                    pass
                else:
                    if abs(c["top"] - last["top"]) > 8 or c["x0"] < last["x0"] - 10 or c["x0"] - last["x1"] > 20:
                        brk = True
            else:
                small = c["size"] < SUP_MAX
                if c["x0"] < last["x0"] - 15 or (not small and lastb is not None and abs(c["bottom"] - lastb["bottom"]) > 5):
                    brk = True
        if brk:
            runs.append((mode, cur))
            cur = []
            lastb = None
        mode = m
        cur.append(c)
        if not (m == "ar" and is_mark(c["text"])):
            last = c
            if m == "tr" and c["size"] >= SUP_MAX:
                lastb = c
    if cur:
        runs.append((mode, cur))
    return runs


def _taban_ata(chars):
    """Hemzeli elif (أ إ آ) metin katmanında sıfır genişlikli hemze + ayrı elif tabanı (U+FFFD ya da ا,
    lam-elif ligatüründeki ا dahil) olarak gelir. Her hemzenin tabanını bulur: önce akışta sonraki,
    yoksa önceki harf; taban U+FFFD ya da ا olmalı ve hemze x'i tabanın genişliğine düşmeli."""
    atilacak = set()
    for i, c in enumerate(chars):
        if c["text"] not in HAMZA_ALEF:
            continue
        for j in (i + 1, i - 1):
            if 0 <= j < len(chars) and j not in atilacak and chars[j]["text"] in (FFFD, "ا"):
                b = chars[j]
                if b["x0"] - 1.0 <= c["x0"] <= b["x1"] + 0.3:
                    atilacak.add(j)
                    break
    return atilacak


def ar_logical(chars):
    """Akış sırasındaki Arapça harf listesinden mantıksal (temiz) metni üretir.

    Dönüş: (ham_akis_metni, temiz_metin)
    """
    ham = "".join(c["text"] for c in chars)
    out = []
    atilacak = _taban_ata(chars)
    for i, c in enumerate(chars):
        t = c["text"]
        if i in atilacak:
            t = ""
        elif t == FFFD:
            t = "ا"
        elif t.startswith("(cid:") or "\u05d0" <= t[:1] <= "\u05ea":
            t = BILINMEYEN
        elif t in HAMZA_ALEF:
            cid = cid_of(c)
            if cid is not None:
                GORULEN_CID[(t, cid)] = GORULEN_CID.get((t, cid), 0) + 1
                t += CID_HAMZA.get(cid, "")
        out.append(t)
    s = "".join(reversed(out))
    s = re.sub(r"\d+", lambda m: m.group()[::-1], s)   # rakam dizileri görsel sırada gelir; ters çevirme onları bozar
    s = re.sub("(?:" + re.escape(BILINMEYEN) + "[\u064b-\u065f\u0670]*){2,}", BILINMEYEN, s)
    return ham, clean_ar(s)


def clean_ar(s):
    s = s.replace(TATWEEL, "")
    # شيء: ي ile ء arasına giren ayırıcı boşluk (glif aralığı) kaldırılır
    s = re.sub("(ي[\u064b-\u065f]*) (?=[\u064b-\u065f]*ء)", r"\1", s)
    # sunum biçimleri varsa standarda; ﷺ (U+FDFA) gibi kısaltma ligatürleri NFKC ile açılmaz, olduğu gibi korunur
    s = "".join(p if KORUNAN.fullmatch(p) else unicodedata.normalize("NFC", unicodedata.normalize("NFKC", p))
                for p in re.split("(" + KORUNAN.pattern + ")", s) if p)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub("^[\u064b-\u065f\u0670 ]+", "", s)   # satır başına kaçan yetim hareke
    return s


FA_WORDS = {"از", "به", "در", "را", "كه", "كى", "که", "ز", "چه", "تا", "بر", "با", "اين", "آن", "مرا", "نه", "هر", "من", "او", "هم", "كم", "نايد", "شدم", "شود"}


def ar_lang(s):
    """Sezgisel: Fars harfi ya da >=2 Farsça işlev sözcüğü -> 'fa'."""
    if set(s) & PERSIAN:
        return "fa"
    toks = re.sub("[\u064b-\u065f\u0670]", "", s).split()
    return "fa" if sum(1 for t in toks if t in FA_WORDS and t not in ("من",)) >= 2 else "ar"


def tr_clean(lines):
    """Satırları birleştirir: satır sonu tireyi kaldırır, üst indis -> [^n]."""
    text = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if text.endswith("-") and ln[:1].islower():
            text = text[:-1] + ln
        else:
            text = (text + " " + ln) if text else ln
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", text)).strip()


def tr_line_text(chars, mark_notes):
    """Bir Türkçe satırın ham ve temiz metni; üst indis rakamlar [^n] olur."""
    ham = "".join(c["text"] for c in chars)
    out, k = [], 0
    while k < len(chars):
        c = chars[k]
        if c["size"] < SUP_MAX and c["text"].isdigit() and not INDEKS:
            j = k
            while j < len(chars) and chars[j]["size"] < SUP_MAX and chars[j]["text"].isdigit():
                j += 1
            rakam = "".join(x["text"] for x in chars[k:j])
            if out and out[-1][-1:].isdigit() and j < len(chars) and chars[j]["text"] == "/":
                out.append(rakam.translate(UST_INDIS))   # "[25¹/4]" bölüm işareti (2. cilt): dipnot çağrısı değil
            else:
                out.append("[^" + rakam + "]")
            k = j
        else:
            out.append(c["text"])
            k += 1
    return ham, "".join(out)


def aile(yazi):
    """Yazı tipi ailesi: italik/normal Garamond aynı paragrafta kalır."""
    return "nimbus" if "Nimbus" in yazi else ("bold" if "Bold" in yazi else "garamond")


LINE_TOL = 6.0   # aynı görsel satırdaki Arapça/Türkçe parçaların top farkı (satır aralığı >= 14)
KORUNAN = re.compile("[\ufdf0-\ufdff]")   # ﷺ ﷲ gibi Arapça kısaltma ligatürleri: NFKC genişletmez, olduğu gibi kalır


def _satirlara_ayir(items):
    """Parçaları top'a göre görsel satırlara kümeler; her satırı mantıksal okuma sırasına koyar.

    Yalnız Arapça (ya da [x/y] işaretli) satır: sağdan sola (beyit hemistişleri).
    Karışık satır (Türkçe + satır içi Arapça): parçalar soldan sağa (x0); bitişik Arapça/[x/y] parçaları
    kendi aralarında sağdan sola. Böylece Türkçe parça sırası ve satır sonu tire doğru kalır (G-026, Ö-1).
    """
    items = sorted(items, key=lambda it: it["top"])
    kumeler = []
    for it in items:
        if kumeler and it["top"] - kumeler[-1][0] <= LINE_TOL:
            kumeler[-1][1].append(it)
        else:
            kumeler.append([it["top"], [it]])
    satirlar = []
    for _, k in kumeler:
        ar_var = any(it["mod"] == "ar" for it in k)
        for it in k:
            it["satir_ar"] = ar_var
            it["yalniz_isaret"] = it["isaret"] and len(k) == 1 and not ar_var   # kendi satırında duran [x/y]
            if not ar_var:          # [x/y] Arapça satırın içindeyse bölüm işaretidir
                it["isaret"] = False
        benzer = lambda it: it["mod"] == "ar" or it["isaret"]
        if all(benzer(it) for it in k):
            sirali = sorted(k, key=lambda it: -it["x0"])
        else:
            k = sorted(k, key=lambda it: it["x0"])
            sirali, i = [], 0
            while i < len(k):
                if benzer(k[i]):
                    j = i
                    while j < len(k) and benzer(k[j]):
                        j += 1
                    sirali += sorted(k[i:j], key=lambda it: -it["x0"])
                    i = j
                else:
                    sirali.append(k[i])
                    i += 1
        satirlar.append(sirali)
    return satirlar


def _arapca_rakamlari_ayir(chars):
    """Arapça yazı tipiyle dizilmiş küçük (< 10 pt) rakamlar (2. cilt, G-036):
    * "[25¹/47]" bölüm işaretinin üst indisi ("/" ile devam ediyorsa): Türkçe üst indis yapılır, işaret bütün kalır;
    * Arapça satıra yapışan dipnot çağrısı ("كشفيًّا،523"): metinden çıkarılır, (rakam, top, x0) olarak döner.
    1. ciltte böyle karakter yoktur; çıktısı değişmez."""
    out, refler, i = [], [], 0
    küçük_rakam = lambda c: c["text"].isdigit() and is_ar(c) and c["size"] < 10
    while i < len(chars):
        c = chars[i]
        if küçük_rakam(c):
            j = i
            while j < len(chars) and küçük_rakam(chars[j]):
                j += 1
            grup = chars[i:j]
            while out and out[-1]["text"] == " " and is_ar(out[-1]) and out[-1]["size"] < 10:
                out.pop()      # rakamın önündeki küçük ayırıcı boşluk
            onceki_rakam = bool(out) and out[-1]["text"].isdigit()
            if j < len(chars) and chars[j]["text"] == "/" and onceki_rakam:
                for g in grup:
                    out.append({**g, "fontname": "AGaramondPro-Regular", "size": 6.7})
            else:
                refler.append(("".join(g["text"] for g in grup), grup[0]["top"], grup[0]["x0"]))
            i = j
        else:
            out.append(c)
            i += 1
    return out, refler


def _isaret_blok(it):
    return {"tur": "isaret", "dil": "tr", "ham": it["ham"], "metin": it["tem"].strip(), "top": it["top"],
            "x0": it["x0"], "x1": it["x1"], "boyut": it["boyut"], "yazi": it["yazi"]}


def page_blocks(pg):
    """Bir sayfa için blok listesi, okuma sırasında: (tur, dil, ham, metin, top, x0, boyut, yazi).

    Satır içi Arapçalı Türkçe satırlarda blok sırası: Türkçe | Arapça | Türkçe (G-026).
    Dipnot ayracının altındaki Arapça dipnot bloğunun içinde "{ar: ...}" olarak kalır, gövdeye sızmaz.
    """
    chars, dipnot_refler = _arapca_rakamlari_ayir([c for c in pg.chars if c["text"] != "\x00"])
    sep = None
    for ln in pg.lines + pg.rects:
        if abs(ln["bottom"] - ln["top"]) < 1.5 and 50 < ln["x1"] - ln["x0"] < 320 and ln["top"] > SEP_MIN_TOP:
            sep = ln["top"]
    items = []
    for mode, run in split_runs(chars):
        bases = [c for c in run if not (mode == "ar" and is_mark(c["text"]))]
        if not bases:
            continue
        top = sorted(c["top"] for c in bases)[len(bases) // 2]
        x0 = min(c["x0"] for c in bases)
        if mode == "ar":
            ham, tem = ar_logical(run)
            if not tem:
                continue
            items.append({"mod": "ar", "isaret": False, "dil": ar_lang(tem), "ham": ham, "tem": tem,
                          "top": top, "x0": x0, "x1": max(c["x1"] for c in bases),
                          "boyut": run[0]["size"], "yazi": "Scheherazade"})
        else:
            ham, tem = tr_line_text(run, None)
            if not tem.strip():
                continue
            big = max(c["size"] for c in run)
            fn = min(sorted(set(c["fontname"].split("+")[-1].split("#")[0] for c in run)), key=lambda f: (-sum(1 for c in run if c["fontname"].split("+")[-1].split("#")[0] == f), "Italic" in f))   # eşitlikte italik olmayan, sonra sıralı ilk (küme sırası süreçten sürece değişiyordu)
            items.append({"mod": "tr", "isaret": bool(re.fullmatch(r"\[[\d⁰¹²³⁴⁵⁶⁷⁸⁹]+/\d+\]", tem.strip())), "ham": ham, "tem": tem,
                          "top": top, "x0": x0, "x1": max(c["x1"] for c in run), "boyut": big, "yazi": fn})
    for rakam, rtop, rx in dipnot_refler:      # dipnot çağrısı, en yakın Arapça parçaya bağlanır
        ar_items = [it for it in items if it["mod"] == "ar" and abs(it["top"] - rtop) < 25]
        if ar_items:
            hedef = min(ar_items, key=lambda it: (0 if it["x0"] - 8 <= rx <= it["x1"] + 8 else 1, abs(it["top"] - rtop)))
            hedef.setdefault("dipnot_ref", []).append(rakam)
    satirlar = _satirlara_ayir(items)
    for si, sat in enumerate(satirlar):
        for it in sat:
            it["satir"] = si
    sirali = [it for sat in satirlar for it in sat]
    body_left = min([it["x0"] for it in sirali if it["mod"] == "tr" and it["top"] > HEADER_TOP and it["boyut"] >= BODY_MIN] or [68])

    out = []        # blok sözlükleri ya da açık paragraflar ({"p": ...})
    acik = None     # açık paragraf: {"p": True, "tur", "ogeler": [item...]}

    def ac(tur, it):
        nonlocal acik
        acik = {"p": True, "tur": tur, "ogeler": [it]}
        out.append(acik)

    for it in sirali:
        if it["top"] < HEADER_TOP and it["mod"] == "tr":
            if acik and acik["tur"] == "baslik_sayfa":
                acik["ogeler"].append(it)
            else:
                ac("baslik_sayfa", it)
        elif sep is not None and it["top"] >= sep:
            if it["mod"] == "ar":
                if not (acik and acik["tur"] == "dipnot"):
                    ac("dipnot", it)
                else:
                    acik["ogeler"].append(it)
            elif re.match(r"^\s*\d{1,4}[  ]", it["tem"]) or not (acik and acik["tur"] == "dipnot"):
                ac("dipnot", it)
            else:
                acik["ogeler"].append(it)
        elif it["mod"] == "ar":
            acik = None
            out.append({"tur": "arapca", "dil": it["dil"], "ham": it["ham"], "metin": it["tem"], "top": it["top"],
                        "x0": it["x0"], "x1": it["x1"], "boyut": it["boyut"], "yazi": it["yazi"],
                        **({"dipnot_ref": it["dipnot_ref"]} if it.get("dipnot_ref") else {})})
        elif it["isaret"]:
            acik = None
            out.append(_isaret_blok(it))
        else:
            son = acik["ogeler"][-1] if acik and acik["tur"] == "gövde" else None
            if son is None:
                yeni = True
            else:
                ayni = son["satir"] == it["satir"]
                yeni = ((it["x0"] > body_left + 5 and not ayni)
                        or aile(it["yazi"]) != aile(son["yazi"])
                        or (it["top"] - son["top"] > 20 and not ayni))
            # kendi satırında duran [x/y]: yeni paragraf başlıyorsa ya da Arapçalı satırı izliyorsa bölüm işaretidir
            if it["yalniz_isaret"] and (yeni or (son is not None and son["satir_ar"])):
                acik = None
                out.append(_isaret_blok(it))
            elif yeni:
                ac("gövde", it)
            else:
                acik["ogeler"].append(it)

    blocks = []
    for p in out:
        if not p.get("p"):
            blocks.append(p)
            continue
        ls = p["ogeler"]
        tur = p["tur"]
        if tur == "baslik_sayfa":
            ls = sorted(ls, key=lambda l: l["x0"])
        parcalar = []
        for l in ls:
            if l["mod"] == "ar":      # yalnız dipnotta: bitişik Arapça parçaları tek {ar: ...} olur
                if parcalar and parcalar[-1][0] == "ar":
                    parcalar[-1][1].append(l["tem"])
                else:
                    parcalar.append(("ar", [l["tem"]]))
            else:
                parcalar.append(("tr", l["tem"]))
        tem = tr_clean([("{ar: " + " ".join(v) + "}") if k == "ar" else v for k, v in parcalar])
        if tur == "gövde":
            f = ls[0]["yazi"]
            if re.match(r"^(Ya[’'‘]?ni|Tercüme|Meâl|Terceme)\b", tem) or "Nimbus" in f:
                tur = "terceme"
            elif "Bold" in f:
                tur = "baslik"
            else:
                tur = "serh"
        blocks.append({"tur": tur, "dil": "tr", "ham": "\n".join(l["ham"] for l in ls), "metin": tem,
                       "top": ls[0]["top"], "x0": ls[0]["x0"], "x1": 0,
                       "boyut": ls[0]["boyut"], "yazi": ls[0]["yazi"]})
    return blocks


def ocr_sayfa(pdf_yolu, n, dil="eng"):
    """Metin katmanı olmayan ama mürekkep taşıyan sayfa için Tesseract (G-018 yöntemi). Yoksa None."""
    import glob
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-f", str(n), "-l", str(n), "-png", pdf_yolu, d + "/s"], check=True)
        png = glob.glob(d + "/s*.png")[0]
        from PIL import Image
        im = Image.open(png).convert("L")
        koyu = sum(1 for v in im.resize((im.width // 4, im.height // 4)).tobytes() if v < 160)
        if koyu < 200:
            return None
        r = subprocess.run(["tesseract", png, "-", "-l", dil, "--psm", "6"], capture_output=True, text=True)
        return r.stdout.strip() or None


def basili_no(blocks):
    for b in blocks:
        if b["tur"] == "baslik_sayfa":
            m = re.search(r"(\d+)\s*$", b["metin"]) or re.match(r"^\s*(\d+)", b["metin"])
            if m:
                return int(m.group(1))
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("cikti")
    ap.add_argument("--ilk", type=int, default=1)
    ap.add_argument("--son", type=int, default=0)
    ap.add_argument("--sep-min", type=float, default=400, help="dipnot ayracı için en düşük top (2. cilt: 100)")
    ap.add_argument("--indeks-ilk", type=int, default=0, help="bu PDF sayfasından itibaren üst indis rakamlar düz rakam kalır (dizinler)")
    a = ap.parse_args(argv)
    import os
    hook_cid()
    global SEP_MIN_TOP, INDEKS
    SEP_MIN_TOP = a.sep_min
    import pdfplumber
    os.makedirs(a.cikti, exist_ok=True)
    nham = ntem = 0
    with pdfplumber.open(a.pdf) as pdf, open(os.path.join(a.cikti, "ham.jsonl"), "w", encoding="utf-8") as fh, \
            open(os.path.join(a.cikti, "temiz.jsonl"), "w", encoding="utf-8") as ft:
        son = a.son or len(pdf.pages)
        for n in range(a.ilk, son + 1):
            INDEKS = bool(a.indeks_ilk) and n >= a.indeks_ilk
            bl = page_blocks(pdf.pages[n - 1])
            if not bl and not pdf.pages[n - 1].chars:
                t = ocr_sayfa(a.pdf, n)
                if t:
                    bl = [{"tur": "ocr_sayfa", "dil": "tr", "ham": t, "metin": t, "top": 0, "x0": 0, "boyut": 0, "yazi": "tesseract-eng"}]
            bn = basili_no(bl)
            for i, b in enumerate(bl, 1):
                base = {"sayfa": n, "basili_sayfa": bn, "sira": i, "tur": b["tur"], "dil": b["dil"]}
                if b.get("dipnot_ref"):
                    base["dipnot_ref"] = b["dipnot_ref"]   # yalnız Arapça blokta, varsa (G-036)
                fh.write(json.dumps({**base, "ham": b["ham"], "yazi": b["yazi"], "boyut": round(b["boyut"], 1),
                                     "top": round(b["top"], 1), "x0": round(b["x0"], 1)}, ensure_ascii=False) + "\n")
                ft.write(json.dumps({**base, "metin": b["metin"]}, ensure_ascii=False) + "\n")
                nham += 1
    print(f"{a.ilk}-{son}: {nham} blok", file=sys.stderr)
    yeni = sorted(k for k in GORULEN_CID if k[1] not in BILINEN_ALEF_CID)
    if yeni:
        print("UYARI: bilinmeyen hemzeli elif CID'leri:", yeni, file=sys.stderr)
    json.dump({f"{k[0]}#{k[1]}": v for k, v in GORULEN_CID.items()}, open(os.path.join(a.cikti, "cid_sayim.json"), "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
