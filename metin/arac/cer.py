#!/usr/bin/env python3
"""Karakter hata oranı (CER): cer.py referans.txt ocr.txt
Başlık (<!--) satırları atlanır. Katmanlar: ham (yalnız boşluk sadeleşir),
katlı (hareke/tatvil kalkar; Fars harfleri ve doğu rakamları Arapçaya katlanır)."""
import sys, re
FOLD = str.maketrans({'ک':'ك','ی':'ي','ى':'ي','ھ':'ه','ہ':'ه','ۃ':'ة','۰':'٠','۱':'١','۲':'٢','۳':'٣','۴':'٤','۵':'٥','۶':'٦','۷':'٧','۸':'٨','۹':'٩',
  'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ة':'ه'})
def oku(p):
    return "\n".join(l for l in open(p, encoding='utf-8').read().splitlines() if not l.startswith('<!--'))
def sade(t, kat):
    if kat:
        t = re.sub('[ً-ٰٟـ]', '', t).translate(FOLD)
    return re.sub(r'\s+', ' ', t).strip()
def lev(a, b):
    p = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        c = [i]
        for j, y in enumerate(b, 1):
            c.append(min(p[j]+1, c[-1]+1, p[j-1]+(x != y)))
        p = c
    return p[-1]
def cer(ref, ocr, kat):
    r, o = sade(ref, kat), sade(ocr, kat)
    return lev(r, o), len(r), lev(r, o)/len(r)
if __name__ == '__main__':
    ref, ocr = oku(sys.argv[1]), oku(sys.argv[2])
    for ad, k in (('ham', False), ('katlı', True)):
        d, n, c = cer(ref, ocr, k)
        print(f"{ad}: mesafe={d} ref_karakter={n} CER={c:.3f}")
