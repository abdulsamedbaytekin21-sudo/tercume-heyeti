#!/usr/bin/env python3
"""Musahhih: işaretli tashihli metni katmanlara ayırır ve Arapçayı normalleştirir.

İlke: girdi (tashihli metin) asla değiştirilmez; normalleştirme ayrı çıktıdır.
İşaretleme sözdizimi için metin/AKIS.md'ye bakın.
"""
import re
import sys
import unicodedata

PAGE_RE = re.compile(r"^\[s\. (\d+)\]\s*$")
HEAD_RE = re.compile(r"^(#{1,3}) (fass|bâb|fasıl|mukaddime|başlık): (.+)$")
FN_DEF_RE = re.compile(r"^\[\^(\w+)\]: (.+)$")
FN_REF_RE = re.compile(r"\[\^\w+\]")
ADD_RE = re.compile(r"\[(?!s\. \d|\^)([^\[\]]+)\]")
UNREADABLE = "⟨?⟩"

TASHKEEL = re.compile("[ً-ْٰٓ-ٕۖ-ۭ]")
TATWEEL = "ـ"
ALEF_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"})


def normalize_ar(text, *, ta_marbuta=False, ya=True):
    """Harekeyi, tatvili ve elif/yâ varyantlarını sadeleştirir.

    ⟨?⟩ işaretleri ve boşluk düzeni korunur. ta_marbuta=True ise ة -> ه
    (varsayılan kapalı; bilgi kaybettirir).
    """
    t = unicodedata.normalize("NFC", text)
    t = TASHKEEL.sub("", t).replace(TATWEEL, "")
    t = t.translate(ALEF_MAP)
    if ya:
        t = t.replace("ى", "ي")
    if ta_marbuta:
        t = t.replace("ة", "ه")
    return t


def parse(raw):
    """İşaretli metni katmanlara ayırır.

    Dönüş: {"govde": [{sayfa, satir}], "basliklar": [...], "dipnotlar": [...],
            "ilaveler": [...], "okunamayan": [...]}
    Dipnot ve mütercim ilavesi gövde satırından çıkarılır (ana metne karışmaz).
    """
    out = {"govde": [], "basliklar": [], "dipnotlar": [], "ilaveler": [], "okunamayan": []}
    sayfa = None
    for no, line in enumerate(raw.splitlines(), 1):
        if not line.strip() or line.startswith("<!--"):
            continue
        m = PAGE_RE.match(line)
        if m:
            sayfa = int(m.group(1))
            continue
        m = HEAD_RE.match(line)
        if m:
            out["basliklar"].append({"sayfa": sayfa, "tur": m.group(2), "seviye": len(m.group(1)), "metin": m.group(3)})
            continue
        m = FN_DEF_RE.match(line)
        if m:
            out["dipnotlar"].append({"sayfa": sayfa, "no": m.group(1), "metin": m.group(2)})
            continue
        for a in ADD_RE.finditer(line):
            out["ilaveler"].append({"sayfa": sayfa, "metin": a.group(1)})
        if UNREADABLE in line:
            out["okunamayan"].append({"sayfa": sayfa, "satir": no})
        body = FN_REF_RE.sub("", line)
        body = ADD_RE.sub("", body)
        body = re.sub(r"[ \t]{2,}", " ", body).strip()
        out["govde"].append({"sayfa": sayfa, "satir": body})
    return out


def normalize_document(raw, **kw):
    """Gövde satırlarını normalleştirir; sayfa numarası korunur."""
    p = parse(raw)
    return [{"sayfa": g["sayfa"], "satir": normalize_ar(g["satir"], **kw)} for g in p["govde"]]


def sample_errors(pairs):
    """Tashih oranı: pairs = [(ham, tashihli), ...] örneklenen satırlar.
    Dönüş: (örneklenen, hatalı, oran)."""
    n = len(pairs)
    bad = sum(1 for a, b in pairs if a != b)
    return n, bad, (bad / n if n else 0.0)


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read()
    for g in normalize_document(src):
        print(f"[s. {g['sayfa']}] {g['satir']}")
