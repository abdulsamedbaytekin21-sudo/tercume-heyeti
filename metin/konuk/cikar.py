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

AR_FONTS = ("Scheherazade", "Suleymaniye")
HAMZA_ALEF = "أإآٱ"
FFFD = "�"
TATWEEL = "ـ"
PERSIAN = set("پچژگکیھہۀ")
SUP_MAX = 8.0          # üst indis boyu (altı = dipnot çağrısı)
BODY_MIN = 10.4        # gövde Türkçe boyu (Garamond 11.5, Nimbus 10.6)
HEADER_TOP = 70


# Scheherazade alt kümesinde أَ ve أُ tek glif (CID) olup metin katmanında yalnız U+0623 görünür.
# CID, pdfminer kancasıyla yazı tipi adına "#<cid>" olarak eklenir (hook_cid).
# Eşleme sayfa görüntüsünde doğrulandı: s. 84'te 1110 = أَ, 1111 = أُ, 913 = harekesiz أ.
CID_HAMZA = {1110: "\u064e", 1111: "\u064f"}
BILINEN_ALEF_CID = {913, 1110, 1111, 914, 912}
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
        elif t in HAMZA_ALEF:
            cid = cid_of(c)
            if cid is not None:
                GORULEN_CID[(t, cid)] = GORULEN_CID.get((t, cid), 0) + 1
                t += CID_HAMZA.get(cid, "")
        out.append(t)
    s = "".join(reversed(out))
    return ham, clean_ar(s)


def clean_ar(s):
    s = s.replace(TATWEEL, "")
    # شيء: ي ile ء arasına giren ayırıcı boşluk (glif aralığı) kaldırılır
    s = re.sub("(ي[\u064b-\u065f]*) (?=[\u064b-\u065f]*ء)", r"\1", s)
    s = unicodedata.normalize("NFKC", s)   # sunum biçimleri varsa standarda
    s = unicodedata.normalize("NFC", s)
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
        if c["size"] < SUP_MAX and c["text"].isdigit():
            j = k
            while j < len(chars) and chars[j]["size"] < SUP_MAX and chars[j]["text"].isdigit():
                j += 1
            out.append("[^" + "".join(x["text"] for x in chars[k:j]) + "]")
            k = j
        else:
            out.append(c["text"])
            k += 1
    return ham, "".join(out)


def aile(yazi):
    """Yazı tipi ailesi: italik/normal Garamond aynı paragrafta kalır."""
    return "nimbus" if "Nimbus" in yazi else ("bold" if "Bold" in yazi else "garamond")


def page_blocks(pg):
    """Bir sayfa için blok listesi: (tur, dil, ham, temiz, top, x0, boyut, yazi)."""
    chars = [c for c in pg.chars if c["text"] != "\x00"]
    sep = None
    for ln in pg.lines + pg.rects:
        if abs(ln["bottom"] - ln["top"]) < 1.5 and 50 < ln["x1"] - ln["x0"] < 320 and ln["top"] > 400:
            sep = ln["top"]
    blocks = []
    tr_lines = []   # (top, x0, size, font, ham, temiz)
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
            blocks.append({"tur": "arapca", "dil": ar_lang(tem), "ham": ham, "metin": tem,
                           "top": top, "x0": x0, "x1": max(c["x1"] for c in bases),
                           "boyut": run[0]["size"], "yazi": "Scheherazade"})
        else:
            ham, tem = tr_line_text(run, None)
            if not tem.strip():
                continue
            big = max(c["size"] for c in run)
            fn = max(set(c["fontname"].split("+")[-1].split("#")[0] for c in run), key=lambda f: sum(1 for c in run if c["fontname"].split("+")[-1].split("#")[0] == f))
            tr_lines.append({"top": top, "x0": x0, "boyut": big, "yazi": fn, "ham": ham, "tem": tem})
    # Türkçe satırları paragraflara topla
    tr_lines.sort(key=lambda l: l["top"])
    ar_tops = [b["top"] for b in blocks if b["tur"] == "arapca"]
    body_left = min([l["x0"] for l in tr_lines if l["top"] > HEADER_TOP and l["boyut"] >= BODY_MIN] or [68])
    paras = []
    for l in tr_lines:
        if l["top"] < HEADER_TOP:
            if paras and paras[-1]["tur"] == "baslik_sayfa":
                paras[-1]["satirlar"].append(l)
            else:
                paras.append({"tur": "baslik_sayfa", "satirlar": [l]})
        elif sep is not None and l["top"] >= sep:
            if re.match(r"^\s*\d{1,4}[  ]", l["tem"]) or not paras or paras[-1]["tur"] != "dipnot":
                paras.append({"tur": "dipnot", "satirlar": [l]})
            else:
                paras[-1]["satirlar"].append(l)
        else:
            yeni = (not paras or paras[-1]["tur"] in ("baslik_sayfa", "dipnot")
                    or l["x0"] > body_left + 5
                    or aile(l["yazi"]) != aile(paras[-1]["satirlar"][-1]["yazi"])
                    or l["top"] - paras[-1]["satirlar"][-1]["top"] > 20
                    or any(paras[-1]["satirlar"][-1]["top"] - 5 <= a <= l["top"] - 5 for a in ar_tops))
            if yeni:
                paras.append({"tur": "gövde", "satirlar": [l]})
            else:
                paras[-1]["satirlar"].append(l)
    for p in paras:
        ls = p["satirlar"]
        if p["tur"] == "baslik_sayfa":
            ls.sort(key=lambda l: l["x0"])
        tem = tr_clean([l["tem"] for l in ls])
        tur = p["tur"]
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
    # Okuma sırası: yukarıdan aşağı; aynı satırdaki Arapça parçalar sağdan sola
    def key(b):
        return (round(b["top"] / 6), -b["x0"] if b["tur"] == "arapca" else b["x0"])
    ar_idx = [b for b in blocks if b["tur"] == "arapca"]
    # Arapça blokları kendi aralarında satır kümesine göre sırala
    for b in blocks:
        if b["dil"] == "tr" and re.fullmatch(r"\[\d+/\d+\]", b["metin"]):
            b["tur"] = "isaret"   # Arapça satır içine giren "[6/45]" Fusûs bölüm/sayfa işareti
    satirda = ("arapca", "isaret")
    blocks.sort(key=lambda b: (round(b["top"] / 6) * 6 if b["tur"] in satirda else b["top"], -b["x0"] if b["tur"] in satirda else 0))
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
    a = ap.parse_args(argv)
    import os
    hook_cid()
    import pdfplumber
    os.makedirs(a.cikti, exist_ok=True)
    nham = ntem = 0
    with pdfplumber.open(a.pdf) as pdf, open(os.path.join(a.cikti, "ham.jsonl"), "w", encoding="utf-8") as fh, \
            open(os.path.join(a.cikti, "temiz.jsonl"), "w", encoding="utf-8") as ft:
        son = a.son or len(pdf.pages)
        for n in range(a.ilk, son + 1):
            bl = page_blocks(pdf.pages[n - 1])
            if not bl and not pdf.pages[n - 1].chars:
                t = ocr_sayfa(a.pdf, n)
                if t:
                    bl = [{"tur": "ocr_sayfa", "dil": "tr", "ham": t, "metin": t, "top": 0, "x0": 0, "boyut": 0, "yazi": "tesseract-eng"}]
            bn = basili_no(bl)
            for i, b in enumerate(bl, 1):
                base = {"sayfa": n, "basili_sayfa": bn, "sira": i, "tur": b["tur"], "dil": b["dil"]}
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
